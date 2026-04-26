from __future__ import annotations

from typing import Optional

import pandas as pd
from PyQt6.QtCore import QLocale, QObject, QSize, Qt, QThread
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from Theme_helper import current_theme


class BuddyCareExcelUI(QMainWindow):
    headers = ["ลำดับ", "เลือก", "วันที่ xls", "วันที่ hos", "คำนำหน้า", "ชื่อ", "นามสกุล", "สถานะ", "Reason", "CID", "VN", "VST_TYPE"]
    select_column_index = headers.index("เลือก")
    reason_column_index = headers.index("Reason")
    cid_column_index = headers.index("CID")
    default_done_status = "เข้าเยี่ยมเสร็จสิ้น"
    sort_role = Qt.ItemDataRole.UserRole + 1
    row_index_role = Qt.ItemDataRole.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BuddyCare Excel")
        self.resize(1100, 680)

        self.df: Optional[pd.DataFrame] = None
        self.lookup_thread: Optional[QThread] = None
        self.lookup_worker: Optional[QObject] = None
        self._is_rendering = False
        self._visible_indices: list[int] = []
        self.model = QStandardItemModel(0, len(self.headers))
        self.model.setHorizontalHeaderLabels(self.headers)
        self.model.setSortRole(self.sort_role)
        self.model.itemChanged.connect(self.on_item_changed)

        self.file_label = QLabel("ยังไม่ได้เลือกไฟล์ Excel")
        self.date_label = QLabel("วันที่ Excel:")
        self.date_filter = QComboBox()
        self.date_filter.setMinimumWidth(180)
        self.date_filter.setMinimumContentsLength(12)
        self.date_filter.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.date_filter.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        self.date_filter.view().setMinimumWidth(200)
        self.date_filter.setEnabled(False)
        self.date_filter.currentIndexChanged.connect(self.apply_filters)

        self.status_label = QLabel("สถานะ:")
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(260)
        self.status_filter.setMinimumContentsLength(20)
        self.status_filter.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.status_filter.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        self.status_filter.view().setMinimumWidth(320)
        self.status_filter.setEnabled(False)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.btn_choose = QPushButton("เลือกไฟล์ Excel")
        self.btn_choose.clicked.connect(self.choose_excel_file)
        self.btn_choose.setMinimumHeight(35)
        self.btn_choose.setMaximumHeight(35)

        theme = current_theme()
        toolbar_label_style = (
            f"font-size: 14px; color: {theme.accent}; font-weight: 800; padding: 0 4px;"
        )
        self.status_label.setStyleSheet(toolbar_label_style)
        self.date_label.setStyleSheet(toolbar_label_style)
        self.date_filter.setMinimumHeight(35)
        self.date_filter.setMaximumHeight(35)
        self.status_filter.setMinimumHeight(35)
        self.status_filter.setMaximumHeight(35)

        self.select_all_checkbox = QCheckBox("เลือกทั้งหมด")
        self.select_all_checkbox.setTristate(False)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        self.select_all_checkbox.setMinimumHeight(36)

        self.vn_filter = QComboBox()
        self.vn_filter.addItems(["ทั้งหมด", "มี VN แล้ว", "ไม่มี VN"])
        self.vn_filter.setMinimumWidth(140)
        self.vn_filter.setMinimumHeight(38)
        self.vn_filter.currentIndexChanged.connect(self.apply_filters)

        self.btn_open_visit = QPushButton("เปิด Visit")
        self.btn_open_visit.setMinimumHeight(40)
        self.btn_open_visit.setEnabled(False)
        self.btn_open_visit.clicked.connect(self.on_open_visit_clicked)

        self.lookup_result_label = QLabel("")
        self.lookup_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lookup_result_label.setMinimumHeight(36)
        self.lookup_result_label.setStyleSheet(
            f"color: {theme.primary}; font-size: 14px; font-weight: 700;"
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setLocale(QLocale.c())

        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("QToolBar { spacing: 10px; }")
        self.addToolBar(toolbar)
        toolbar.addWidget(self.btn_choose)
        toolbar.addSeparator()
        toolbar.addWidget(self.date_label)
        toolbar.addWidget(self.date_filter)
        toolbar.addSeparator()
        toolbar.addWidget(self.status_label)
        toolbar.addWidget(self.status_filter)
        toolbar.addSeparator()
        toolbar.addWidget(self.progress_bar)

        toolbar_widget = toolbar.widgetForAction(toolbar.actions()[0])
        if toolbar_widget is not None:
            toolbar_widget.setStyleSheet("font-size: 14px;")

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.on_table_double_click)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 52)
        self.table.setColumnWidth(self.reason_column_index, 360)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.file_label)

        select_row = QHBoxLayout()
        select_row.addWidget(self.select_all_checkbox)
        select_row.addSpacing(12)
        select_row.addWidget(self.vn_filter)
        select_row.addStretch(1)
        select_row.addWidget(self.lookup_result_label, 2)
        select_row.addStretch(1)
        select_row.addWidget(self.btn_open_visit)
        layout.addLayout(select_row)

        layout.addWidget(self.table)
        self.setCentralWidget(container)
        self.apply_modern_theme()

    def apply_modern_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {theme.window};
            }}
            QProgressBar {{
                border: 1px solid {theme.border};
                border-radius: 8px;
                background: {theme.surface_muted};
                text-align: center;
                color: {theme.text};
                font-weight: 700;
                min-height: 22px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.primary_hover}, stop:1 {theme.primary});
                border-radius: 7px;
            }}
            QToolBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.toolbar_start}, stop:1 {theme.toolbar_end});
                border: 1px solid {theme.border};
                border-radius: 12px;
                padding: 4px 12px;
            }}
            QLabel {{
                color: {theme.text};
                font-size: 14px;
                font-weight: 600;
            }}
            QCheckBox {{
                color: {theme.text};
                font-size: 15px;
                font-weight: 700;
                spacing: 10px;
                padding: 4px 2px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.accent}, stop:1 {theme.primary});
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.accent_hover}, stop:1 {theme.primary_hover});
            }}
            QPushButton:disabled {{
                background: {theme.disabled};
                color: {theme.disabled_text};
            }}
            QComboBox {{
                background: {theme.surface};
                color: {theme.text};
                border: 2px solid {theme.border};
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 14px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QTableView {{
                background: {theme.surface};
                alternate-background-color: {theme.surface_alt};
                border: 1px solid {theme.border};
                border-radius: 12px;
                color: {theme.text};
                font-size: 13px;
                selection-background-color: {theme.selection};
                selection-color: {theme.selection_text};
            }}
            QHeaderView::section {{
                background: {theme.surface_muted};
                color: {theme.primary};
                border: none;
                border-bottom: 1px solid {theme.border};
                padding: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )

    @staticmethod
    def display_excel_date(value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def build_sortable_date(value, *, dayfirst: bool) -> str:
        if pd.isna(value):
            return ""

        text = str(value).strip()
        if not text:
            return ""

        parsed = pd.to_datetime(text, errors="coerce", dayfirst=dayfirst)
        if pd.isna(parsed):
            return text.casefold()

        return parsed.strftime("%Y-%m-%d")
