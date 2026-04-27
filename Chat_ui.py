from PyQt6.QtCore import Qt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from Theme_helper import current_theme


class ChatUI(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("แชท")
        self.resize(800, 600)
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("ระบบปรึกษากับ Admin อำเภอ /จังหวัด")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("chat_title")

        subtitle_label = QLabel("กำลังอยู่ระหว่างการพัฒนา")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("chat_subtitle")

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {theme.window};
            }}
            QLabel#chat_title {{
                color: {theme.primary};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#chat_subtitle {{
                color: {theme.text_muted};
                font-size: 16px;
                font-style: italic;
            }}
            """
        )

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {theme.window};
            }}
            QLabel#chat_title {{
                color: {theme.primary};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#chat_subtitle {{
                color: {theme.text_muted};
                font-size: 16px;
                font-style: italic;
            }}
            """
        )
