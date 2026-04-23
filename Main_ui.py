from __future__ import annotations

from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QGuiApplication, QMouseEvent, QShowEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMdiArea,
    QMenu,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class WindowTitleBar(QWidget):
    def __init__(self, parent: QMainWindow) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            window_handle = self.window().windowHandle()
            if window_handle is not None and window_handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            parent_window = self.window()
            if isinstance(parent_window, QMainWindow):
                if parent_window.isMaximized():
                    parent_window.showNormal()
                else:
                    parent_window.showMaximized()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


class MainUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Plk Platform")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1100, 680)
        self._has_positioned_on_show = False

        self._apply_main_theme()

        self.mdi_area = QMdiArea()
        self.mdi_area.setObjectName("mdi_area")
        self.mdi_area.setBackground(QColor("#dff7ea"))
        self.setCentralWidget(self.mdi_area)

        self._create_actions()
        self._build_window_chrome()
        self._build_toolbar()

        self.statusBar().setObjectName("main_statusbar")
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("พร้อมใช้งาน")
        self._update_maximize_button()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._has_positioned_on_show:
            return

        self._has_positioned_on_show = True
        QTimer.singleShot(0, self._position_initial_window)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_maximize_button()

    def _apply_main_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #eefaf3;
                border: 1px solid #8ed1ad;
            }
            QWidget#window_chrome {
                background: transparent;
            }
            QWidget#title_bar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #b7ebcd, stop:1 #8fdcb2);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QLabel#window_title {
                color: #1f5c3f;
                font-size: 15px;
                font-weight: 700;
                padding: 0 10px;
            }
            QWidget#menu_strip {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d8f4e4, stop:1 #beeccf);
                border-bottom: 1px solid #9fdbb9;
            }
            QToolButton#menu_button {
                background: transparent;
                color: #2f6b4c;
                border: none;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 700;
            }
            QToolButton#menu_button:hover {
                background: rgba(47, 107, 76, 0.10);
            }
            QToolButton#window_control, QToolButton#close_button {
                background: rgba(255, 255, 255, 0.55);
                color: #2c6a4a;
                border: 1px solid rgba(63, 122, 84, 0.18);
                border-radius: 8px;
                font-size: 15px;
                font-weight: 800;
                padding-bottom: 1px;
            }
            QToolButton#window_control:hover {
                background: rgba(255, 255, 255, 0.80);
            }
            QToolButton#window_control:pressed {
                background: rgba(212, 242, 224, 0.95);
            }
            QToolButton#close_button:hover {
                background: #dc2626;
                color: #ffffff;
            }
            QToolButton#close_button:pressed {
                background: #b91c1c;
            }
            QMenu {
                background: #f7fdf9;
                color: #24553a;
                border: 1px solid #a7dabc;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 8px;
            }
            QMenu::item:selected {
                background: #d8f4e4;
            }
            QStatusBar#main_statusbar {
                background: #d8f4e4;
                color: #2f6b4c;
                border-top: 1px solid #9fdbb9;
                font-size: 12px;
                font-weight: 600;
            }
            QStatusBar::item {
                border: none;
            }
            QMdiArea#mdi_area {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eefaf3, stop:1 #dff7ea);
                border: none;
            }
        """
        )

    def _create_actions(self) -> None:
        self.setting_action = QAction("Setting", self)
        self.setting_action.setStatusTip("ตั้งค่าการเชื่อมต่อ HIS")
        self.setting_action.triggered.connect(self.open_his_setting)

        self.buddycare_action = QAction("BuddyCare Excel", self)
        self.buddycare_action.setStatusTip("เปิดหน้าจอ BuddyCare Excel")
        self.buddycare_action.triggered.connect(self.open_buddycare_excel)

        self.authen_action = QAction("Authen", self)
        self.authen_action.setStatusTip("เปิดโมดูล Authen")
        self.authen_action.triggered.connect(self.open_authen_module)

        self.central_data_action = QAction("ศูนย์ข้อมูลกลาง", self)
        self.central_data_action.setStatusTip("เปิดโมดูลศูนย์ข้อมูลกลาง")
        self.central_data_action.triggered.connect(self.open_central_data_module)

        self.ai_assistant_action = QAction("AI Assistant", self)
        self.ai_assistant_action.setStatusTip("เปิดโมดูล AI Assistant")
        self.ai_assistant_action.triggered.connect(self.open_ai_assistant_module)

        self.data_quality_action = QAction("คุณภาพข้อมูล", self)
        self.data_quality_action.setStatusTip("เปิดโมดูลคุณภาพข้อมูล")
        self.data_quality_action.triggered.connect(self.open_data_quality_module)

        self.revenue_storage_action = QAction("จัดเก็บรายได้", self)
        self.revenue_storage_action.setStatusTip("เปิดโมดูลจัดเก็บรายได้")
        self.revenue_storage_action.triggered.connect(self.open_revenue_storage_module)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setStatusTip("ปิดโปรแกรม")
        self.exit_action.triggered.connect(self.close)

    def _build_window_chrome(self) -> None:
        top_widget = QWidget(self)
        top_widget.setObjectName("window_chrome")
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.title_bar = WindowTitleBar(self)
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(42)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 4, 10, 4)
        title_layout.setSpacing(8)

        self.window_title_label = QLabel(self.windowTitle(), self.title_bar)
        self.window_title_label.setObjectName("window_title")
        self.window_title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        title_layout.addWidget(self.window_title_label)
        title_layout.addStretch(1)

        self.minimize_button = self._create_window_control("_", self.showMinimized)
        self.maximize_button = self._create_window_control("□", self._toggle_maximize_restore)
        self.close_button = self._create_window_control("X", self.close)
        self.close_button.setObjectName("close_button")

        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.maximize_button)
        title_layout.addWidget(self.close_button)

        menu_strip = QWidget(self)
        menu_strip.setObjectName("menu_strip")
        menu_strip.setFixedHeight(34)
        menu_layout = QHBoxLayout(menu_strip)
        menu_layout.setContentsMargins(8, 0, 8, 0)
        menu_layout.setSpacing(4)

        file_menu = QMenu(self)
        file_menu.addAction(self.setting_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        modules_menu = QMenu(self)
        modules_menu.addAction(self.buddycare_action)
        modules_menu.addAction(self.authen_action)
        modules_menu.addAction(self.central_data_action)
        modules_menu.addAction(self.ai_assistant_action)
        modules_menu.addAction(self.data_quality_action)
        modules_menu.addAction(self.revenue_storage_action)

        menu_layout.addWidget(self._create_menu_button("File", file_menu))
        menu_layout.addWidget(self._create_menu_button("Modules", modules_menu))
        menu_layout.addStretch(1)

        top_layout.addWidget(self.title_bar)
        top_layout.addWidget(menu_strip)

        self.setMenuWidget(top_widget)
        self.windowTitleChanged.connect(self.window_title_label.setText)

    def _build_toolbar(self) -> None:
        self.main_toolbar = QToolBar("Main Toolbar", self)
        self.main_toolbar.setObjectName("main_toolbar")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setFloatable(False)
        self.main_toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.main_toolbar.setStyleSheet(
            """
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c8f0d8, stop:1 #9be0bb);
                border: none;
                border-bottom: 1px solid #9fdbb9;
                spacing: 10px;
                padding: 3px 10px;
            }
            QToolButton {
                background: #ffffff;
                border: 1px solid #a7dabc;
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: 600;
                color: #2f6b4c;
            }
            QToolButton:hover {
                background: #edf9f1;
            }
            QToolButton:pressed {
                background: #d8f4e4;
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

    def _create_menu_button(self, label: str, menu: QMenu) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("menu_button")
        button.setText(label)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setMenu(menu)
        return button

    def _create_window_control(self, label: str, handler) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("window_control")
        button.setText(label)
        button.setFixedSize(34, 28)
        button.clicked.connect(handler)
        return button

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._update_maximize_button()

    def _update_maximize_button(self) -> None:
        if not hasattr(self, "maximize_button"):
            return
        self.maximize_button.setText("❐" if self.isMaximized() else "□")

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
        if orientation == Qt.Orientation.Vertical:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        else:
            self.toolbar_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        button_size = QSize(88, 35)
        for button in (
            self.setting_button,
            self.buddycare_button,
        ):
            button.setMinimumSize(button_size)
            button.setMaximumHeight(button_size.height())

    def _position_initial_window(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return

        available_geometry = screen.availableGeometry()
        target_width = min(self.width(), max(320, available_geometry.width()))
        target_height = min(self.height(), max(240, available_geometry.height()))

        if target_width != self.width() or target_height != self.height():
            self.resize(target_width, target_height)

        target_x = available_geometry.left() + max((available_geometry.width() - target_width) // 2, 0)
        target_y = available_geometry.top() + max((available_geometry.height() - target_height) // 2, 0)

        max_x = available_geometry.right() - target_width + 1
        max_y = available_geometry.bottom() - target_height + 1
        target_x = min(max(target_x, available_geometry.left()), max_x)
        target_y = min(max(target_y, available_geometry.top()), max_y)

        self.move(target_x, target_y)
