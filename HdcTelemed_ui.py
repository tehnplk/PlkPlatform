from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from Theme_helper import button_style, current_theme


class HdcTelemedWindow(QMainWindow):
    """หน้าต่างสำหรับแสดงผลงานใน HDC ปัจจุบัน (Telemedicine)"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ผลงานใน HDC ปัจจุบัน")
        self.resize(1200, 700)

        self.model = QStandardItemModel()
        self.selected_year = str(datetime.now().year + 543)
        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header
        theme = current_theme()
        header_layout = QHBoxLayout()

        self.title_label = QLabel("ผลงาน Telemedicine ใน HDC ปัจจุบัน")
        self.title_label.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {theme.primary};"
        )

        self.year_label = QLabel("ปีงบประมาณ:")
        self.year_label.setStyleSheet(f"font-size: 12px; color: {theme.text};")

        self.year_combo = QComboBox()
        self.year_combo.addItems(["2567", "2568", "2569"])
        self.year_combo.setCurrentText(self.selected_year)
        self.year_combo.setMinimumWidth(100)

        self.status_label = QLabel("ยังไม่โหลดข้อมูล")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {theme.text_muted};")

        self.hoscode_label = QLabel("หน่วยบริการ: —")
        self.hoscode_label.setStyleSheet(f"font-size: 12px; color: {theme.danger}; font-weight: 600;")

        self.refresh_button = QPushButton("รีเฟรชข้อมูล")
        self.refresh_button.setMinimumWidth(150)
        self.refresh_button.clicked.connect(self.on_refresh)
        self.refresh_button.setStyleSheet(button_style("primary"))

        header_layout.addWidget(self.title_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(self.year_label)
        header_layout.addWidget(self.year_combo)
        header_layout.addStretch()
        header_layout.addWidget(self.hoscode_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.refresh_button)

        main_layout.addLayout(header_layout)

        # Table
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)

        main_layout.addWidget(self.table_view)

        self.statusBar().showMessage("พร้อมใช้งาน")

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {theme.window};
            }}
            QTableView {{
                background: {theme.surface};
                color: {theme.text};
                alternate-background-color: {theme.surface_alt};
                gridline-color: {theme.grid};
                border: 1px solid {theme.border};
                border-radius: 4px;
            }}
            QTableView::item {{
                color: {theme.text};
                padding: 4px;
            }}
            QTableView::item:selected {{
                background: {theme.selection};
                color: {theme.selection_text};
            }}
            QHeaderView::section {{
                background: {theme.surface_muted};
                color: {theme.primary};
                padding: 5px;
                border: 1px solid {theme.border};
                font-weight: 600;
            }}
            QPushButton {{
                background: {theme.primary};
                color: {theme.primary_text};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme.primary_hover};
            }}
            QPushButton:pressed {{
                background: {theme.primary_pressed};
            }}
            QPushButton:disabled {{
                background: {theme.disabled};
                color: {theme.disabled_text};
            }}
            QLabel {{
                color: {theme.primary};
            }}
            """
        )

    def on_refresh(self) -> None:
        """โหลดข้อมูลผลงาน Telemedicine จาก HDC"""
        self.selected_year = self.year_combo.currentText()
        self.statusBar().showMessage("กำลังโหลดข้อมูล...")
        self.refresh_button.setEnabled(False)

    def load_data(self, columns: list[str], rows: list[list[str]]) -> None:
        """โหลดข้อมูลลงในตาราง"""
        self.model.clear()
        self.model.setColumnCount(len(columns))
        self.model.setHorizontalHeaderLabels(columns)
        self.model.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QStandardItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.model.setItem(row_idx, col_idx, item)

        self.table_view.resizeColumnsToContents()
        self.status_label.setText(f"ข้อมูล {len(rows)} แถว")
        self.statusBar().showMessage(f"โหลดข้อมูลสำเร็จ ({len(rows)} แถว)", 3000)
        self.refresh_button.setEnabled(True)

    def load_error(self, message: str) -> None:
        """แสดงข้อผิดพลาด"""
        self.status_label.setText("เกิดข้อผิดพลาด")
        self.statusBar().showMessage(message, 5000)
        self.refresh_button.setEnabled(True)
