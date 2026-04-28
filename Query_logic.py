from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from PyQt6.QtCore import QObject, QSortFilterProxyModel, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from His_factory import make_his
from Query_ui import QueryUI


WRITE_KEYWORDS = re.compile(
    r"\b(insert|update|delete|replace|drop|alter|create|truncate|grant|revoke|"
    r"merge|call|execute|exec|set|lock|unlock|commit|rollback|vacuum|analyze)\b",
    re.IGNORECASE,
)
UNSAFE_SELECT_PATTERNS = re.compile(
    r"\binto\s+(outfile|dumpfile)\b|\bfor\s+update\b|\block\s+in\s+share\s+mode\b",
    re.IGNORECASE,
)


class QuerySortProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right) -> bool:
        left_value = left.data(Qt.ItemDataRole.UserRole)
        right_value = right.data(Qt.ItemDataRole.UserRole)
        return self._sort_key(left_value) < self._sort_key(right_value)

    @staticmethod
    def _sort_key(value):
        if value is None:
            return (0, "")
        if isinstance(value, bool):
            return (1, int(value))
        if isinstance(value, (int, float, Decimal)):
            return (2, float(value))
        if isinstance(value, (date, datetime)):
            return (3, value.isoformat())
        text = str(value)
        try:
            return (2, float(text.replace(",", "")))
        except ValueError:
            return (4, text.casefold())


class QueryWorker(QObject):
    finished = pyqtSignal(list, list)
    failed = pyqtSignal(str)

    def __init__(self, sql: str, limit: int) -> None:
        super().__init__()
        self.sql = sql
        self.limit = limit

    def run(self) -> None:
        try:
            safe_sql = validate_select_sql(self.sql)
            safe_sql = apply_limit(safe_sql, self.limit)
            his = make_his()
            cur = his.execute_with_retry(safe_sql, dict_cursor=False, commit=False)
            if cur is None:
                self.failed.emit("เชื่อมต่อ HIS ไม่สำเร็จ")
                return

            try:
                rows = cur.fetchall()
                columns = [desc[0] for desc in (cur.description or [])]
            finally:
                cur.close()
                try:
                    his.conn.rollback()
                except Exception:
                    pass

            self.finished.emit(columns, rows)
        except Exception as exc:
            self.failed.emit(str(exc))


def validate_select_sql(sql: str) -> str:
    cleaned = sql.strip()
    if not cleaned:
        raise ValueError("กรุณาระบุ SQL")

    cleaned = cleaned.rstrip(";").strip()
    if ";" in cleaned:
        raise ValueError("อนุญาตให้ประมวลผล SQL ได้ครั้งละ 1 statement เท่านั้น")

    first_word_match = re.match(r"^\s*([a-zA-Z]+)", cleaned)
    first_word = first_word_match.group(1).lower() if first_word_match else ""
    if first_word not in {"select", "with"}:
        raise ValueError("อนุญาตเฉพาะ SQL แบบ SELECT เท่านั้น")

    if WRITE_KEYWORDS.search(cleaned) or UNSAFE_SELECT_PATTERNS.search(cleaned):
        raise ValueError("พบคำสั่งที่ไม่อนุญาตใน Query module")

    return cleaned


def apply_limit(sql: str, limit: int) -> str:
    has_limit = re.search(
        r"\blimit\s+(\d+\s*,\s*)?\d+(\s+offset\s+\d+)?\s*$",
        sql,
        re.IGNORECASE,
    )
    if has_limit:
        return sql
    if re.match(r"^\s*with\b", sql, re.IGNORECASE):
        return f"{sql} LIMIT {int(limit)}"
    return f"SELECT * FROM ({sql}) AS query_module_result LIMIT {int(limit)}"


def format_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class QueryWindow(QueryUI):
    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: QueryWorker | None = None
        self.proxy_model = QuerySortProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.table_view.setModel(self.proxy_model)
        self.run_button.clicked.connect(self.run_query)
        self.clear_button.clicked.connect(self.clear_query)
        self.export_button.clicked.connect(self.export_excel)

    def run_query(self) -> None:
        if self._thread is not None:
            return

        sql = self.sql_editor.toPlainText()
        try:
            validate_select_sql(sql)
        except ValueError as exc:
            QMessageBox.warning(self, "Query", str(exc))
            return

        self.run_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.summary_label.setText("กำลังประมวลผล...")
        self.statusBar().showMessage("กำลังประมวลผล...")

        self._thread = QThread(self)
        self._worker = QueryWorker(sql, self.limit_spin.value())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._handle_result)
        self._worker.failed.connect(self._handle_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()

    def clear_query(self) -> None:
        self.sql_editor.clear()
        self.model.clear()
        self.export_button.setEnabled(False)
        self.summary_label.setText("ยังไม่มีข้อมูล")
        self.statusBar().showMessage("พร้อมใช้งาน")

    def export_excel(self) -> None:
        if self.proxy_model.rowCount() == 0:
            QMessageBox.information(self, "Query", "ไม่มีข้อมูลสำหรับส่งออก")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "บันทึกไฟล์ Excel",
            "query_result.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path = f"{file_path}.xlsx"

        try:
            columns = [
                self.proxy_model.headerData(col, Qt.Orientation.Horizontal)
                for col in range(self.proxy_model.columnCount())
            ]
            rows = []
            for row in range(self.proxy_model.rowCount()):
                values = []
                for col in range(self.proxy_model.columnCount()):
                    index = self.proxy_model.index(row, col)
                    values.append(index.data(Qt.ItemDataRole.DisplayRole))
                rows.append(values)

            pd.DataFrame(rows, columns=columns).to_excel(file_path, index=False)
            self.statusBar().showMessage(f"ส่งออก Excel สำเร็จ: {file_path}", 5000)
            QMessageBox.information(self, "Query", "ส่งออก Excel สำเร็จ")
        except Exception as exc:
            QMessageBox.warning(self, "Query", f"ส่งออก Excel ไม่สำเร็จ: {exc}")

    def _handle_result(self, columns: list, rows: list) -> None:
        self.model.clear()
        self.model.setColumnCount(len(columns))
        self.model.setHorizontalHeaderLabels([str(column) for column in columns])

        for row in rows:
            items = []
            for value in row:
                item = QStandardItem(format_cell(value))
                item.setData(value, Qt.ItemDataRole.UserRole)
                items.append(item)
            self.model.appendRow(items)

        self.table_view.resizeColumnsToContents()
        self.summary_label.setText(f"แสดงผล {len(rows):,} แถว")
        self.export_button.setEnabled(len(rows) > 0)
        self.statusBar().showMessage("ประมวลผลสำเร็จ", 5000)

    def _handle_error(self, message: str) -> None:
        self.summary_label.setText("ประมวลผลไม่สำเร็จ")
        self.statusBar().showMessage("ประมวลผลไม่สำเร็จ", 5000)
        QMessageBox.warning(self, "Query", message)

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None
        self.run_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.export_button.setEnabled(self.model.rowCount() > 0)
