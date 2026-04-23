from __future__ import annotations

import json
import sys

from openpyxl import Workbook
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List
from urllib import error as urlerror
from urllib import request as urlrequest

import pymysql
import pymysql.cursors
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QWidget,
)

from DataCenter_ui import DataCenterUI
from Setting_helper import get_settings, load_db_settings

SQL_FILE = "mysql_visit_type_count.sql"
API_URL = "https://dashboard.plkhealth.go.th/telemedicine/api/visit-type-daily"
LAST_SENT_KEY_PREFIX = "DataCenter/LastSentAt/"


def _last_sent_key(code: str) -> str:
    return f"{LAST_SENT_KEY_PREFIX}{code}"


def _load_last_sent(code: str) -> str:
    value = get_settings().value(_last_sent_key(code), "")
    return str(value or "")


def _save_last_sent(code: str, value: str) -> None:
    settings = get_settings()
    settings.setValue(_last_sent_key(code), value)
    settings.sync()


@dataclass
class DataSet:
    code: str
    name: str
    category: str
    source: str
    record_count: int = 0
    updated_at: str = ""
    rows: List[dict] = field(default_factory=list)
    error: str = ""


def _resolve_app_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


def _load_sql() -> str:
    sql_path = _resolve_app_path(SQL_FILE)
    return sql_path.read_text(encoding="utf-8")


