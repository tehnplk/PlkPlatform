from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

from Theme_helper import current_theme


class ChatUI(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("แชท")
        self.resize(1200, 800)
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {theme.window};
            }}
            """
        )
