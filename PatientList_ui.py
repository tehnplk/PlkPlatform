from __future__ import annotations

from PyQt6.QtCore import QDate, QLocale, QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygon, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


RESULT_COLUMNS = [
    ("VN", "vn"),
    ("วันที่", "vstdate"),
    ("เวลา", "vsttime"),
    ("CID", "cid"),
    ("HN", "hn"),
    ("ชื่อผู้ป่วย", "fullname"),
    ("สิทธิการรักษา", "pttype_name"),
    ("เลขที่สิทธิ", "pttypeno"),
    ("แพทย์ผู้ตรวจ", "doctor_name"),
]

RESULT_COLUMN_WIDTH_WEIGHTS = [12, 9, 8, 13, 8, 19, 18, 13, 16]
RESULT_COLUMN_MIN_WIDTHS = [100, 80, 70, 115, 70, 140, 130, 100, 130]


class PatientListHeader(QHeaderView):
    filter_clicked = pyqtSignal(int)
    _FILTER_AREA_WIDTH = 18

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._filtered_columns: set[int] = set()
        self._hovered_column = -1
        self.setSectionsClickable(True)
        self.setSectionsMovable(True)
        self.setHighlightSections(False)
        self.setMouseTracking(True)
        self.setSortIndicatorShown(False)
        self.sortIndicatorChanged.connect(self._handle_sort_indicator_changed)

    def _handle_sort_indicator_changed(self, _section: int, _order: Qt.SortOrder) -> None:
        self.setSortIndicatorShown(False)
        self.viewport().update()

    def set_filter_active(self, logical_index: int, active: bool) -> None:
        if active:
            self._filtered_columns.add(logical_index)
        else:
            self._filtered_columns.discard(logical_index)
        self.viewport().update()

    def _filter_area_rect(self, logical_index: int) -> QRect:
        x = self.sectionViewportPosition(logical_index)
        width = self.sectionSize(logical_index)
        return QRect(x + width - self._FILTER_AREA_WIDTH - 5, 4, self._FILTER_AREA_WIDTH, 16)

    def paintSection(self, painter, rect: QRect, logical_index: int) -> None:
        super().paintSection(painter, rect, logical_index)
        if logical_index < 0:
            return

        self._paint_header_state(painter, rect, logical_index)
        self._paint_sort_arrow(painter, rect, logical_index)
        if self._is_filter_visible(logical_index):
            self._paint_filter_icon(painter, logical_index)

    def _is_filter_visible(self, logical_index: int) -> bool:
        return logical_index == self._hovered_column or logical_index in self._filtered_columns

    def _paint_header_state(self, painter, rect: QRect, logical_index: int) -> None:
        color = None
        if logical_index in self._filtered_columns:
            color = QColor("#ccfbf1")
        if logical_index == self._hovered_column:
            color = QColor("#e0f2fe")
        if color is None:
            return

        color.setAlpha(170)
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.restore()

    def _paint_sort_arrow(self, painter, rect: QRect, logical_index: int) -> None:
        if self.sortIndicatorSection() != logical_index:
            return

        label = str(self.model().headerData(logical_index, self.orientation()) or "")
        label_width = self.fontMetrics().horizontalAdvance(label)
        arrow_center_x = rect.center().x() + (label_width // 2) + 8
        arrow_center_x = min(arrow_center_x, self._filter_area_rect(logical_index).left() - 8)
        arrow_center_y = rect.center().y()

        if self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder:
            arrow = QPolygon(
                [
                    QPoint(arrow_center_x, arrow_center_y - 4),
                    QPoint(arrow_center_x - 4, arrow_center_y + 3),
                    QPoint(arrow_center_x + 4, arrow_center_y + 3),
                ]
            )
        else:
            arrow = QPolygon(
                [
                    QPoint(arrow_center_x - 4, arrow_center_y - 3),
                    QPoint(arrow_center_x + 4, arrow_center_y - 3),
                    QPoint(arrow_center_x, arrow_center_y + 4),
                ]
            )

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#64748b"))
        painter.drawPolygon(arrow)
        painter.restore()

    def _paint_filter_icon(self, painter, logical_index: int) -> None:
        filter_area = self._filter_area_rect(logical_index)
        active = logical_index in self._filtered_columns
        color = QColor("#0891b2" if active else "#94a3b8")
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(color, 1.1))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        funnel_x = filter_area.left() + 4
        funnel_y = filter_area.top() + 2
        funnel = QPolygon(
            [
                QPoint(funnel_x, funnel_y),
                QPoint(funnel_x + 9, funnel_y),
                QPoint(funnel_x + 5, funnel_y + 6),
                QPoint(funnel_x + 5, funnel_y + 11),
                QPoint(funnel_x + 3, funnel_y + 12),
                QPoint(funnel_x + 3, funnel_y + 6),
            ]
        )
        painter.drawPolygon(funnel)
        painter.restore()

    def mousePressEvent(self, event) -> None:
        logical_index = self.logicalIndexAt(event.position().toPoint())
        if (
            logical_index >= 0
            and self._is_filter_visible(logical_index)
            and self._filter_area_rect(logical_index).contains(
            event.position().toPoint()
            )
        ):
            self.filter_clicked.emit(logical_index)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        logical_index = self.logicalIndexAt(event.position().toPoint())
        if logical_index != self._hovered_column:
            self._hovered_column = logical_index
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hovered_column != -1:
            self._hovered_column = -1
            self.viewport().update()
        super().leaveEvent(event)


class PatientListUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Patient List")
        self.resize(1040, 680)
        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 16)
        root.setSpacing(12)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        self.title_label = QLabel("Patient List")
        self.title_label.setObjectName("PageTitle")
        self.subtitle_label = QLabel("รายการผู้เข้ารับบริการประจำวัน")
        self.subtitle_label.setObjectName("PageSubtitle")
        title_group.addWidget(self.title_label)
        title_group.addWidget(self.subtitle_label)
        root.addLayout(title_group)

        self.filter_panel = QFrame()
        self.filter_panel.setObjectName("FilterPanel")
        filter_panel_layout = QHBoxLayout(self.filter_panel)
        filter_panel_layout.setContentsMargins(12, 10, 12, 10)
        filter_panel_layout.setSpacing(10)

        date_label = QLabel("วันที่รับบริการ")
        date_label.setObjectName("FieldLabel")
        filter_panel_layout.addWidget(date_label)

        self.visit_date_edit = QDateEdit()
        self.visit_date_edit.setObjectName("VisitDateEdit")
        self.visit_date_edit.setLocale(QLocale.c())
        self.visit_date_edit.setCalendarPopup(True)
        self.visit_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.visit_date_edit.setDate(QDate.currentDate())
        self.visit_date_edit.setMinimumHeight(36)
        self.visit_date_edit.setMinimumWidth(240)
        calendar = self.visit_date_edit.calendarWidget()
        if calendar is not None:
            calendar.setLocale(QLocale.c())
        filter_panel_layout.addWidget(self.visit_date_edit)

        self.table_hint_label = QLabel("ลากหัวตารางเพื่อสลับตำแหน่งคอลัมน์")
        self.table_hint_label.setObjectName("TableHint")
        filter_panel_layout.addWidget(self.table_hint_label)
        filter_panel_layout.addStretch(1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setMinimumHeight(36)
        self.refresh_button.setMinimumWidth(110)
        filter_panel_layout.addWidget(self.refresh_button)
        root.addWidget(self.filter_panel)

        self.summary_label = QLabel("ยังไม่มีข้อมูล")
        self.summary_label.setObjectName("SummaryLabel")
        root.addWidget(self.summary_label)

        self.result_model = QStandardItemModel(0, len(RESULT_COLUMNS), self)
        self.result_model.setHorizontalHeaderLabels([label for label, _ in RESULT_COLUMNS])

        self.result_table = QTableView()
        self.result_table.setObjectName("PatientTable")
        self.result_table.setModel(self.result_model)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSortingEnabled(True)
        self.result_table.setShowGrid(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.verticalHeader().setDefaultSectionSize(34)
        header = PatientListHeader(self.result_table)
        self.result_table.setHorizontalHeader(header)
        self.result_table.setSortingEnabled(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSortIndicatorShown(False)
        root.addWidget(self.result_table, 1)

        QTimer.singleShot(0, self.adjust_result_column_widths)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self.adjust_result_column_widths)

    def adjust_result_column_widths(self) -> None:
        available_width = self.result_table.viewport().width()
        if available_width <= 0:
            return

        total_weight = sum(RESULT_COLUMN_WIDTH_WEIGHTS)
        used_width = 0
        last_column = len(RESULT_COLUMNS) - 1
        for column, weight in enumerate(RESULT_COLUMN_WIDTH_WEIGHTS):
            if column == last_column:
                width = max(RESULT_COLUMN_MIN_WIDTHS[column], available_width - used_width)
            else:
                width = max(
                    RESULT_COLUMN_MIN_WIDTHS[column],
                    int(available_width * weight / total_weight),
                )
                used_width += width
            self.result_table.setColumnWidth(column, width)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f8fb;
            }
            QLabel {
                color: #1f2937;
            }
            QLabel#PageTitle {
                color: #0f172a;
                font-size: 22px;
                font-weight: 800;
            }
            QLabel#PageSubtitle {
                color: #64748b;
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#FieldLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#TableHint {
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
            }
            QLabel#SummaryLabel {
                color: #0f766e;
                font-size: 13px;
                font-weight: 700;
                padding: 2px 2px 0 2px;
            }
            QFrame#FilterPanel {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QDateEdit#VisitDateEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 5px 10px;
                background: #ffffff;
                color: #0f172a;
                font-size: 13px;
                font-weight: 600;
            }
            QDateEdit#VisitDateEdit:hover {
                border-color: #94a3b8;
            }
            QDateEdit#VisitDateEdit:focus {
                border: 1px solid #0891b2;
                background: #f8feff;
            }
            QPushButton#RefreshButton {
                background: #0891b2;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#RefreshButton:hover {
                background: #0e7490;
            }
            QPushButton#RefreshButton:pressed {
                background: #155e75;
            }
            QPushButton#RefreshButton:disabled {
                background: #cbd5e1;
                color: #f8fafc;
            }
            QTableView#PatientTable {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                color: #0f172a;
                gridline-color: #e2e8f0;
                selection-background-color: #dff6ff;
                selection-color: #0f172a;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 13px;
            }
            QTableView#PatientTable::item {
                padding: 5px 8px;
                border: none;
            }
            QTableView#PatientTable::item:selected {
                background: #dff6ff;
                color: #0f172a;
            }
            QHeaderView::section {
                background: #f1f5f9;
                color: #334155;
                padding: 8px 24px 8px 8px;
                border: none;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #dbe4ee;
                font-size: 12px;
                font-weight: 800;
            }
            QStatusBar {
                background: #f6f8fb;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
            }
            """
        )
