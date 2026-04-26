from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from Theme_helper import current_theme


class DataCenterUI(QMainWindow):
    headers = ["ลำดับ", "รหัส", "ชื่อชุดข้อมูล", "หมวดหมู่", "แหล่งข้อมูล", "จำนวนรายการ", "อัปเดตล่าสุด", "ประมวลผล", "Export", "Action"]
    process_column_index = headers.index("ประมวลผล")
    export_column_index = headers.index("Export")
    action_column_index = headers.index("Action")

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ศูนย์ข้อมูลกลาง")
        self.resize(1100, 680)

        self.model = QStandardItemModel(0, len(self.headers))
        self.model.setHorizontalHeaderLabels(self.headers)

        self.search_label = QLabel("ค้นหา:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("พิมพ์ชื่อชุดข้อมูล / หมวดหมู่ / แหล่งข้อมูล")
        self.search_input.setMinimumHeight(35)
        self.search_input.setMaximumHeight(35)

        self.btn_refresh = QPushButton("รีเฟรช")
        self.btn_refresh.setMinimumHeight(35)
        self.btn_refresh.setMaximumHeight(35)

        theme = current_theme()
        toolbar_label_style = (
            f"font-size: 14px; color: {theme.accent}; font-weight: 800; padding: 0 4px;"
        )
        self.search_label.setStyleSheet(toolbar_label_style)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 8, 8, 0)
        top_bar.setSpacing(8)
        top_bar.addWidget(self.search_label)
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(self.btn_refresh)

        self.summary_label = QLabel("ยังไม่มีข้อมูล")
        self.summary_label.setStyleSheet(
            f"color: {theme.primary}; font-size: 13px; font-weight: 700; padding: 6px 10px;"
        )

        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(top_bar)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.table_view, 1)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("พร้อมใช้งาน")

        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {theme.window}; }}
            QLineEdit {{
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 4px 8px;
                background: {theme.surface};
                color: {theme.text};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {theme.primary}; }}
            QPushButton {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 4px 14px;
                font-size: 13px;
                font-weight: 700;
                color: {theme.primary};
            }}
            QPushButton:hover {{ background: {theme.surface_alt}; }}
            QPushButton:pressed {{ background: {theme.primary_soft}; }}
            QTableView {{
                background: {theme.surface};
                alternate-background-color: {theme.surface_alt};
                color: {theme.text};
                gridline-color: {theme.grid};
                selection-background-color: {theme.selection};
                selection-color: {theme.selection_text};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background: {theme.surface_muted};
                color: {theme.primary};
                padding: 6px;
                border: 0;
                border-right: 1px solid {theme.border};
                font-weight: 800;
            }}
            QStatusBar {{
                background: {theme.surface_muted};
                color: {theme.primary};
                border-top: 1px solid {theme.border};
                font-weight: 600;
            }}
            """
        )
