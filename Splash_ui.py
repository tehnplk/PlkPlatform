from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

from Theme_helper import current_theme
from version import VERSION


class SplashUI(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(520, 320)

        # Main background container with rounded corners and border
        self.container = QFrame(self)
        self.container.setObjectName("splash_container")
        self.container.setGeometry(10, 10, 500, 300)  # Give padding for drop shadow

        # Setup drop shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(Qt.GlobalColor.black)
        self.shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(self.shadow)

        # Layout inside container
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(0)

        # Top section: Logo + App Name + Subtitle
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.logo_label.setObjectName("splash_logo")
        icon_path = self._resolve_app_path("icon.png")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                self.logo_label.setPixmap(
                    pixmap.scaled(
                        80,
                        80,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        header_layout.addWidget(self.logo_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.title_label = QLabel("PlkPlatform")
        self.title_label.setObjectName("splash_title")

        self.subtitle_label = QLabel("ระบบ Utility จัดการ HIS")
        self.subtitle_label.setObjectName("splash_subtitle")

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch(1)

        layout.addLayout(header_layout)
        layout.addStretch(1)

        # Middle section: Status & Progress
        self.status_label = QLabel("กำลังเริ่มระบบ...")
        self.status_label.setObjectName("splash_status")

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("splash_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)

        layout.addWidget(self.status_label)
        layout.addSpacing(8)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)

        # Footer section: Credit and Version
        footer_layout = QHBoxLayout()
        self.credit_label = QLabel("สำนักงานสาธารณสุขจังหวัดพิษณุโลก")
        self.credit_label.setObjectName("splash_credit")

        self.version_label = QLabel(f"เวอร์ชัน {VERSION}")
        self.version_label.setObjectName("splash_version")

        footer_layout.addWidget(self.credit_label)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.version_label)
        layout.addLayout(footer_layout)

        self._apply_splash_theme()

    def _apply_splash_theme(self) -> None:
        theme = current_theme()
        # Custom stylesheet for the splash screen matching the main theme
        self.setStyleSheet(
            f"""
            QFrame#splash_container {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme.surface}, stop:1 {theme.window});
                border: 1px solid {theme.border};
                border-radius: 16px;
            }}
            QLabel#splash_title {{
                color: {theme.primary};
                font-family: "Segoe UI", "Tahoma", "Sarabun", sans-serif;
                font-size: 32px;
                font-weight: 800;
                background: transparent;
            }}
            QLabel#splash_subtitle {{
                color: {theme.text_muted};
                font-family: "Segoe UI", "Tahoma", "Sarabun", sans-serif;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
            QLabel#splash_status {{
                color: {theme.text};
                font-family: "Segoe UI", "Tahoma", "Sarabun", sans-serif;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }}
            QProgressBar#splash_progress {{
                background: {theme.surface_alt};
                border: 1px solid {theme.border};
                border-radius: 3px;
            }}
            QProgressBar#splash_progress::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.primary}, stop:1 {theme.primary_hover});
                border-radius: 2px;
            }}
            QLabel#splash_credit, QLabel#splash_version {{
                color: {theme.text_muted};
                font-family: "Segoe UI", "Tahoma", "Sarabun", sans-serif;
                font-size: 11px;
                font-weight: 500;
                background: transparent;
            }}
            """
        )

    @staticmethod
    def _resolve_app_path(relative_path: str) -> Path:
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return base_path / relative_path
