from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication


@dataclass(frozen=True)
class AppTheme:
    is_dark: bool
    window: str
    surface: str
    surface_alt: str
    surface_muted: str
    text: str
    text_muted: str
    border: str
    grid: str
    primary: str
    primary_hover: str
    primary_pressed: str
    primary_soft: str
    primary_text: str
    accent: str
    accent_hover: str
    accent_pressed: str
    danger: str
    danger_hover: str
    danger_pressed: str
    warning: str
    warning_hover: str
    warning_pressed: str
    disabled: str
    disabled_text: str
    selection: str
    selection_text: str
    toolbar_start: str
    toolbar_end: str
    title_start: str
    title_end: str
    mdi_start: str
    mdi_end: str


def is_windows_dark_theme() -> bool:
    """Return True when Qt reports a dark system palette or color scheme."""
    app = QGuiApplication.instance()
    if app is None:
        return False

    try:
        if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            return True
    except AttributeError:
        pass

    color = app.palette().color(QPalette.ColorRole.Window)
    return color.lightness() < 128


def current_theme() -> AppTheme:
    if is_windows_dark_theme():
        return AppTheme(
            is_dark=True,
            window="#101815",
            surface="#17231e",
            surface_alt="#1d2c26",
            surface_muted="#22352d",
            text="#e9f4ef",
            text_muted="#a9c2b6",
            border="#355145",
            grid="#2a4037",
            primary="#56b981",
            primary_hover="#67c892",
            primary_pressed="#3f9d69",
            primary_soft="#213b2e",
            primary_text="#07130d",
            accent="#6aa7ff",
            accent_hover="#83b8ff",
            accent_pressed="#4f8ce6",
            danger="#ef6a6a",
            danger_hover="#f37f7f",
            danger_pressed="#d75151",
            warning="#d99a35",
            warning_hover="#e3ad55",
            warning_pressed="#b87d24",
            disabled="#3b4a44",
            disabled_text="#7f958b",
            selection="#3f9d69",
            selection_text="#ffffff",
            toolbar_start="#182820",
            toolbar_end="#244536",
            title_start="#1c3c2d",
            title_end="#2f6f4b",
            mdi_start="#101815",
            mdi_end="#15271f",
        )

    return AppTheme(
        is_dark=False,
        window="#eefaf3",
        surface="#ffffff",
        surface_alt="#f3fbf6",
        surface_muted="#d8f4e4",
        text="#0f172a",
        text_muted="#4b6358",
        border="#a7dabc",
        grid="#cfe8d9",
        primary="#2f6b4c",
        primary_hover="#3b8a61",
        primary_pressed="#255a3f",
        primary_soft="#d8f4e4",
        primary_text="#ffffff",
        accent="#2563eb",
        accent_hover="#1d4ed8",
        accent_pressed="#1e40af",
        danger="#dc2626",
        danger_hover="#b91c1c",
        danger_pressed="#991b1b",
        warning="#b45309",
        warning_hover="#d97706",
        warning_pressed="#92400e",
        disabled="#9eb7ac",
        disabled_text="#eef2ef",
        selection="#bfe6cf",
        selection_text="#1f5c3f",
        toolbar_start="#c8f0d8",
        toolbar_end="#9be0bb",
        title_start="#b7ebcd",
        title_end="#8fdcb2",
        mdi_start="#eefaf3",
        mdi_end="#dff7ea",
    )


def rgb_csv(hex_color: str) -> str:
    text = hex_color.lstrip("#")
    return ", ".join(str(int(text[i : i + 2], 16)) for i in (0, 2, 4))


def button_style(role: str = "primary") -> str:
    theme = current_theme()
    if role == "danger":
        bg, hover, pressed = theme.danger, theme.danger_hover, theme.danger_pressed
        text = "#ffffff"
    elif role == "warning":
        bg, hover, pressed = theme.warning, theme.warning_hover, theme.warning_pressed
        text = "#ffffff"
    elif role == "accent":
        bg, hover, pressed = theme.accent, theme.accent_hover, theme.accent_pressed
        text = "#ffffff"
    else:
        bg, hover, pressed = theme.primary, theme.primary_hover, theme.primary_pressed
        text = theme.primary_text

    return f"""
        QPushButton {{
            background: {bg};
            color: {text};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {hover}; }}
        QPushButton:pressed {{ background: {pressed}; }}
        QPushButton:disabled {{
            background: {theme.disabled};
            color: {theme.disabled_text};
        }}
    """


def message_box_style(role: str = "primary") -> str:
    theme = current_theme()
    bg = theme.danger if role == "danger" else theme.primary
    return f"""
        QMessageBox {{ background-color: {bg}; }}
        QLabel {{ color: #ffffff; }}
        QPushButton {{
            background: rgba(255, 255, 255, 0.18);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{ background: rgba(255, 255, 255, 0.28); }}
    """


def apply_application_palette(app: QApplication) -> None:
    """Let native controls inherit the system palette unless local styles override them."""
    app.setStyle("Fusion")
