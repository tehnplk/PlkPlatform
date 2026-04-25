from __future__ import annotations

import traceback
from datetime import date, datetime
from typing import Any

from PyQt6.QtCore import QDate, QEvent, QItemSelectionModel, QLocale, Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QStandardItem
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QVBoxLayout,
)

from BuddyCareExcel_logic import (
    create_db_connection,
    load_doctor_options,
    load_ovstist_options,
)
from His_factory import make_his
from QuickVisit_ui import RESULT_COLUMNS, QuickVisitUI
from Setting_helper import read_setting, save_settings

SEARCH_DEBOUNCE_MS = 300
MIN_SEARCH_LEN = 2
MAX_RESULTS = 50


class QuickVisitDialog(QDialog):
    """Dialog เปิด visit — เลือกวันที่ + dx + doctor + ประเภทการมา"""

    def __init__(
        self,
        dx_code: str,
        doctor_options: list[tuple[str, str]],
        ovstist_options: list[tuple[str, str]],
        default_doctor_code: str,
        default_ovstist: str,
        default_visit_date: date | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("เปิด Visit")
        self.setModal(True)
        self.resize(460, 220)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        en_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.date_edit.setLocale(en_locale)
        cal = self.date_edit.calendarWidget()
        if cal is not None:
            cal.setLocale(en_locale)
        d = default_visit_date or date.today()
        self.date_edit.setDate(QDate(d.year, d.month, d.day))

        self.dx_input = QLineEdit(dx_code)
        self.dx_input.setPlaceholderText("เช่น Z718")

        self.doctor_combo = QComboBox()
        for code, name in doctor_options:
            label = f"{code} - {name}" if name else code
            self.doctor_combo.addItem(label, code)
        if default_doctor_code:
            idx = self.doctor_combo.findData(default_doctor_code)
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)

        self.ovstist_combo = QComboBox()
        for code, name in ovstist_options:
            label = f"{code} - {name}" if name else code
            self.ovstist_combo.addItem(label, code)
        if default_ovstist:
            idx = self.ovstist_combo.findData(default_ovstist)
            if idx >= 0:
                self.ovstist_combo.setCurrentIndex(idx)

        form = QFormLayout()
        form.addRow("วันที่ visit", self.date_edit)
        form.addRow("รหัสวินิจฉัย", self.dx_input)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("ประเภทการมา", self.ovstist_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[date, str, str, str]:
        qd = self.date_edit.date()
        visit_date = date(qd.year(), qd.month(), qd.day())
        dx_code = self.dx_input.text().strip().upper()
        doctor_code = str(self.doctor_combo.currentData() or "").strip()
        ovstist_code = str(self.ovstist_combo.currentData() or "").strip()
        return visit_date, dx_code, doctor_code, ovstist_code


def _search_patients(term: str) -> list[dict[str, Any]]:
    """ค้นหา patient แบบ unified — ตรวจทั้ง cid / hn / fname / lname พร้อมกัน"""
    term = (term or "").strip()
    if len(term) < MIN_SEARCH_LEN:
        return []

    sql_base = (
        "SELECT t.hn, t.cid, "
        "       CONCAT(COALESCE(t.pname,''), COALESCE(t.fname,''), ' ', COALESCE(t.lname,'')) AS fullname, "
        "       t.sex, t.birthday, "
        "       CASE WHEN t.birthday IS NULL THEN '' ELSE CONCAT( "
        "            TIMESTAMPDIFF(YEAR, t.birthday, CURRENT_DATE), ' ปี ', "
        "            TIMESTAMPDIFF(MONTH, t.birthday, CURRENT_DATE) MOD 12, ' เดือน ', "
        "            DATEDIFF(CURRENT_DATE, DATE_ADD(t.birthday, INTERVAL TIMESTAMPDIFF(MONTH, t.birthday, CURRENT_DATE) MONTH)), ' วัน' "
        "       ) END AS age, "
        "       CONCAT('(', COALESCE(t.pttype,''), ') ', COALESCE(p.name,'')) AS inscl, "
        "       COALESCE(hrt.house_regist_type_name, '') AS type_area, "
        "       CASE WHEN t.mobile_phone_number IS NULL OR TRIM(t.mobile_phone_number) = '' "
        "            THEN t.hometel ELSE t.mobile_phone_number END AS mobile "
        "FROM patient t "
        "LEFT JOIN pttype p ON p.pttype = t.pttype "
        "LEFT JOIN house_regist_type hrt ON hrt.house_regist_type_id = t.type_area "
    )

    prefix = f"{term}%"
    contains = f"%{term}%"

    parts = term.split()
    if len(parts) >= 2:
        # กรอก "ชื่อ นามสกุล" — match ทั้งคู่
        fname_like = f"%{parts[0]}%"
        lname_like = f"%{' '.join(parts[1:])}%"
        sql = sql_base + (
            "WHERE t.cid LIKE %s "
            "   OR t.hn LIKE %s "
            "   OR (TRIM(t.fname) LIKE %s AND TRIM(t.lname) LIKE %s) "
            "   OR TRIM(t.fname) LIKE %s "
            "   OR TRIM(t.lname) LIKE %s "
            "ORDER BY t.fname, t.lname "
            f"LIMIT {MAX_RESULTS}"
        )
        params: tuple = (prefix, prefix, fname_like, lname_like, contains, contains)
    else:
        sql = sql_base + (
            "WHERE t.cid LIKE %s "
            "   OR t.hn LIKE %s "
            "   OR TRIM(t.fname) LIKE %s "
            "   OR TRIM(t.lname) LIKE %s "
            "ORDER BY t.fname, t.lname "
            f"LIMIT {MAX_RESULTS}"
        )
        params = (prefix, prefix, contains, contains)

    conn = create_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall() or [])
    finally:
        conn.close()


