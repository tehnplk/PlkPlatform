from __future__ import annotations

from PyQt6.QtCore import QLocale, QStringListModel, Qt
from PyQt6.QtGui import QFont, QStandardItemModel, QTextCursor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from Theme_helper import current_theme


SQL_COMPLETIONS = [
    "SELECT",
    "FROM",
    "WHERE",
    "LEFT JOIN",
    "INNER JOIN",
    "RIGHT JOIN",
    "JOIN",
    "ON",
    "AND",
    "OR",
    "GROUP BY",
    "ORDER BY",
    "HAVING",
    "LIMIT",
    "OFFSET",
    "WITH",
    "AS",
    "DISTINCT",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "COALESCE",
    "CONCAT",
    "DATE_FORMAT",
    "CURRENT_DATE",
]

HOSXP_TABLE_COMPLETIONS = [
    "an_stat",
    "clinic",
    "diagtype",
    "doctor",
    "drugitems",
    "er_regist",
    "icd101",
    "ipt",
    "income",
    "kskdepartment",
    "lab_head",
    "lab_order",
    "opdscreen",
    "opitemrece",
    "ovst",
    "ovst_diag",
    "ovst_seq",
    "ovstist",
    "ovstost",
    "patient",
    "person",
    "pttype",
    "referin",
    "referout",
    "spclty",
    "thaiaddress",
    "visit_pttype",
    "vn_stat",
    "ward",
    "xray_head",
    "xray_report",
]


class SqlEditor(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self._completion_model = QStringListModel(SQL_COMPLETIONS, self)
        self.completer = QCompleter(self._completion_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setWidget(self)
        self.completer.activated.connect(self._insert_completion)

    def keyPressEvent(self, event) -> None:
        if self.completer.popup().isVisible():
            if event.key() in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            ):
                event.ignore()
                return

        is_shortcut = (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Space
        )
        if not is_shortcut:
            super().keyPressEvent(event)

        prefix = self._completion_prefix()
        is_table_context = self._is_table_completion_context(prefix)
        words = HOSXP_TABLE_COMPLETIONS if is_table_context else SQL_COMPLETIONS
        min_prefix_length = 1 if is_table_context else 2

        if not is_shortcut and len(prefix) < min_prefix_length:
            self.completer.popup().hide()
            return

        self._completion_model.setStringList(words)
        self.completer.setCompletionPrefix(prefix)
        self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))
        rect = self.cursorRect()
        rect.setWidth(
            self.completer.popup().sizeHintForColumn(0)
            + self.completer.popup().verticalScrollBar().sizeHint().width()
        )
        self.completer.complete(rect)

    def _completion_prefix(self) -> str:
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def _is_table_completion_context(self, prefix: str) -> bool:
        cursor = self.textCursor()
        before_cursor = self.toPlainText()[: cursor.position()]
        if prefix:
            before_cursor = before_cursor[: -len(prefix)]

        tokens = before_cursor.lower().replace("\n", " ").split()
        if not tokens:
            return False

        return tokens[-1] in {"from", "form", "join"}

    def _insert_completion(self, completion: str) -> None:
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)


class QueryUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Query")
        self.resize(1100, 680)

        self.model = QStandardItemModel(0, 0, self)

        self.sql_editor = SqlEditor()
        self.sql_editor.setPlaceholderText("เขียน SQL แบบ SELECT เท่านั้น")
        self.sql_editor.setMinimumHeight(150)
        self.sql_editor.setFont(QFont("Consolas", 11))

        self.limit_label = QLabel("จำกัดแถว:")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 10000)
        self.limit_spin.setValue(500)
        self.limit_spin.setSingleStep(100)
        self.limit_spin.setLocale(QLocale.c())

        self.run_button = QPushButton("ประมวลผล")
        self.clear_button = QPushButton("ล้าง")
        self.export_button = QPushButton("ส่งออก Excel")
        self.export_button.setEnabled(False)

        self.summary_label = QLabel("ยังไม่มีข้อมูล")

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)

        control_bar = QHBoxLayout()
        control_bar.setContentsMargins(8, 8, 8, 0)
        control_bar.setSpacing(8)
        control_bar.addWidget(self.limit_label)
        control_bar.addWidget(self.limit_spin)
        control_bar.addStretch(1)
        control_bar.addWidget(self.export_button)
        control_bar.addWidget(self.clear_button)
        control_bar.addWidget(self.run_button)

        result_panel = QWidget()
        result_layout = QVBoxLayout(result_panel)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(6)
        result_layout.addLayout(control_bar)
        result_layout.addWidget(self.summary_label)
        result_layout.addWidget(self.table_view, 1)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.sql_editor)
        self.splitter.addWidget(result_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setSizes([180, 500])

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.splitter)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("พร้อมใช้งาน")

        self._apply_theme()

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.summary_label.setStyleSheet(
            f"color: {theme.primary}; font-size: 13px; font-weight: 700; padding: 4px 10px;"
        )
        self.limit_label.setStyleSheet(
            f"color: {theme.accent}; font-size: 13px; font-weight: 800;"
        )
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {theme.window}; }}
            QPlainTextEdit, QSpinBox {{
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 6px 8px;
                background: {theme.surface};
                color: {theme.text};
                selection-background-color: {theme.selection};
                selection-color: {theme.selection_text};
            }}
            QPlainTextEdit:focus, QSpinBox:focus {{ border: 1px solid {theme.primary}; }}
            QPushButton {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 700;
                color: {theme.primary};
            }}
            QPushButton:hover {{ background: {theme.surface_alt}; }}
            QPushButton:pressed {{ background: {theme.primary_soft}; }}
            QPushButton:disabled {{
                color: {theme.text_muted};
                background: {theme.surface_muted};
            }}
            QSplitter::handle {{
                background: {theme.border};
                height: 5px;
            }}
            QSplitter::handle:hover {{
                background: {theme.primary};
            }}
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
