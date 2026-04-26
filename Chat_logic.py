from PyQt6.QtWidgets import QWidget
from Chat_ui import ChatUI

class ChatWindow(ChatUI):
    def __init__(self) -> None:
        super().__init__()
        self._setup_logic()

    def _setup_logic(self) -> None:
        # Business logic for Chat module goes here
        pass