def _get_visits_by_cid_on_date(cid: str, visit_date: date) -> list[dict[str, Any]]:
    """คืน list visits ของ CID ในวันที่ระบุ (vn, vsttime, ovstist)"""
    cid = (cid or "").strip()
    if not cid:
        return []
    sql = (
        "SELECT o.vn, o.vsttime, o.ovstist "
        "FROM ovst o "
        "INNER JOIN patient p ON p.hn = o.hn "
        "WHERE TRIM(p.cid) = %s AND o.vstdate = %s "
        "ORDER BY o.vsttime"
    )
    conn = create_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (cid, visit_date.isoformat()))
            return list(cursor.fetchall() or [])
    finally:
        conn.close()


def _format_value(column_key: str, value: Any) -> str:
    if value is None:
        return ""
    if column_key == "birthday" and isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value)


class QuickVisitWindow(QuickVisitUI):
    """หน้าต่าง Quick Visit — ค้นคนไข้ live แล้วเปิด visit ได้ทันที"""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = []

        # debounce timer
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._do_search)

        self.search_input.textChanged.connect(self._on_text_changed)
        self.open_visit_button.clicked.connect(self.on_open_visit_clicked)
        self.result_table.selectionModel().selectionChanged.connect(
            self._update_open_button_state
        )
        self.result_table.doubleClicked.connect(lambda _: self.on_open_visit_clicked())

        # ใช้ arrow keys / Enter ที่ช่องค้นหาเพื่อเลือก row / เปิด visit ได้ทันที
        self.search_input.installEventFilter(self)

    # ---------------------------------------------------------------- search
    def _on_text_changed(self, text: str) -> None:
        term = text.strip()
        if len(term) < MIN_SEARCH_LEN:
            self._search_timer.stop()
            self.rows = []
            self._render_rows(self.rows)
            self.status_label.setText("")
            return
        self._search_timer.start()

    def _do_search(self) -> None:
        self._search_timer.stop()
        term = self.search_input.text().strip()
        if len(term) < MIN_SEARCH_LEN:
            return

        self.status_label.setText("กำลังค้นหา...")
        QApplication.processEvents()

        try:
            self.rows = _search_patients(term)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.status_label.setText("")
            QMessageBox.critical(self, "ค้นหาไม่สำเร็จ", str(exc))
            return

        self._render_rows(self.rows)
        if len(self.rows) >= MAX_RESULTS:
            self.status_label.setText(f"พบ {len(self.rows)} รายการ (แสดงเฉพาะ {MAX_RESULTS} รายการแรก)")
        else:
            self.status_label.setText(f"พบ {len(self.rows)} รายการ")

    def _render_rows(self, rows: list[dict[str, Any]]) -> None:
        self.result_model.setRowCount(0)
        for row in rows:
            items = []
            for _, key in RESULT_COLUMNS:
                item = QStandardItem(_format_value(key, row.get(key)))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                items.append(item)
            self.result_model.appendRow(items)
        self.result_table.resizeColumnsToContents()
        if rows:
            self._select_row(0)
        self._update_open_button_state()

    def _select_row(self, row: int) -> None:
        if not (0 <= row < self.result_model.rowCount()):
            return
        index = self.result_model.index(row, 0)
        selection = self.result_table.selectionModel()
        selection.setCurrentIndex(
            index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        self.result_table.scrollTo(index)

    def _move_selection(self, delta: int) -> None:
        total = self.result_model.rowCount()
        if total == 0:
            return
        current = self._selected_row_index()
        if current < 0:
            target = 0 if delta > 0 else total - 1
        else:
            target = max(0, min(total - 1, current + delta))
        self._select_row(target)

    # ---------------------------------------------------------------- keyboard
    def eventFilter(self, obj, event) -> bool:
        if obj is self.search_input and event.type() == QEvent.Type.KeyPress:
            assert isinstance(event, QKeyEvent)
            key = event.key()
            if key == Qt.Key.Key_Down:
                self._move_selection(+1)
                return True
            if key == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
            if key == Qt.Key.Key_PageDown:
                self._move_selection(+10)
                return True
            if key == Qt.Key.Key_PageUp:
                self._move_selection(-10)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # ถ้ามี row ที่เลือกอยู่ → เปิด visit; ถ้ายังไม่มีผลลัพธ์ → ยิงค้นหา
                if self._selected_row_index() >= 0:
                    self.on_open_visit_clicked()
                else:
                    self._do_search()
                return True
        return super().eventFilter(obj, event)

    def _selected_row_index(self) -> int:
        selection = self.result_table.selectionModel()
        if selection is None:
            return -1
        indexes = selection.selectedRows()
        if not indexes:
            return -1
        return indexes[0].row()

    def _selected_row_indices(self) -> list[int]:
        selection = self.result_table.selectionModel()
        if selection is None:
            return []
        return sorted({idx.row() for idx in selection.selectedRows()})

    def _update_open_button_state(self, *_args) -> None:
        rows = self._selected_row_indices()
        ok = bool(rows) and all(
            0 <= r < len(self.rows) and bool(self.rows[r].get("cid")) for r in rows
        )
        if ok and len(rows) > 1:
            self.open_visit_button.setText(f"เปิด Visit ({len(rows)})")
        else:
            self.open_visit_button.setText("เปิด Visit")
        self.open_visit_button.setEnabled(ok)

    # ---------------------------------------------------------------- open visit
    def on_open_visit_clicked(self) -> None:
        row_indices = self._selected_row_indices()
        if not row_indices:
            QMessageBox.information(self, "เลือกคนไข้", "กรุณาเลือกคนไข้ก่อน")
            return

        patients: list[dict[str, Any]] = []
        missing_cid: list[str] = []
        for r in row_indices:
            if not (0 <= r < len(self.rows)):
                continue
            p = self.rows[r]
            cid = str(p.get("cid") or "").strip()
            if not cid:
                missing_cid.append(str(p.get("hn") or p.get("fullname") or "-"))
                continue
            patients.append(p)

        if missing_cid:
            QMessageBox.warning(
                self,
                "ไม่มี CID",
                "คนไข้ต่อไปนี้ไม่มี CID จะถูกข้าม:\n  • " + "\n  • ".join(missing_cid),
            )
        if not patients:
            return

        try:
            conn = create_db_connection()
            try:
                with conn.cursor() as cursor:
                    doctor_options = load_doctor_options(cursor)
                    ovstist_options = load_ovstist_options(cursor)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            QMessageBox.critical(self, "โหลดข้อมูลไม่สำเร็จ", str(exc))
            return

        if not doctor_options or not ovstist_options:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่พร้อม",
                "ไม่พบข้อมูลตาราง doctor หรือ ovstist",
            )
            return

        default_dx = read_setting("LAST_DX_CODE", "Z718").strip() or "Z718"
        default_doctor = read_setting("LAST_DOCTOR_CODE", "0010").strip() or "0010"
        default_ovstist = read_setting("LAST_OVSTIST", "05").strip() or "05"

        dialog = QuickVisitDialog(
            default_dx,
            doctor_options,
            ovstist_options,
            default_doctor,
            default_ovstist,
            date.today(),
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        visit_date, dx_code, doctor_code, ovstist_code = dialog.values()
        if not dx_code or not doctor_code or not ovstist_code:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณาระบุ dx / doctor / ovstist ให้ครบ")
            return

        # ตรวจสอบ visit ซ้ำในวันที่เลือก (ทุกคนที่เลือก)
        duplicates: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
        for p in patients:
            cid = str(p.get("cid") or "").strip()
            try:
                existing = _get_visits_by_cid_on_date(cid, visit_date)
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                QMessageBox.critical(self, "ตรวจสอบ visit ไม่สำเร็จ", str(exc))
                return
            if existing:
                duplicates.append((p, existing))

        if duplicates:
            blocks: list[str] = []
            for p, existing in duplicates:
                lines = []
                for v in existing:
                    vsttime = v.get("vsttime")
                    time_str = ""
                    if isinstance(vsttime, (date, datetime)):
                        time_str = vsttime.strftime("%H:%M:%S")
                    elif vsttime is not None:
                        time_str = str(vsttime)
                    lines.append(
                        f"    • VN {v.get('vn')} เวลา {time_str} (ovstist {v.get('ovstist') or '-'})"
                    )
                blocks.append(
                    f"CID {p.get('cid')} ({p.get('fullname') or '-'}):\n" + "\n".join(lines)
                )
            joined = "\n\n".join(blocks)
            reply = QMessageBox.question(
                self,
                f"มี visit วันที่ {visit_date.isoformat()} แล้ว",
                (
                    f"พบ visit วันที่ {visit_date.isoformat()} อยู่แล้ว:\n\n{joined}\n\n"
                    "ยืนยันจะเปิด visit เพิ่มสำหรับทุกคนที่เลือกหรือไม่?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        main_pdx = dx_code[:3] if len(dx_code) >= 3 else dx_code

        try:
            his = make_his()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            QMessageBox.critical(self, "เชื่อมต่อ HIS ไม่สำเร็จ", str(exc))
            return

        if not his.his_is_connected():
            QMessageBox.critical(
                self, "เชื่อมต่อ HIS ไม่สำเร็จ", "ไม่สามารถเชื่อมต่อฐานข้อมูล HIS ได้"
            )
            return

        success: list[tuple[str, str]] = []
        failed: list[tuple[str, str]] = []
        cancelled = False

        progress = QProgressDialog(
            "กำลังเปิด visit...", "ยกเลิก", 0, len(patients), self
        )
        progress.setWindowTitle("เปิด Visit")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        progress.setValue(0)

        for i, p in enumerate(patients):
            if progress.wasCanceled():
                cancelled = True
                break
            cid = str(p.get("cid") or "").strip()
            name = str(p.get("fullname") or "").strip()
            progress.setLabelText(f"({i + 1}/{len(patients)}) CID {cid} {name}")
            QApplication.processEvents()

            payload = {
                "cid": cid,
                "visit_date": visit_date.isoformat(),
                "dx_code": dx_code,
                "main_pdx": main_pdx,
                "doctor": doctor_code,
                "ovstist": ovstist_code,
            }
            try:
                vn = his.openVisitHosxp(payload)
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                failed.append((cid, str(exc)))
            else:
                if vn:
                    success.append((cid, str(vn)))
                else:
                    failed.append((cid, "ไม่สามารถเปิด visit ได้"))

            progress.setValue(i + 1)
            QApplication.processEvents()

        progress.close()

        if success:
            save_settings({
                "LAST_DX_CODE": dx_code,
                "LAST_DOCTOR_CODE": doctor_code,
                "LAST_OVSTIST": ovstist_code,
            })

        ok_lines = "\n".join(f"  • CID {c} → VN {v}" for c, v in success) or "  (ไม่มี)"
        fail_lines = "\n".join(f"  • CID {c} → {msg}" for c, msg in failed)
        header = f"สำเร็จ {len(success)} / ทั้งหมด {len(patients)}"
        if cancelled:
            header += " (ยกเลิกระหว่างทาง)"
        body = f"{header}\n\nสำเร็จ:\n{ok_lines}"
        if fail_lines:
            body += f"\n\nล้มเหลว:\n{fail_lines}"

        if failed and not success:
            QMessageBox.critical(self, "เปิด Visit ไม่สำเร็จ", body)
        elif failed or cancelled:
            QMessageBox.warning(self, "เปิด Visit สำเร็จบางส่วน", body)
        else:
            QMessageBox.information(self, "เปิด Visit สำเร็จ", body)
