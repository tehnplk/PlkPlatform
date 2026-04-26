from __future__ import annotations

import os
import time
import traceback
from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from PyQt6.QtCore import QLocale, QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QVBoxLayout,
)

from BuddyCareExcel_ui import BuddyCareExcelUI
from His_factory import make_his
from PersonDetail_dlg import DlgPersonDetail
from Setting_helper import load_db_settings, read_setting, save_settings

PREFIXES = ["นางสาว", "น.ส.", "นาง", "นาย", "ด.ญ.", "ด.ช.", "พระ"]
REQUIRED_COLUMNS = ["วันที่", "ชื่อ-สกุล", "สถานะ"]


def split_thai_name(full_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if pd.isna(full_name):
        return None, None, None

    normalized = str(full_name).strip()
    if not normalized:
        return None, None, None

    parts = normalized.split()
    if len(parts) < 2:
        return None, None, None

    lname = parts[-1].strip()
    first_part = " ".join(parts[:-1]).strip()

    pname = None
    fname = first_part
    for prefix in PREFIXES:
        if first_part.startswith(prefix):
            pname = prefix
            fname = first_part[len(prefix):].strip()
            break

    return pname, fname.strip(), lname.strip()


def load_excel_for_lookup(path: str) -> pd.DataFrame:
    raw_df = pd.read_excel(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in raw_df.columns]
    if missing:
        raise ValueError(f"ไฟล์ไม่มีคอลัมน์ที่จำเป็น: {', '.join(missing)}")

    raw_df = raw_df.copy()
    raw_df["__date_sort"] = pd.to_datetime(
        raw_df["วันที่"],
        errors="coerce",
        dayfirst=True,
    )
    raw_df["__original_order"] = range(len(raw_df))
    raw_df = raw_df.sort_values(
        by=["__date_sort", "__original_order"],
        ascending=[True, True],
        kind="mergesort",
        na_position="last",
    )

    parsed_rows = []
    for order_number, (_, row) in enumerate(raw_df.iterrows(), start=1):
        pname, fname, lname = split_thai_name(row.get("ชื่อ-สกุล", ""))
        parsed_rows.append(
            {
                "ลำดับ": order_number,
                "วันที่ xls": row.get("วันที่", ""),
                "วันที่ hos": "",
                "VN": row.get("VN", row.get("vn", "")),
                "VST_TYPE": row.get("VST_TYPE", row.get("vst_type", "")),
                "คำนำหน้า": pname or "",
                "ชื่อ": fname or "",
                "นามสกุล": lname or "",
                "สถานะ": row.get("สถานะ", ""),
                "Reason": row.get("เหตุผลในการนัดหมาย", ""),
                "cid": "",
            }
        )

    return pd.DataFrame(parsed_rows)


def create_db_connection():
    """Open a FRESH pymysql DictCursor connection.

    We intentionally do not return His_factory's singleton connection because
    callers close the returned connection, which would invalidate the shared
    HIS instance. The HIS lookup SQL here is MySQL-dialect only.
    """
    settings = load_db_settings()
    if not settings.get("host") or not settings.get("user") or not settings.get("database"):
        raise ConnectionError("ไม่พบค่าเชื่อมต่อฐานข้อมูล HIS")
    return pymysql.connect(
        host=settings["host"],
        port=int(settings["port"]),
        user=settings["user"],
        password=settings["password"],
        database=settings["database"],
        charset=settings.get("charset") or "utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
    )


def lookup_cid_value(cursor, fname: str, lname: str) -> str:
    normalized_fname = str(fname).strip()
    normalized_lname = str(lname).strip()
    if not normalized_fname or not normalized_lname:
        return ""

    sql_exact = (
        "SELECT cid FROM person "
        "WHERE TRIM(fname) = %s AND TRIM(lname) = %s "
        "LIMIT 1"
    )
    cursor.execute(sql_exact, (normalized_fname, normalized_lname))
    found = cursor.fetchone()

    if not found:
        sql_fuzzy = (
            "SELECT cid FROM person "
            "WHERE TRIM(fname) LIKE %s AND TRIM(lname) = %s "
            "LIMIT 1"
        )
        cursor.execute(sql_fuzzy, (f"%{normalized_fname}%", normalized_lname))
        found = cursor.fetchone()

    return found["cid"] if found else ""


def to_mysql_date(value) -> str:
    if value is None:
        return ""
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def lookup_hn_by_cid(cursor, cid: str) -> str:
    normalized_cid = str(cid).strip()
    if not normalized_cid:
        return ""

    sql = (
        "SELECT hn "
        "FROM patient "
        "WHERE TRIM(cid) = %s "
        "LIMIT 1"
    )
    cursor.execute(sql, (normalized_cid,))
    found = cursor.fetchone()
    if not found:
        return ""
    return str(found.get("hn", "") or "")


def lookup_visit_info_by_date_hn(cursor, date_xls, hn: str) -> dict[str, str]:
    mysql_date = to_mysql_date(date_xls)
    normalized_hn = str(hn).strip()
    if not mysql_date or not normalized_hn:
        return {"วันที่ hos": "", "VN": "", "VST_TYPE": ""}

    sql = (
        "SELECT "
        "DATE_FORMAT(vstdate, '%%Y-%%m-%%d') AS visit_date_db, "
        "o.vn, "
        "o.ovstist "
        "FROM ovst o "
        "WHERE TRIM(o.hn) = %s AND o.vstdate = %s "
        "ORDER BY o.vsttime DESC "
        "LIMIT 1"
    )
    cursor.execute(sql, (normalized_hn, mysql_date))
    found = cursor.fetchone()
    if not found:
        return {"วันที่ hos": "", "VN": "", "VST_TYPE": ""}

    return {
        "วันที่ hos": str(found.get("visit_date_db", "") or ""),
        "VN": str(found.get("vn", "") or ""),
        "VST_TYPE": str(found.get("ovstist", "") or ""),
    }


def lookup_visit_info_by_date_cid(cursor, date_xls, cid: str) -> dict[str, str]:
    normalized_cid = str(cid).strip()
    if not normalized_cid:
        return {"วันที่ hos": "", "VN": "", "VST_TYPE": ""}

    hn = lookup_hn_by_cid(cursor, normalized_cid)
    if not hn:
        return {"วันที่ hos": "", "VN": "", "VST_TYPE": ""}

    return lookup_visit_info_by_date_hn(cursor, date_xls, hn)


def lookup_icd101(cursor, code: str) -> Optional[dict[str, Any]]:
    normalized_code = str(code).strip().upper()
    if not normalized_code:
        return None

    sql = (
        "SELECT code, name "
        "FROM icd101 "
        "WHERE TRIM(code) = %s "
        "LIMIT 1"
    )
    cursor.execute(sql, (normalized_code,))
    return cursor.fetchone()


def load_doctor_options(cursor) -> list[tuple[str, str]]:
    sql = (
        "SELECT code, name "
        "FROM doctor "
        "ORDER BY code"
    )
    cursor.execute(sql)
    rows = cursor.fetchall() or []
    return [
        (str(row.get("code", "") or "").strip(), str(row.get("name", "") or "").strip())
        for row in rows
        if str(row.get("code", "") or "").strip()
    ]


def load_ovstist_options(cursor) -> list[tuple[str, str]]:
    sql = (
        "SELECT ovstist, name "
        "FROM ovstist "
        "WHERE TRIM(ovstist) <> '' "
        "ORDER BY ovstist"
    )
    cursor.execute(sql)
    rows = cursor.fetchall() or []
    return [
        (str(row.get("ovstist", "") or "").strip(), str(row.get("name", "") or "").strip())
        for row in rows
        if str(row.get("ovstist", "") or "").strip()
    ]


class DxDoctorDialog(QDialog):
    def __init__(
        self,
        dx_code: str,
        doctor_options: list[tuple[str, str]],
        ovstist_options: list[tuple[str, str]],
        default_doctor_code: str,
        default_ovstist: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ระบุรหัสวินิจฉัย")
        self.setModal(True)
        self.resize(460, 180)

        self.dx_input = QLineEdit(dx_code)
        self.dx_input.setPlaceholderText("เช่น Z718")

        self.doctor_combo = QComboBox()
        for code, name in doctor_options:
            label = f"{code} - {name}" if name else code
            self.doctor_combo.addItem(label, code)

        if default_doctor_code:
            index = self.doctor_combo.findData(default_doctor_code)
            if index >= 0:
                self.doctor_combo.setCurrentIndex(index)

        self.ovstist_combo = QComboBox()
        for code, name in ovstist_options:
            label = f"{code} - {name}" if name else code
            self.ovstist_combo.addItem(label, code)

        if default_ovstist:
            index = self.ovstist_combo.findData(default_ovstist)
            if index >= 0:
                self.ovstist_combo.setCurrentIndex(index)

        form = QFormLayout()
        form.addRow("รหัสวินิจฉัย", self.dx_input)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("ประเภทการมา", self.ovstist_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str]:
        dx_code = self.dx_input.text().strip().upper()
        doctor_code = str(self.doctor_combo.currentData() or "").strip()
        ovstist_code = str(self.ovstist_combo.currentData() or "").strip()
        return dx_code, doctor_code, ovstist_code


def get_person_detail_by_cid(cid: str) -> Optional[dict[str, Any]]:
    normalized_cid = str(cid).strip()
    if not normalized_cid:
        return None

    his = make_his()
    cursor = his.get_cursor(dict_cursor=True)
    if cursor is None:
        return None

    try:
        sql = (
            "SELECT "
            "person_id AS pid, "
            "patient_hn AS hn, "
            "cid, "
            "pname AS prename, "
            "fname, "
            "lname, "
            "sex, "
            "h.address AS house_no, "
            "v.village_moo AS village_moo, "
            "COALESCE(t.name, v.village_tambol_name) AS tambon "
            "FROM person p "
            "LEFT JOIN house h ON p.house_id = h.house_id "
            "LEFT JOIN village v ON h.village_id = v.village_id "
            "LEFT JOIN thaiaddress t ON v.address_id = t.addressid "
            "WHERE p.cid = %s "
            "LIMIT 1"
        )
        cursor.execute(sql, (normalized_cid,))
        return cursor.fetchone()
    finally:
        cursor.close()


class BuddyCareExcelWorker(QObject):
    progress_changed = pyqtSignal(int)
    finished = pyqtSignal(pd.DataFrame)
    failed = pyqtSignal(str)

    def __init__(self, df: pd.DataFrame) -> None:
        super().__init__()
        self.df = df.copy()

    def run(self) -> None:
        try:
            if self.df.empty:
                self.progress_changed.emit(100)
                self.finished.emit(self.df)
                return

            his = make_his()
            cursor = his.get_cursor(dict_cursor=True)
            if cursor is None:
                raise ConnectionError("ไม่สามารถสร้าง Database Cursor ได้")

            try:
                total = len(self.df)
                for i, (idx, row) in enumerate(self.df.iterrows(), start=1):
                    fname = str(row["ชื่อ"]).strip()
                    lname = str(row["นามสกุล"]).strip()
                    cid_value = lookup_cid_value(cursor, fname, lname)
                    self.df.at[idx, "cid"] = cid_value

                    visit_info = lookup_visit_info_by_date_cid(
                        cursor,
                        row.get("วันที่ xls", ""),
                        cid_value,
                    )
                    self.df.at[idx, "วันที่ hos"] = visit_info["วันที่ hos"]
                    self.df.at[idx, "VN"] = visit_info["VN"]
                    self.df.at[idx, "VST_TYPE"] = visit_info["VST_TYPE"]
                    self.progress_changed.emit(int((i / total) * 100))
            finally:
                cursor.close()

            self.finished.emit(self.df)
        except Exception as exc:  # noqa: BLE001
            print(f"[BuddyCareExcelWorker] error: {exc}")
            traceback.print_exc()
            self.failed.emit(str(exc))


class BuddyCareExcelWindow(BuddyCareExcelUI):
    def show_progress_splash(self, title: str, message: str, maximum: int) -> None:
        self.close_progress_splash()
        self.progress_splash = QProgressDialog(message, None, 0, max(maximum, 0), self)
        self.progress_splash.setWindowTitle(title)
        self.progress_splash.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_splash.setCancelButton(None)
        self.progress_splash.setAutoClose(False)
        self.progress_splash.setAutoReset(False)
        self.progress_splash.setMinimumDuration(0)
        self.progress_splash.setValue(0)
        self.progress_splash.setMinimumWidth(420)
        self.progress_splash.setLocale(QLocale.c())
        self.progress_splash.show()
        QApplication.processEvents()

    def update_progress_splash(self, value: int, message: str | None = None) -> None:
        splash = getattr(self, "progress_splash", None)
        if splash is None:
            return
        if message:
            splash.setLabelText(message)
        splash.setValue(value)
        QApplication.processEvents()

    def close_progress_splash(self) -> None:
        splash = getattr(self, "progress_splash", None)
        if splash is None:
            return
        splash.close()
        splash.deleteLater()
        self.progress_splash = None
        QApplication.processEvents()

    def choose_excel_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "เลือกไฟล์ Excel",
            str(Path.cwd()),
            "Excel Files (*.xlsx *.xls)",
        )
        if not path:
            return

        try:
            self.df = load_excel_for_lookup(path)
            self.df["__selected"] = False
        except ValueError as exc:
            print(f"[choose_excel_file] validation error: {exc}")
            QMessageBox.warning(self, "คอลัมน์ไม่ครบ", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[choose_excel_file] error: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "อ่านไฟล์ไม่สำเร็จ", f"ไม่สามารถอ่านไฟล์ Excel ได้\n{exc}")
            return

        self.file_label.setText(f"ไฟล์: {path} | จำนวนรายการ: {len(self.df)}")
        self.lookup_result_label.clear()
        self.reset_filters()
        self.apply_filters()
        self.lookup_cid()

    def lookup_cid(self) -> None:
        if self.df is None or self.df.empty:
            QMessageBox.information(self, "ไม่มีข้อมูล", "กรุณาเลือกไฟล์ Excel ก่อน")
            return

        if self.lookup_thread is not None and self.lookup_thread.isRunning():
            return

        self.btn_choose.setEnabled(False)
        self.date_filter.setEnabled(False)
        self.status_filter.setEnabled(False)
        self.lookup_result_label.setText("กำลังค้นใน HOS...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.show_progress_splash("กำลังทำงาน", "กำลังค้นข้อมูลใน HOS...", 100)

        self.lookup_thread = QThread(self)
        self.lookup_worker = BuddyCareExcelWorker(self.df)
        self.lookup_worker.moveToThread(self.lookup_thread)

        self.lookup_thread.started.connect(self.lookup_worker.run)
        self.lookup_worker.progress_changed.connect(self.progress_bar.setValue)
        self.lookup_worker.progress_changed.connect(
            lambda value: self.update_progress_splash(value, f"กำลังค้นข้อมูลใน HOS... {value}%")
        )
        self.lookup_worker.finished.connect(self.on_lookup_finished)
        self.lookup_worker.failed.connect(self.on_lookup_failed)

        self.lookup_worker.finished.connect(self.lookup_thread.quit)
        self.lookup_worker.failed.connect(self.lookup_thread.quit)
        self.lookup_thread.finished.connect(self.lookup_worker.deleteLater)
        self.lookup_thread.finished.connect(self.lookup_thread.deleteLater)
        self.lookup_thread.finished.connect(self.on_lookup_thread_finished)

        self.lookup_thread.start()

    def on_lookup_finished(self, updated_df: pd.DataFrame) -> None:
        self.df = updated_df
        if "__selected" not in self.df.columns:
            self.df["__selected"] = False

        found_cid_count = self.count_non_empty_values(self.df, "cid")
        found_vn_count = self.count_non_empty_values(self.df, "VN")

        self.apply_filters()
        status_index = self.status_filter.findText(self.default_done_status)
        if status_index >= 0:
            self.status_filter.setCurrentIndex(status_index)
        self.progress_bar.setValue(100)
        self.lookup_result_label.setText(
            " | ".join(
                [
                    f"พบ CID ตรงกับ Excel {found_cid_count} คน",
                    f"พบ VN ตรงกับ Excel {found_vn_count} คน",
                ]
            )
        )

    def on_lookup_failed(self, error_message: str) -> None:
        self.lookup_result_label.clear()
        print(f"[on_lookup_failed] {error_message}")
        QMessageBox.critical(self, "ค้นใน HOS ไม่สำเร็จ", error_message)

    def on_lookup_thread_finished(self) -> None:
        self.progress_bar.setVisible(False)
        self.close_progress_splash()
        self.btn_choose.setEnabled(True)
        self.date_filter.setEnabled(self.df is not None and not self.df.empty)
        self.status_filter.setEnabled(self.df is not None and not self.df.empty)
        self.update_open_visit_button_state()
        self.lookup_worker = None
        self.lookup_thread = None

    @staticmethod
    def count_non_empty_values(df: pd.DataFrame, column_name: str) -> int:
        if column_name not in df.columns:
            return 0

        return int(
            df[column_name]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

    def update_open_visit_button_state(self) -> None:
        if self.df is None or self.df.empty:
            self.btn_open_visit.setEnabled(False)
            self.btn_open_visit.setText("เปิด Visit")
            return

        selected_with_cid = self.df[
            self.df["__selected"].fillna(False)
            & self.df["cid"].fillna("").astype(str).str.strip().ne("")
            & self.df["VN"].fillna("").astype(str).str.strip().eq("")
        ]
        selected_count = len(selected_with_cid)
        self.btn_open_visit.setEnabled(selected_count > 0)
        if selected_count > 0:
            self.btn_open_visit.setText(f"เปิด Visit {selected_count} คน")
        else:
            self.btn_open_visit.setText("เปิด Visit")

    @staticmethod
    def has_text_value(value) -> bool:
        if pd.isna(value):
            return False
        return str(value).strip() != ""

    def is_row_selectable(self, row: pd.Series) -> bool:
        return not self.has_text_value(row.get("VN", ""))

    def get_selectable_visible_indices(self) -> list[int]:
        if self.df is None:
            return []

        selectable_indices: list[int] = []
        for df_index in self._visible_indices:
            if df_index not in self.df.index:
                continue
            if self.is_row_selectable(self.df.loc[df_index]):
                selectable_indices.append(df_index)
        return selectable_indices

    def reset_filters(self) -> None:
        self.date_filter.blockSignals(True)
        self.date_filter.clear()
        self.date_filter.addItem("ทั้งหมด")

        if self.df is not None and not self.df.empty:
            formatted_dates = self.df["วันที่ xls"].apply(self.display_excel_date)
            dates = sorted({date_text for date_text in formatted_dates if date_text})
            for date_text in dates:
                self.date_filter.addItem(date_text)
            self.date_filter.setEnabled(True)
        else:
            self.date_filter.setEnabled(False)

        self.date_filter.setCurrentIndex(0)
        self.date_filter.blockSignals(False)

        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("ทั้งหมด")

        if self.df is not None and not self.df.empty:
            statuses = sorted({str(v).strip() for v in self.df["สถานะ"].dropna() if str(v).strip()})
            for status in statuses:
                self.status_filter.addItem(status)
            self.status_filter.setEnabled(True)
        else:
            self.status_filter.setEnabled(False)

        self.status_filter.setCurrentIndex(0)
        self.status_filter.blockSignals(False)
        self.refresh_select_all_state()

    def apply_filters(self) -> None:
        if self.df is None:
            self._visible_indices = []
            self.render_table(pd.DataFrame(columns=self.headers))
            self.refresh_select_all_state()
            self.update_open_visit_button_state()
            return

        filtered_df = self.df

        selected_date = self.date_filter.currentText().strip()
        if selected_date and selected_date != "ทั้งหมด":
            date_mask = filtered_df["วันที่ xls"].apply(self.display_excel_date) == selected_date
            filtered_df = filtered_df[date_mask]

        selected_status = self.status_filter.currentText().strip()
        if selected_status and selected_status != "ทั้งหมด":
            filtered_df = filtered_df[
                filtered_df["สถานะ"].astype(str).str.strip() == selected_status
            ]

        selected_vn_filter = self.vn_filter.currentText().strip()
        if selected_vn_filter == "มี VN แล้ว":
            filtered_df = filtered_df[
                filtered_df["VN"].fillna("").astype(str).str.strip().ne("")
            ]
        elif selected_vn_filter == "ไม่มี VN":
            filtered_df = filtered_df[
                filtered_df["VN"].fillna("").astype(str).str.strip().eq("")
            ]

        self._visible_indices = filtered_df.index.tolist()
        self.render_table(filtered_df)
        self.refresh_select_all_state()
        self.update_open_visit_button_state()

    def render_table(self, df: pd.DataFrame) -> None:
        self._is_rendering = True
        self.model.setRowCount(0)

        for _, row in df.iterrows():
            order_item = QStandardItem("" if pd.isna(row.get("ลำดับ", "")) else str(row.get("ลำดับ", "")))
            order_item.setEditable(False)
            order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            checkbox_item = QStandardItem()
            checkbox_item.setCheckable(True)
            checkbox_item.setEditable(False)
            is_selectable = self.is_row_selectable(row)
            if not is_selectable and self.df is not None:
                self.df.at[int(row.name), "__selected"] = False
            is_selected = is_selectable and bool(row.get("__selected", False))
            df_index = int(row.name)
            order_item.setData(df_index, self.row_index_role)
            checkbox_item.setCheckState(
                Qt.CheckState.Checked if is_selected else Qt.CheckState.Unchecked
            )
            checkbox_item.setEnabled(is_selectable)
            checkbox_item.setData(df_index, self.row_index_role)
            checkbox_item.setData(1 if is_selected else 0, self.sort_role)
            sort_value = pd.to_numeric(order_item.text(), errors="coerce")
            order_item.setData(
                int(sort_value) if not pd.isna(sort_value) else order_item.text().casefold(),
                self.sort_role,
            )

            values = [
                self.display_excel_date(row.get("วันที่ xls", "")),
                row.get("วันที่ hos", ""),
                row.get("คำนำหน้า", ""),
                row.get("ชื่อ", ""),
                row.get("นามสกุล", ""),
                row.get("สถานะ", ""),
                row.get("Reason", ""),
                row.get("cid", ""),
                row.get("VN", ""),
                row.get("VST_TYPE", ""),
            ]

            items = [order_item, checkbox_item]
            for column_index, value in enumerate(values, start=2):
                text = "" if pd.isna(value) else str(value)
                item = QStandardItem(text)
                item.setEditable(False)
                if column_index == self.reason_column_index:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(df_index, self.row_index_role)
                if column_index == 2:
                    sort_value = self.build_sortable_date(text, dayfirst=True)
                elif column_index == 3:
                    sort_value = self.build_sortable_date(text, dayfirst=False)
                else:
                    sort_value = text.casefold()
                item.setData(sort_value, self.sort_role)
                items.append(item)

            self.model.appendRow(items)

        sort_column = self.table.horizontalHeader().sortIndicatorSection()
        sort_order = self.table.horizontalHeader().sortIndicatorOrder()
        if self.model.rowCount() > 0:
            self.model.sort(sort_column, sort_order)

        self._is_rendering = False

    def on_item_changed(self, item: QStandardItem) -> None:
        if self._is_rendering:
            return
        if item.column() != self.select_column_index:
            return
        if self.df is None:
            return
        df_index = item.data(self.row_index_role)
        if df_index is None or df_index not in self.df.index:
            return
        if not self.is_row_selectable(self.df.loc[df_index]):
            self.df.at[df_index, "__selected"] = False
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(0, self.sort_role)
            return

        self.df.at[df_index, "__selected"] = item.checkState() == Qt.CheckState.Checked
        item.setData(1 if item.checkState() == Qt.CheckState.Checked else 0, self.sort_role)
        self.refresh_select_all_state()
        self.update_open_visit_button_state()

    def on_select_all_changed(self, state: int) -> None:
        if self.df is None or not self._visible_indices:
            return
        if self._is_rendering:
            return

        checked = state == Qt.CheckState.Checked.value
        for df_index in self.get_selectable_visible_indices():
            self.df.at[df_index, "__selected"] = checked
        self.apply_filters()

    def refresh_select_all_state(self) -> None:
        self.select_all_checkbox.blockSignals(True)
        selectable_indices = self.get_selectable_visible_indices()
        if self.df is None or not selectable_indices:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.select_all_checkbox.setEnabled(False)
        else:
            self.select_all_checkbox.setEnabled(True)
            selected_values = [bool(self.df.at[i, "__selected"]) for i in selectable_indices]
            if all(selected_values):
                self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.select_all_checkbox.blockSignals(False)

    def on_open_visit_clicked(self) -> None:
        if self.df is None or self.df.empty:
            QMessageBox.information(self, "ไม่มีข้อมูล", "กรุณาเลือกไฟล์ Excel ก่อน")
            return

        selected_df = self.df[
            self.df["__selected"].fillna(False)
            & self.df["cid"].fillna("").astype(str).str.strip().ne("")
            & self.df["VN"].fillna("").astype(str).str.strip().eq("")
        ]
        if selected_df.empty:
            QMessageBox.information(
                self,
                "ยังไม่พร้อมเปิด Visit",
                "กรุณาค้นใน HOS ให้พบ CID และติ๊กเลือกอย่างน้อย 1 รายการ",
            )
            return

        preview = selected_df[["cid", "วันที่ xls"]].fillna("").head(20)
        lines = [
            f"CID: {r['cid']} | VST_DATE: {self.display_excel_date(r['วันที่ xls'])}"
            for _, r in preview.iterrows()
        ]
        suffix = ""
        if len(selected_df) > 20:
            suffix = f"\n... และอีก {len(selected_df) - 20} รายการ"

        reply = QMessageBox.question(
            self,
            "ยืนยันเปิด Visit",
            "ต้องการเปิด Visit สำหรับรายการที่เลือกหรือไม่\n\n"
            + "\n".join(lines)
            + suffix,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        dx_code = read_setting("LAST_DX_CODE", "Z718").strip().upper() or "Z718"
        default_doctor_code = read_setting("LAST_DOCTOR_CODE", "0010").strip() or "0010"
        default_ovstist = read_setting("LAST_OVSTIST", "05").strip() or "05"
        icd_row = None
        selected_doctor_code = default_doctor_code
        selected_ovstist = default_ovstist
        try:
            icd_conn = create_db_connection()
            icd_cursor = icd_conn.cursor()
            try:
                doctor_options = load_doctor_options(icd_cursor)
                ovstist_options = load_ovstist_options(icd_cursor)
            finally:
                icd_cursor.close()
                icd_conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"[on_open_visit_clicked] load doctor options failed: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "โหลดรายชื่อ Doctor ไม่สำเร็จ", str(exc))
            return

        if not doctor_options:
            QMessageBox.warning(self, "ไม่พบรายชื่อ Doctor", "ไม่พบข้อมูลในตาราง doctor")
            return
        if not ovstist_options:
            QMessageBox.warning(self, "ไม่พบข้อมูล ovstist", "ไม่พบข้อมูลในตาราง ovstist")
            return

        while True:
            dialog = DxDoctorDialog(
                dx_code,
                doctor_options,
                ovstist_options,
                selected_doctor_code,
                selected_ovstist,
                self,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            dx_code, selected_doctor_code, selected_ovstist = dialog.values()
            if not dx_code:
                QMessageBox.warning(self, "ยังไม่ได้ระบุรหัสวินิจฉัย", "กรุณาระบุรหัสวินิจฉัยก่อน process open visit")
                continue
            if not selected_doctor_code:
                QMessageBox.warning(self, "ยังไม่ได้เลือก Doctor", "กรุณาเลือก Doctor ก่อน process open visit")
                continue
            if not selected_ovstist:
                QMessageBox.warning(self, "ยังไม่ได้เลือก ovstist", "กรุณาเลือก ovstist ก่อน process open visit")
                continue

            try:
                icd_conn = create_db_connection()
                icd_cursor = icd_conn.cursor()
                try:
                    icd_row = lookup_icd101(icd_cursor, dx_code)
                finally:
                    icd_cursor.close()
                    icd_conn.close()
            except Exception as exc:  # noqa: BLE001
                print(f"[on_open_visit_clicked] icd101 lookup failed for {dx_code}: {exc}")
                traceback.print_exc()
                QMessageBox.critical(self, "ตรวจสอบรหัสวินิจฉัยไม่สำเร็จ", str(exc))
                return

            if icd_row:
                break

            QMessageBox.warning(
                self,
                "ไม่พบรหัสวินิจฉัย",
                f"ไม่พบรหัส {dx_code} ในตาราง icd101\nกรุณากรอกใหม่หรือกดยกเลิก",
            )

        main_pdx = dx_code[:3] if len(dx_code) >= 3 else dx_code

        try:
            his = make_his()
        except Exception as exc:  # noqa: BLE001
            print(f"[on_open_visit_clicked] cannot create His: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "เชื่อมต่อ HIS ไม่สำเร็จ", str(exc))
            return

        if not his.his_is_connected():
            QMessageBox.critical(self, "เชื่อมต่อ HIS ไม่สำเร็จ", "ไม่สามารถเชื่อมต่อฐานข้อมูล HIS ได้")
            return

        success_count = 0
        error_messages: list[str] = []
        total_selected = len(selected_df)
        self.show_progress_splash("กำลังเปิด Visit", f"กำลังเปิด Visit 0/{total_selected}", total_selected)

        for processed_count, (idx, row) in enumerate(selected_df.iterrows(), start=1):
            cid = str(row.get("cid", "") or "").strip()
            visit_date = to_mysql_date(row.get("วันที่ xls", ""))
            self.update_progress_splash(
                processed_count - 1,
                f"กำลังเปิด Visit {processed_count}/{total_selected}\nCID: {cid or '-'}",
            )
            if not cid or not visit_date:
                error_messages.append(f"แถว {idx + 1}: ข้อมูล CID หรือวันที่ไม่ถูกต้อง")
                self.update_progress_splash(
                    processed_count,
                    f"กำลังเปิด Visit {processed_count}/{total_selected}\nCID: {cid or '-'}",
                )
                continue

            payload = {
                "cid": cid,
                "visit_date": visit_date,
                "dx_code": dx_code,
                "main_pdx": main_pdx,
                "doctor": selected_doctor_code,
                "ovstist": selected_ovstist,
            }

            try:
                vn = his.openVisitHosxp(payload)
                if not vn:
                    error_messages.append(f"CID {cid}: เปิด Visit ไม่สำเร็จ")
                    self.update_progress_splash(
                        processed_count,
                        f"กำลังเปิด Visit {processed_count}/{total_selected}\nCID: {cid or '-'}",
                    )
                    continue

                lookup_conn = create_db_connection()
                lookup_cursor = lookup_conn.cursor()
                try:
                    visit_info = lookup_visit_info_by_date_cid(
                        lookup_cursor,
                        row.get("วันที่ xls", ""),
                        cid,
                    )
                finally:
                    lookup_cursor.close()
                    lookup_conn.close()
                self.df.at[idx, "วันที่ hos"] = visit_info["วันที่ hos"] or visit_date
                self.df.at[idx, "VN"] = str(vn)
                self.df.at[idx, "VST_TYPE"] = "05"
                self.df.at[idx, "__selected"] = False
                success_count += 1
            except Exception as exc:  # noqa: BLE001
                print(f"[on_open_visit_clicked] open visit failed for CID {cid}: {exc}")
                traceback.print_exc()
                error_messages.append(f"CID {cid}: {exc}")

            self.update_progress_splash(
                processed_count,
                f"กำลังเปิด Visit {processed_count}/{total_selected}\nCID: {cid or '-'}",
            )

        self.close_progress_splash()
        self.apply_filters()

        if success_count > 0:
            save_settings({
                "LAST_DX_CODE": dx_code,
                "LAST_DOCTOR_CODE": selected_doctor_code,
                "LAST_OVSTIST": selected_ovstist,
            })

        message_lines = [f"เปิด Visit สำเร็จ {success_count} รายการ"]
        if error_messages:
            message_lines.append("")
            message_lines.extend(error_messages[:10])
            if len(error_messages) > 10:
                message_lines.append(f"... และอีก {len(error_messages) - 10} รายการ")

        QMessageBox.information(self, "ผลการเปิด Visit", "\n".join(message_lines))

    def on_table_double_click(self, index) -> None:
        if index.column() != self.cid_column_index:
            return

        cid_value = self.model.item(index.row(), self.cid_column_index).text().strip()
        if not cid_value:
            QMessageBox.information(self, "ไม่มี CID", "เซลล์ CID นี้ว่างอยู่")
            return

        try:
            detail = get_person_detail_by_cid(cid_value)
        except Exception as exc:  # noqa: BLE001
            print(f"[on_table_double_click] error fetching person detail for CID {cid_value}: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "ดึงข้อมูลไม่สำเร็จ", str(exc))
            return

        if not detail:
            QMessageBox.information(self, "ไม่พบข้อมูล", f"ไม่พบข้อมูล person ของ CID: {cid_value}")
            return

        dialog = DlgPersonDetail(detail, self)
        dialog.exec()
