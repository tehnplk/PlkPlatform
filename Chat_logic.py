from urllib.parse import urlencode

from PyQt6.QtCore import QUrl

from Chat_ui import ChatUI
from Setting_helper import get_settings


class ChatWindow(ChatUI):
    BASE_URL = "https://platform.plkhealth.go.th/chat/user"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_logic()

    def _setup_logic(self) -> None:
        hoscode = self._load_hoscode()
        url = f"{self.BASE_URL}?{urlencode({'hoscode': hoscode})}"
        self.web_view.setUrl(QUrl(url))

    def _load_hoscode(self) -> str:
        settings = get_settings()
        value = settings.value("hoscode", "")
        return str(value).strip() if value else ""
