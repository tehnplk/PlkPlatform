from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QGuiApplication, QMouseEvent, QPixmap, QShowEvent
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

from version import RELEASE, VERSION
from Theme_helper import current_theme, rgb_csv


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
                if hasattr(parent_window, "_toggle_maximize_restore"):
                    parent_window._toggle_maximize_restore()
                    event.accept()
                    return
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
        self._normal_geometry = self.geometry()

        self._apply_main_theme()

        self.mdi_area = QMdiArea()
        self.mdi_area.setObjectName("mdi_area")
        self.mdi_area.setBackground(QColor(current_theme().mdi_end))
        self.setCentralWidget(self.mdi_area)

        self._create_actions()
        self._build_window_chrome()
        self._build_toolbar()

        self.statusBar().setObjectName("main_statusbar")
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("พร้อมใช้งาน")
        self._version_label = QLabel(f"Version {VERSION}  •  Release {RELEASE}")
        self._version_label.setStyleSheet(
            f"color: {current_theme().primary}; font-weight: 700; padding: 0 10px;"
        )
        self.statusBar().addPermanentWidget(self._version_label)
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
        theme = current_theme()
        primary_rgb = rgb_csv(theme.primary)
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {theme.window};
                border: 1px solid {theme.border};
            }}
            QWidget#window_chrome {{
                background: transparent;
            }}
            QWidget#title_bar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.title_start}, stop:1 {theme.title_end});
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QLabel#window_title {{
                color: {theme.text};
                font-size: 15px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QLabel#window_icon {{
                background: transparent;
                padding: 0;
            }}
            QWidget#menu_strip {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.surface_muted}, stop:1 {theme.primary_soft});
                border-bottom: 1px solid {theme.border};
            }}
            QToolButton#menu_button {{
                background: transparent;
                color: {theme.primary};
                border: none;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            QToolButton#menu_button:hover {{
                background: rgba({primary_rgb}, 0.16);
            }}
            QToolButton#window_control, QToolButton#close_button {{
                background: {theme.surface_alt};
                color: {theme.primary};
                border: 1px solid {theme.border};
                border-radius: 8px;
                font-size: 15px;
                font-weight: 800;
                padding-bottom: 1px;
            }}
            QToolButton#window_control:hover {{
                background: {theme.surface};
            }}
            QToolButton#window_control:pressed {{
                background: {theme.primary_soft};
            }}
            QToolButton#close_button:hover {{
                background: {theme.danger};
                color: #ffffff;
            }}
            QToolButton#close_button:pressed {{
                background: {theme.danger_pressed};
            }}
            QMenu {{
                background: {theme.surface};
                color: {theme.text};
                border: 1px solid {theme.border};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 18px;
                border-radius: 8px;
            }}
            QMenu::item:selected {{
                background: {theme.primary_soft};
            }}
            QStatusBar#main_statusbar {{
                background: {theme.surface_muted};
                color: {theme.primary};
                border-top: 1px solid {theme.border};
                font-size: 12px;
                font-weight: 600;
            }}
            QStatusBar::item {{
                border: none;
            }}
            QMdiArea#mdi_area {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme.mdi_start}, stop:1 {theme.mdi_end});
                border: none;
            }}
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

        self.central_data_ovst_action = QAction("Telemed - ส่งข้อมูลประเภทการมาด้วย OVST", self)
        self.central_data_ovst_action.setStatusTip("ส่งข้อมูลประเภทการมาด้วยแฟ้ม OVST")
        self.central_data_ovst_action.triggered.connect(self.open_central_data_module)

        self.central_data_service_action = QAction("Telemed - ส่งข้อมูลประเภทการมาด้วยแฟ้ม SERVICE", self)
        self.central_data_service_action.setStatusTip("ส่งข้อมูลประเภทการมาด้วยแฟ้ม SERVICE")
        self.central_data_service_action.triggered.connect(self.open_telemed_daily_module)

        self.buddycare_visit_action = QAction("เปิด Visit ด้วย BuddyCare Excel", self)
        self.buddycare_visit_action.setStatusTip("เปิด visit จำนวนมากด้วย BuddyCare Excel")
        self.buddycare_visit_action.triggered.connect(self.open_buddycare_excel)

        # ---- ส่งออกข้อมูล ----
        self.export_43files_action = QAction("43 Files", self)
        self.export_43files_action.setStatusTip("ส่งออกข้อมูลมาตรฐาน 43 แฟ้ม")
        self.export_43files_action.triggered.connect(self.open_f43_export_module)

        self.export_13files_plus_action = QAction("13 Files Plus (NHSO Digital Platform)", self)
        self.export_13files_plus_action.setStatusTip("ส่งออกข้อมูล 13 แฟ้ม Plus สำหรับ NHSO Digital Platform")
        self.export_13files_plus_action.triggered.connect(
            lambda: self._show_pending_module("ส่งออก 13 Files Plus (NHSO Digital Platform)")
        )

        self.ai_assistant_action = QAction("AI Assistant", self)
        self.ai_assistant_action.setStatusTip("เปิดโมดูล AI Assistant")
        self.ai_assistant_action.triggered.connect(self.open_ai_assistant_module)

        self.data_quality_action = QAction("คุณภาพข้อมูล", self)
        self.data_quality_action.setStatusTip("เปิดโมดูลคุณภาพข้อมูล")
        self.data_quality_action.triggered.connect(self.open_data_quality_module)

        self.revenue_storage_action = QAction("จัดเก็บรายได้", self)
        self.revenue_storage_action.setStatusTip("เปิดโมดูลจัดเก็บรายได้")
        self.revenue_storage_action.triggered.connect(self.open_revenue_storage_module)

        self.quick_visit_action = QAction("Quick Visit", self)
        self.quick_visit_action.setStatusTip("ค้นหาคนไข้และเปิด visit ได้เร็ว")
        self.quick_visit_action.triggered.connect(self.open_quick_visit_module)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setStatusTip("ปิดโปรแกรม")
        self.exit_action.triggered.connect(self.close)

        # ---- View / MDI management actions ----
        self.view_cascade_action = QAction("จัดเรียงซ้อน (Cascade)", self)
        self.view_cascade_action.setStatusTip("จัดเรียงหน้าต่างย่อยแบบซ้อนกัน")
        self.view_cascade_action.triggered.connect(lambda: self.mdi_area.cascadeSubWindows())

        self.view_tile_action = QAction("จัดเรียงเรียง (Tile)", self)
        self.view_tile_action.setStatusTip("จัดเรียงหน้าต่างย่อยแบบ tile")
        self.view_tile_action.triggered.connect(lambda: self.mdi_area.tileSubWindows())

        self.view_close_action = QAction("ปิดหน้าต่างปัจจุบัน", self)
        self.view_close_action.setStatusTip("ปิดหน้าต่างย่อยที่กำลังใช้งานอยู่")
        self.view_close_action.triggered.connect(lambda: self.mdi_area.closeActiveSubWindow())

        self.view_close_all_action = QAction("ปิดทุกหน้าต่าง", self)
        self.view_close_all_action.setStatusTip("ปิดหน้าต่างย่อยทั้งหมด")
        self.view_close_all_action.triggered.connect(lambda: self.mdi_area.closeAllSubWindows())

        self.view_next_action = QAction("หน้าต่างถัดไป", self)
        self.view_next_action.setShortcut("Ctrl+Tab")
        self.view_next_action.triggered.connect(lambda: self.mdi_area.activateNextSubWindow())

        self.view_prev_action = QAction("หน้าต่างก่อนหน้า", self)
        self.view_prev_action.setShortcut("Ctrl+Shift+Tab")
        self.view_prev_action.triggered.connect(lambda: self.mdi_area.activatePreviousSubWindow())

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

        self.window_icon_label = QLabel(self.title_bar)
        self.window_icon_label.setObjectName("window_icon")
        self.window_icon_label.setFixedSize(24, 24)
        self.window_icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon_path = self._resolve_app_path("icon.png")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                self.window_icon_label.setPixmap(
                    pixmap.scaled(
                        24,
                        24,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        self.window_title_label = QLabel(self.windowTitle(), self.title_bar)
        self.window_title_label.setObjectName("window_title")
        self.window_title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        title_layout.addWidget(self.window_icon_label)
        title_layout.addWidget(self.window_title_label)
        title_layout.addStretch(1)

        self.minimize_button = self._create_window_control("_", self._show_window_minimized)
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

        helpers_menu = QMenu("🛠️ ระบบช่วยงาน", modules_menu)
        helpers_menu.addAction(self.authen_action)
        helpers_menu.addAction(self.quick_visit_action)
        helpers_menu.addAction(self.data_quality_action)
        helpers_menu.addAction(self.revenue_storage_action)
        helpers_menu.addAction(self.ai_assistant_action)
        modules_menu.addMenu(helpers_menu)

        urgent_menu = QMenu("🚨 นโยบายเร่งด่วน", modules_menu)

        central_submenu = QMenu("ส่งข้อมูลเข้าระบบกลาง", urgent_menu)
        central_submenu.addAction(self.central_data_ovst_action)
        central_submenu.addAction(self.central_data_service_action)
        urgent_menu.addMenu(central_submenu)

        urgent_menu.addAction(self.buddycare_visit_action)
        modules_menu.addMenu(urgent_menu)

        export_menu = QMenu("📦 ส่งออกข้อมูล", modules_menu)
        export_menu.addAction(self.export_43files_action)
        export_menu.addAction(self.export_13files_plus_action)
        modules_menu.addMenu(export_menu)

        view_menu = QMenu(self)
        view_menu.addAction(self.view_cascade_action)
        view_menu.addAction(self.view_tile_action)
        view_menu.addSeparator()
        view_menu.addAction(self.view_next_action)
        view_menu.addAction(self.view_prev_action)
        view_menu.addSeparator()
        view_menu.addAction(self.view_close_action)
        view_menu.addAction(self.view_close_all_action)
        view_menu.addSeparator()
        self._view_windows_separator_added = True
        view_menu.aboutToShow.connect(lambda m=view_menu: self._rebuild_view_windows_list(m))
        self._view_menu = view_menu

        menu_layout.addWidget(self._create_menu_button("File", file_menu))
        menu_layout.addWidget(self._create_menu_button("Modules", modules_menu))
        menu_layout.addWidget(self._create_menu_button("View", view_menu))
        menu_layout.addStretch(1)

        top_layout.addWidget(self.title_bar)
        top_layout.addWidget(menu_strip)

        self.setMenuWidget(top_widget)
        self.windowTitleChanged.connect(self.window_title_label.setText)

    @staticmethod
    def _resolve_app_path(relative_path: str) -> Path:
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return base_path / relative_path

    def _build_toolbar(self) -> None:
        theme = current_theme()
        self.main_toolbar = QToolBar("Main Toolbar", self)
        self.main_toolbar.setObjectName("main_toolbar")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setFloatable(False)
        self.main_toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.main_toolbar.setStyleSheet(
            f"""
            QToolBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.toolbar_start}, stop:1 {theme.toolbar_end});
                border: none;
                border-bottom: 1px solid {theme.border};
                spacing: 10px;
                padding: 3px 10px;
            }}
            QToolButton {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 12px;
                font-weight: 600;
                color: {theme.primary};
            }}
            QToolButton:hover {{
                background: {theme.surface_alt};
            }}
            QToolButton:pressed {{
                background: {theme.primary_soft};
            }}
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

    def _rebuild_view_windows_list(self, menu: QMenu) -> None:
        """รีเฟรชรายการ MDI subwindow ใน View menu (ส่วนหลัง separator สุดท้าย)"""
        # ลบ action เดิมที่เป็นรายการ subwindow ออก (ทุก action หลัง separator สุดท้าย)
        actions = menu.actions()
        last_sep_idx = -1
        for i, a in enumerate(actions):
            if a.isSeparator():
                last_sep_idx = i
        if last_sep_idx >= 0:
            for a in actions[last_sep_idx + 1 :]:
                menu.removeAction(a)

        sub_windows = self.mdi_area.subWindowList()
        if not sub_windows:
            empty = QAction("(ไม่มีหน้าต่างเปิดอยู่)", menu)
            empty.setEnabled(False)
            menu.addAction(empty)
            return

        active = self.mdi_area.activeSubWindow()
        for i, sw in enumerate(sub_windows, start=1):
            title = sw.windowTitle() or f"Window {i}"
            label = f"&{i} {title}" if i < 10 else title
            act = QAction(label, menu)
            act.setCheckable(True)
            act.setChecked(sw is active)
            act.triggered.connect(lambda _checked=False, w=sw: self._activate_sub_window(w))
            menu.addAction(act)

    def _activate_sub_window(self, sw) -> None:
        if sw is None:
            return
        self.mdi_area.setActiveSubWindow(sw)
        sw.showNormal()
        sw.raise_()

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

    def _capture_normal_geometry(self) -> None:
        if not self.isMaximized() and not self.isMinimized():
            self._normal_geometry = self.geometry()

    def _show_window_minimized(self) -> None:
        self._capture_normal_geometry()
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMinimized)

    def _show_window_maximized(self) -> None:
        self._capture_normal_geometry()
        self.setWindowState(
            (self.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowMaximized
        )
        self.show()

    def _show_window_normal(self) -> None:
        self.setWindowState(
            self.windowState()
            & ~Qt.WindowState.WindowMaximized
            & ~Qt.WindowState.WindowMinimized
        )
        self.showNormal()
        if self._normal_geometry.isValid():
            self.setGeometry(self._normal_geometry)

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self._show_window_normal()
        else:
            self._show_window_maximized()
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
