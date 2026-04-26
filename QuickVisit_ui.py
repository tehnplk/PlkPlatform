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

from Theme_helper import current_theme


RESULT_COLUMNS = [
    ("HN", "hn"),
    ("CID", "cid"),
    ("ชื่อ-สกุล", "fullname"),
    ("เพศ", "sex"),
    ("วันเกิด", "birthday"),
    ("อายุ", "age"),
    ("สิทธิ", "inscl"),
    ("TYPE_AREA", "type_area"),
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
        self.result_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        footer.addWidget(self.status_label, 1)

        self.open_visit_button = QPushButton("เปิด Visit")
        self.open_visit_button.setMinimumHeight(38)
        self.open_visit_button.setMinimumWidth(160)
        self.open_visit_button.setEnabled(False)
        footer.addWidget(self.open_visit_button)

        root.addLayout(footer)

    # ---------------------------------------------------------------- theme
    def _apply_theme(self) -> None:
        theme = current_theme()
        self.status_label.setStyleSheet(f"color: {theme.text_muted}; font-size: 12px;")
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {theme.window}; }}
            QLabel {{ color: {theme.primary}; }}
            QLineEdit, QComboBox {{
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 4px 8px;
                background: {theme.surface};
                color: {theme.text};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {theme.primary};
            }}
            QPushButton {{
                background: {theme.primary};
                color: {theme.primary_text};
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.primary_hover}; }}
            QPushButton:pressed {{ background: {theme.primary_pressed}; }}
            QPushButton:disabled {{ background: {theme.disabled}; color: {theme.disabled_text}; }}
            QTableView {{
                background: {theme.surface};
                alternate-background-color: {theme.surface_alt};
                color: {theme.text};
                gridline-color: {theme.grid};
                selection-background-color: {theme.primary};
                selection-color: #ffffff;
                border: 1px solid {theme.border};
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background: {theme.primary};
                color: {theme.primary_text};
                padding: 6px;
                border: none;
            }}
            """
        )
