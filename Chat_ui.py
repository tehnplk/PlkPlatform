from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ChatUI(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chat")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        label = QLabel("หน้าต่างแชท (Chat Module)")
        layout.addWidget(label)