def _fetch_visit_type_rows() -> List[dict]:
    db = load_db_settings()
    conn = pymysql.connect(
        host=str(db["host"]),
        port=int(db["port"]),
        user=str(db["user"]),
        password=str(db["password"]),
        database=str(db["database"]),
        charset=str(db["charset"]),
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(_load_sql())
            rows = cur.fetchall() or []
    finally:
        conn.close()

    normalized: List[dict] = []
    for row in rows:
        normalized.append({
            "hoscode": str(row.get("hoscode") or ""),
            "visit_date": str(row.get("visit_date") or ""),
            "visit_type_2": int(row.get("visit_type_2") or 0),
            "visit_type_3": int(row.get("visit_type_3") or 0),
            "visit_type_5": int(row.get("visit_type_5") or 0),
        })
    return normalized


class DataCenterWindow(DataCenterUI):
    def __init__(self) -> None:
        super().__init__()
        self._datasets: List[DataSet] = []

        self.btn_refresh.clicked.connect(self.load_datasets)
        self.search_input.textChanged.connect(self.apply_filter)

        self.load_datasets()

    def load_datasets(self) -> None:
        dataset = DataSet(
            code="DS-001",
            name="ร้อยละการให้บริการแพทย์ทางไกล",
            category="บริการ",
            source="HIS",
        )
        dataset.updated_at = _load_last_sent(dataset.code)
        self._datasets = [dataset]
        self.apply_filter()
        self.status_bar.showMessage("กด 'ดึงข้อมูล' เพื่อประมวลผล", 4000)

    def fetch_dataset(self, dataset: DataSet) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            rows = _fetch_visit_type_rows()
            dataset.rows = rows
            dataset.record_count = len(rows)
            dataset.error = ""
        except Exception as exc:  # pymysql errors, OSError, etc.
            dataset.error = str(exc)
            dataset.rows = []
            dataset.record_count = 0
        finally:
            QApplication.restoreOverrideCursor()

        self.apply_filter()
        if dataset.error:
            self.status_bar.showMessage(f"ดึงข้อมูลไม่สำเร็จ: {dataset.error}", 5000)
            QMessageBox.critical(self, "ดึงข้อมูล", f"ดึงข้อมูลไม่สำเร็จ:\n{dataset.error}")
        else:
            self.status_bar.showMessage(
                f"ดึงข้อมูลสำเร็จ {dataset.record_count:,} รายการ", 4000
            )

    def apply_filter(self) -> None:
        keyword = self.search_input.text().strip().lower()
        self.model.removeRows(0, self.model.rowCount())

        shown = 0
        for index, ds in enumerate(self._datasets, start=1):
            if keyword:
                haystack = " ".join([ds.code, ds.name, ds.category, ds.source]).lower()
                if keyword not in haystack:
                    continue

            row = [
                self._make_item(str(index), align_center=True),
                self._make_item(ds.code, align_center=True),
                self._make_item(ds.name),
                self._make_item(ds.category, align_center=True),
                self._make_item(ds.source, align_center=True),
                self._make_item(f"{ds.record_count:,}", align_right=True),
                self._make_item(ds.updated_at, align_center=True),
                self._make_item("", align_center=True),
                self._make_item("", align_center=True),
                self._make_item("", align_center=True),
            ]
            self.model.appendRow(row)
            row_index = self.model.rowCount() - 1
            self.table_view.setIndexWidget(
                self.model.index(row_index, self.process_column_index),
                self._build_process_cell(ds),
            )
            self.table_view.setIndexWidget(
                self.model.index(row_index, self.export_column_index),
                self._build_export_cell(ds),
            )
            self.table_view.setIndexWidget(
                self.model.index(row_index, self.action_column_index),
                self._build_action_cell(ds),
            )
            shown += 1

        self.table_view.resizeColumnsToContents()
        self.table_view.setColumnWidth(self.process_column_index, 110)
        self.table_view.setColumnWidth(self.export_column_index, 120)
        self.table_view.setColumnWidth(self.action_column_index, 110)
        total_records = sum(ds.record_count for ds in self._datasets)
        self.summary_label.setText(
            f"แสดง {shown}/{len(self._datasets)} ชุดข้อมูล • รวมทั้งสิ้น {total_records:,} รายการ"
        )

    def _build_process_cell(self, dataset: DataSet) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        button = QPushButton("ดึงข้อมูล")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            """
            QPushButton {
                background: #b45309;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #d97706; }
            QPushButton:pressed { background: #92400e; }
            """
        )
        button.clicked.connect(lambda _=False, ds=dataset: self.fetch_dataset(ds))

        layout.addWidget(button)
        return container

    def _build_export_cell(self, dataset: DataSet) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        button = QPushButton("ส่งออก XLSX")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            """
            QPushButton {
                background: #1e3a8a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #2a4fb3; }
            QPushButton:pressed { background: #18306f; }
            """
        )
        button.clicked.connect(lambda _=False, ds=dataset: self.export_dataset(ds))

        layout.addWidget(button)
        return container

    def export_dataset(self, dataset: DataSet) -> None:
        if dataset.error:
            QMessageBox.warning(self, "Export", f"ไม่สามารถส่งออกได้: {dataset.error}")
            return
        if not dataset.rows:
            QMessageBox.information(self, "Export", "ยังไม่มีข้อมูลให้ส่งออก")
            return

        default_name = f"{dataset.name}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "บันทึกไฟล์",
            str(Path.home() / default_name),
            "Excel Workbook (*.xlsx);;All Files (*.*)",
        )
        if not path:
            return

        fields = ["hoscode", "visit_date", "visit_type_2", "visit_type_3", "visit_type_5"]
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = dataset.code
            ws.append(fields)
            for row in dataset.rows:
                ws.append([row.get(k, "") for k in fields])
            wb.save(path)
        except OSError as exc:
            QMessageBox.critical(self, "Export", f"บันทึกไฟล์ไม่สำเร็จ: {exc}")
            return

        self.status_bar.showMessage(f"ส่งออก {len(dataset.rows)} แถว ไปที่ {path}", 5000)

    def _build_action_cell(self, dataset: DataSet) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        button = QPushButton("จัดส่ง")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(
            """
            QPushButton {
                background: #2f6b4c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #3b8a61; }
            QPushButton:pressed { background: #255a3f; }
            """
        )
        button.clicked.connect(lambda _=False, ds=dataset: self.send_dataset(ds))

        layout.addWidget(button)
        return container

    def send_dataset(self, dataset: DataSet) -> None:
        if dataset.error:
            QMessageBox.warning(
                self,
                "จัดส่งชุดข้อมูล",
                f"ไม่สามารถจัดส่งได้: {dataset.error}",
            )
            return
        if not dataset.rows:
            QMessageBox.information(
                self,
                "จัดส่งชุดข้อมูล",
                "ยังไม่มีข้อมูลให้จัดส่ง",
            )
            return

        payload: Any = dataset.rows if len(dataset.rows) > 1 else dataset.rows[0]
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            API_URL,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            with urlrequest.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                status_code = resp.status
        except urlerror.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            status_code = exc.code
        except urlerror.URLError as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "จัดส่งชุดข้อมูล", f"เชื่อมต่อไม่สำเร็จ: {exc.reason}")
            return
        finally:
            QApplication.restoreOverrideCursor()

        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw}

        sent_count = len(dataset.rows)
        pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
        if 200 <= status_code < 300 and parsed.get("status") == "success":
            sent_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save_last_sent(dataset.code, sent_at)
            dataset.updated_at = sent_at
            self.apply_filter()
            self.status_bar.showMessage(
                f"จัดส่ง {dataset.code} สำเร็จ ({sent_count} รายการ)", 5000
            )
            QMessageBox.information(
                self,
                "จัดส่งชุดข้อมูล",
                f"จัดส่ง {sent_count} รายการสำเร็จ\n\n{pretty}",
            )
        else:
            self.status_bar.showMessage(f"จัดส่ง {dataset.code} ไม่สำเร็จ", 5000)
            QMessageBox.critical(
                self,
                "จัดส่งชุดข้อมูล",
                f"HTTP {status_code}\n\n{pretty}",
            )

    @staticmethod
    def _make_item(text: str, *, align_center: bool = False, align_right: bool = False) -> QStandardItem:
        item = QStandardItem(text)
        if align_center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        elif align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return item
