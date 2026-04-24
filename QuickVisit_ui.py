from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


RESULT_COLUMNS = [
    ("HN", "hn"),
    ("CID", "cid"),
    ("ชื่อ-สกุล", "fullname"),
    ("เพศ", "sex"),
    ("วันเกิด", "birthday"),
    ("สิทธิ", "inscl"),
    ("เบอร์โทร", "mobile"),
]


class QuickVisitUI(QMainWindow):
    """UI สำหรับโมดูล Quick Visit — ค้นหาผู้ป่วยและเปิด visit อย่างเร็ว"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Quick Visit")
        self.resize(1100, 640)
        self._init_ui()
        self._apply_theme()

    # ---------------------------------------------------------------- build
    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # --- Search row ------------------------------------------------
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        search_row.addWidget(QLabel("ค้นหาคนไข้:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("พิมพ์ CID / HN / ชื่อ / นามสกุล (ค้นอัตโนมัติเมื่อพิมพ์ ≥ 2 ตัวอักษร)")
        self.search_input.setMinimumHeight(34)
        self.search_input.setClearButtonEnabled(True)
        search_row.addWidget(self.search_input, 1)

        root.addLayout(search_row)

        # --- Result table ---------------------------------------------
        self.result_model = QStandardItemModel(0, len(RESULT_COLUMNS), self)
        self.result_model.setHorizontalHeaderLabels([label for label, _ in RESULT_COLUMNS])

        self.result_table = QTableView()
        self.result_table.setModel(self.result_model)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        root.addWidget(self.result_table, 1)

        # --- Footer action row ----------------------------------------
        footer = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-size: 12px;")
        footer.addWidget(self.status_label, 1)

        self.open_visit_button = QPushButton("เปิด Visit")
        self.open_visit_button.setMinimumHeight(38)
        self.open_visit_button.setMinimumWidth(160)
        self.open_visit_button.setEnabled(False)
        footer.addWidget(self.open_visit_button)

        root.addLayout(footer)

    # ---------------------------------------------------------------- theme
    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f7f5; }
            QLabel { color: #1f5c3f; }
            QLineEdit, QComboBox {
                border: 1px solid #c4d6cc;
                border-radius: 6px;
                padding: 4px 8px;
                background: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #2f6b4c;
            }
            QPushButton {
                background: #2f6b4c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #3b8a61; }
            QPushButton:pressed { background: #255a3f; }
            QPushButton:disabled { background: #9eb7ac; color: #eef2ef; }
            QTableView {
                background: #ffffff;
                alternate-background-color: #f1f6f3;
                gridline-color: #d7e3dc;
                selection-background-color: #2f6b4c;
                selection-color: #ffffff;
                border: 1px solid #c4d6cc;
                border-radius: 6px;
            }
            QHeaderView::section {
                background: #1f5c3f;
                color: #ffffff;
                padding: 6px;
                border: none;
            }
            """
        )
