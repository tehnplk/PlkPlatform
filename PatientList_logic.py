from __future__ import annotations

from datetime import date, datetime

from PyQt6.QtCore import QSortFilterProxyModel, QObject, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from His_factory import make_his
from PatientList_ui import RESULT_COLUMNS, PatientListUI


class PatientListFilterProxy(QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self._column_filters: dict[int, str] = {}

    def set_column_filter(self, column: int, text: str) -> None:
        filter_text = text.strip().casefold()
        if filter_text:
            self._column_filters[column] = filter_text
        else:
            self._column_filters.pop(column, None)
        self.invalidateFilter()

    def column_filter(self, column: int) -> str:
        return self._column_filters.get(column, "")

    def has_column_filter(self, column: int) -> bool:
        return column in self._column_filters

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        model = self.sourceModel()
        if model is None:
            return True

        for column, filter_text in self._column_filters.items():
            index = model.index(source_row, column, source_parent)
            value = str(model.data(index, Qt.ItemDataRole.DisplayRole) or "").casefold()
            if filter_text not in value:
                return False
        return True


class PatientListWorker(QObject):
    finished = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, visit_date: str) -> None:
        super().__init__()
        self.visit_date = visit_date

    def run(self) -> None:
        sql = (
            "SELECT "
            "  o.vn, "
            "  o.vstdate, "
            "  o.vsttime, "
            "  p.cid, "
            "  o.hn, "
            "  CONCAT(COALESCE(p.pname, ''), COALESCE(p.fname, ''), ' ', COALESCE(p.lname, '')) AS fullname, "
            "  COALESCE(t.name, '') AS pttype_name, "
            "  o.pttypeno, "
            "  COALESCE(d.name, '') AS doctor_name "
            "FROM ovst o "
            "LEFT JOIN patient p ON p.hn = o.hn "
            "LEFT JOIN pttype t ON t.pttype = o.pttype "
            "LEFT JOIN doctor d ON d.code = o.doctor "
            "WHERE o.vstdate = %s "
            "ORDER BY o.vsttime, o.vn"
        )
        his = make_his()
        cur = his.get_cursor(dict_cursor=True)
        if cur is None:
            self.failed.emit("เชื่อมต่อ HIS ไม่สำเร็จ")
            return

        try:
            cur.execute(sql, (self.visit_date,))
            rows = list(cur.fetchall() or [])
        except Exception as exc:  # noqa: BLE001
            try:
                his.conn.rollback()
            except Exception:
                pass
            self.failed.emit(str(exc))
            return
        finally:
            cur.close()

        self.finished.emit(rows)


def _format_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class PatientListWindow(PatientListUI):
    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: PatientListWorker | None = None
        self.filter_proxy = PatientListFilterProxy()
        self.filter_proxy.setSourceModel(self.result_model)
        self.result_table.setModel(self.filter_proxy)

        self.refresh_button.clicked.connect(self.load_patients)
        self.visit_date_edit.dateChanged.connect(lambda _date: self.load_patients())
        self.result_table.horizontalHeader().filter_clicked.connect(self._open_filter_dialog)

        self.load_patients()

    def load_patients(self) -> None:
        if self._thread is not None:
            return

        visit_date = self.visit_date_edit.date().toString("yyyy-MM-dd")
        self.visit_date_edit.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.summary_label.setText("กำลังโหลดข้อมูล...")
        self.statusBar().showMessage("กำลังโหลดรายการผู้รับบริการ...")

        self._thread = QThread(self)
        self._worker = PatientListWorker(visit_date)
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

    def _handle_result(self, rows: list[dict]) -> None:
        self.result_model.setRowCount(0)
        for row in rows:
            items = []
            for _, key in RESULT_COLUMNS:
                item = QStandardItem(_format_cell(row.get(key)))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                items.append(item)
            self.result_model.appendRow(items)

        self.adjust_result_column_widths()
        self._update_summary_after_filter()
        self.statusBar().showMessage("โหลดรายการผู้รับบริการสำเร็จ", 5000)

    def _open_filter_dialog(self, column: int) -> None:
        column_label = RESULT_COLUMNS[column][0]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"ค้นหา: {column_label}")
        dialog.setModal(True)
        dialog.setMinimumWidth(340)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(f"ค้นหาในคอลัมน์ {column_label}")
        title_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        layout.addWidget(title_label)

        filter_input = QLineEdit()
        filter_input.setPlaceholderText("พิมพ์คำที่ต้องการค้นหา")
        filter_input.setText(self.filter_proxy.column_filter(column))
        filter_input.selectAll()
        filter_input.setMinimumHeight(34)
        layout.addWidget(filter_input)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 4, 0, 0)
        button_row.addStretch(1)
        clear_button = QPushButton("ล้างตัวกรอง")
        apply_button = QPushButton("ค้นหา")
        apply_button.setObjectName("ApplyFilterButton")
        clear_button.setMinimumHeight(32)
        apply_button.setMinimumHeight(32)
        button_row.addWidget(clear_button)
        button_row.addWidget(apply_button)
        layout.addLayout(button_row)

        dialog.setStyleSheet(
            """
            QDialog {
                background: #ffffff;
            }
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                color: #0f172a;
                background: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0891b2;
            }
            QPushButton {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                background: #f8fafc;
                color: #334155;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #eef2f7;
            }
            QPushButton#ApplyFilterButton {
                border: none;
                background: #0891b2;
                color: #ffffff;
            }
            QPushButton#ApplyFilterButton:hover {
                background: #0e7490;
            }
            """
        )
        clear_button.clicked.connect(lambda: self._apply_column_filter(dialog, column, ""))
        apply_button.clicked.connect(
            lambda: self._apply_column_filter(dialog, column, filter_input.text())
        )
        filter_input.returnPressed.connect(apply_button.click)

        dialog.exec()

    def _apply_column_filter(self, dialog: QDialog, column: int, text: str) -> None:
        self.filter_proxy.set_column_filter(column, text)
        header = self.result_table.horizontalHeader()
        if hasattr(header, "set_filter_active"):
            header.set_filter_active(column, self.filter_proxy.has_column_filter(column))
        self._update_summary_after_filter()
        dialog.accept()

    def _update_summary_after_filter(self) -> None:
        visit_date = self.visit_date_edit.date().toString("yyyy-MM-dd")
        total_rows = self.result_model.rowCount()
        visible_rows = self.filter_proxy.rowCount()
        if visible_rows == total_rows:
            self.summary_label.setText(f"วันที่ {visit_date} พบ {total_rows:,} รายการ")
        else:
            self.summary_label.setText(
                f"วันที่ {visit_date} แสดง {visible_rows:,} จาก {total_rows:,} รายการ"
            )

    def _handle_error(self, message: str) -> None:
        self.summary_label.setText("โหลดข้อมูลไม่สำเร็จ")
        self.statusBar().showMessage("โหลดรายการผู้รับบริการไม่สำเร็จ", 5000)
        QMessageBox.warning(self, "Patient List", message)

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None
        self.visit_date_edit.setEnabled(True)
        self.refresh_button.setEnabled(True)
