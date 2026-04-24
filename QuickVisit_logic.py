from __future__ import annotations

import traceback
from datetime import date, datetime
from typing import Any

from PyQt6.QtCore import QEvent, QItemSelectionModel, Qt, QTimer
from PyQt6.QtGui import QKeyEvent, QStandardItem
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from BuddyCareExcel_logic import (
    DxDoctorDialog,
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


def _search_patients(term: str) -> list[dict[str, Any]]:
    """ค้นหา patient แบบ unified — ตรวจทั้ง cid / hn / fname / lname พร้อมกัน"""
    term = (term or "").strip()
    if len(term) < MIN_SEARCH_LEN:
        return []

    sql_base = (
        "SELECT t.hn, t.cid, "
        "       CONCAT(COALESCE(t.pname,''), COALESCE(t.fname,''), ' ', COALESCE(t.lname,'')) AS fullname, "
        "       t.sex, t.birthday, "
        "       CONCAT('(', COALESCE(t.pttype,''), ') ', COALESCE(p.name,'')) AS inscl, "
        "       CASE WHEN t.mobile_phone_number IS NULL OR TRIM(t.mobile_phone_number) = '' "
        "            THEN t.hometel ELSE t.mobile_phone_number END AS mobile "
        "FROM patient t "
        "LEFT JOIN pttype p ON p.pttype = t.pttype "
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


def _get_today_visits_by_cid(cid: str) -> list[dict[str, Any]]:
    """คืน list visits วันนี้ของ CID นี้ (vn, vsttime, ovstist)"""
    cid = (cid or "").strip()
    if not cid:
        return []
    sql = (
        "SELECT o.vn, o.vsttime, o.ovstist "
        "FROM ovst o "
        "INNER JOIN patient p ON p.hn = o.hn "
        "WHERE TRIM(p.cid) = %s AND o.vstdate = CURRENT_DATE "
        "ORDER BY o.vsttime"
    )
    conn = create_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (cid,))
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

    def _update_open_button_state(self, *_args) -> None:
        row = self._selected_row_index()
        ok = 0 <= row < len(self.rows) and bool(self.rows[row].get("cid"))
        self.open_visit_button.setEnabled(ok)

    # ---------------------------------------------------------------- open visit
    def on_open_visit_clicked(self) -> None:
        row_idx = self._selected_row_index()
        if not (0 <= row_idx < len(self.rows)):
            QMessageBox.information(self, "เลือกคนไข้", "กรุณาเลือกคนไข้ก่อน")
            return

        patient = self.rows[row_idx]
        cid = str(patient.get("cid") or "").strip()
        if not cid:
            QMessageBox.warning(self, "ไม่มี CID", "คนไข้รายนี้ไม่มี CID ไม่สามารถเปิด visit ได้")
            return

        # ตรวจสอบ visit ซ้ำในวันเดียวกัน
        try:
            existing_visits = _get_today_visits_by_cid(cid)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            QMessageBox.critical(self, "ตรวจสอบ visit ไม่สำเร็จ", str(exc))
            return

        if existing_visits:
            lines = []
            for v in existing_visits:
                vsttime = v.get("vsttime")
                time_str = ""
                if isinstance(vsttime, (date, datetime)):
                    time_str = vsttime.strftime("%H:%M:%S")
                elif vsttime is not None:
                    # timedelta (MySQL TIME) หรือ string
                    time_str = str(vsttime)
                lines.append(f"  • VN {v.get('vn')} เวลา {time_str} (ovstist {v.get('ovstist') or '-'})")
            joined = "\n".join(lines)
            reply = QMessageBox.question(
                self,
                "มี visit วันนี้แล้ว",
                (
                    f"พบว่าคนไข้ CID {cid} มี visit วันนี้แล้ว:\n{joined}\n\n"
                    "ยืนยันจะเปิด visit เพิ่มหรือไม่?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
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

        dialog = DxDoctorDialog(
            default_dx,
            doctor_options,
            ovstist_options,
            default_doctor,
            default_ovstist,
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        dx_code, doctor_code, ovstist_code = dialog.values()
        if not dx_code or not doctor_code or not ovstist_code:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณาระบุ dx / doctor / ovstist ให้ครบ")
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

        payload = {
            "cid": cid,
            "visit_date": date.today().isoformat(),
            "dx_code": dx_code,
            "main_pdx": main_pdx,
            "doctor": doctor_code,
            "ovstist": ovstist_code,
        }

        try:
            vn = his.openVisitHosxp(payload)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            QMessageBox.critical(self, "เปิด Visit ไม่สำเร็จ", str(exc))
            return

        if not vn:
            QMessageBox.warning(self, "เปิด Visit ไม่สำเร็จ", "ไม่สามารถเปิด visit ได้")
            return

        save_settings({
            "LAST_DX_CODE": dx_code,
            "LAST_DOCTOR_CODE": doctor_code,
            "LAST_OVSTIST": ovstist_code,
        })

        QMessageBox.information(
            self,
            "เปิด Visit สำเร็จ",
            f"เปิด visit สำเร็จ\nCID: {cid}\nVN: {vn}",
        )
