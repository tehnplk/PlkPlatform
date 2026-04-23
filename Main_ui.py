from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QGuiApplication, QShowEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QMdiArea,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)


class MainUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Plk Platform")
        self.resize(1100, 680)
        self._has_positioned_on_show = False

        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        self._create_actions()
        self._build_menu()
        self._build_toolbar()
        self.statusBar().showMessage("พร้อมใช้งาน")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._has_positioned_on_show:
            return

        self._has_positioned_on_show = True
        QTimer.singleShot(0, self._position_initial_window)

    def _create_actions(self) -> None:
        self.setting_action = QAction("Setting", self)
        self.setting_action.setStatusTip("ตั้งค่าการเชื่อมต่อ HIS")
        self.setting_action.triggered.connect(self.open_his_setting)

        self.buddycare_action = QAction("BuddyCare Excel", self)
        self.buddycare_action.setStatusTip("เปิดหน้าจอ BuddyCare Excel")
        self.buddycare_action.triggered.connect(self.open_buddycare_excel)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setStatusTip("ปิดโปรแกรม")
        self.exit_action.triggered.connect(self.close)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        modules_menu = self.menuBar().addMenu("Modules")

        file_menu.addAction(self.setting_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        modules_menu.addAction(self.buddycare_action)

    def _build_toolbar(self) -> None:
        self.main_toolbar = QToolBar("Main Toolbar", self)
        self.main_toolbar.setObjectName("main_toolbar")
        self.main_toolbar.setMovable(True)
        self.main_toolbar.setFloatable(False)
        self.main_toolbar.setAllowedAreas(
            Qt.ToolBarArea.TopToolBarArea
            | Qt.ToolBarArea.LeftToolBarArea
            | Qt.ToolBarArea.RightToolBarArea
        )
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.main_toolbar.setStyleSheet(
            """
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #581c87, stop:1 #7c3aed);
                border: none;
                border-bottom: 1px solid #8b5cf6;
                spacing: 10px;
                padding: 3px 10px;
            }
            QToolButton {
                background: #faf5ff;
                border: 1px solid #c4b5fd;
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: 600;
                color: #6d28d9;
            }
            QToolButton:hover {
                background: #ede9fe;
            }
            QToolButton:pressed {
                background: #ddd6fe;
            }
            """
        )
        self.setting_button = self._create_toolbar_button("⚙", "Setting", self.setting_action)
        self.buddycare_button = self._create_toolbar_button("📋", "BuddyCare", self.buddycare_action)
        self.toolbar_spacer = self._create_toolbar_spacer()

        self.main_toolbar.addWidget(self.setting_button)
        self.main_toolbar.addWidget(self.buddycare_button)
        self.main_toolbar.addWidget(self.toolbar_spacer)
        self.main_toolbar.orientationChanged.connect(self._sync_toolbar_layout)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        self._sync_toolbar_layout(self.main_toolbar.orientation())

    def _create_toolbar_button(self, emoji: str, label: str, action: QAction) -> QToolButton:
        button = QToolButton(self)
        button.setText(f"{emoji} {label}")
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setAutoRaise(False)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumSize(88, 35)
        button.setMaximumHeight(35)
        button.clicked.connect(action.trigger)
        return button

    @staticmethod
    def _create_toolbar_spacer() -> QWidget:
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return spacer

    def _sync_toolbar_layout(self, orientation: Qt.Orientation) -> None:
        is_vertical = orientation == Qt.Orientation.Vertical

        if is_vertical:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            button_size = QSize(88, 35)
        else:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            button_size = QSize(88, 35)

        for button in (self.setting_button, self.buddycare_button):
            button.setMinimumSize(button_size)
            button.setMaximumHeight(button_size.height())

    def _position_initial_window(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return

        available_geometry = screen.availableGeometry()
        frame = self.frameGeometry()
        content = self.geometry()

        left_margin = content.left() - frame.left()
        top_margin = content.top() - frame.top()
        right_margin = frame.right() - content.right()
        bottom_margin = frame.bottom() - content.bottom()

        frame_extra_width = left_margin + right_margin
        frame_extra_height = top_margin + bottom_margin

        max_content_width = max(320, available_geometry.width() - frame_extra_width)
        max_content_height = max(240, available_geometry.height() - frame_extra_height)

        target_width = min(self.width(), max_content_width)
        target_height = min(self.height(), max_content_height)
        if target_width != self.width() or target_height != self.height():
            self.resize(target_width, target_height)

        target_frame_width = target_width + frame_extra_width
        target_frame_height = target_height + frame_extra_height

        target_frame_x = available_geometry.left() + max(
            (available_geometry.width() - target_frame_width) // 2,
            0,
        )
        target_frame_y = available_geometry.top() + max(
            (available_geometry.height() - target_frame_height) // 2,
            0,
        )

        max_frame_x = available_geometry.right() - target_frame_width + 1
        max_frame_y = available_geometry.bottom() - target_frame_height + 1
        target_frame_x = min(max(target_frame_x, available_geometry.left()), max_frame_x)
        target_frame_y = min(max(target_frame_y, available_geometry.top()), max_frame_y)

        self.move(target_frame_x, target_frame_y)
