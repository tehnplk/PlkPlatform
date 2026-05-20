from urllib.parse import urlencode

from PyQt6.QtCore import QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtWebChannel import QWebChannel

from Chat_ui import ChatUI
from Setting_helper import get_settings
from version import VERSION


def build_chat_url(hoscode: str) -> str:
    query = urlencode({"hoscode": hoscode.strip(), "version": VERSION})
    return f"{ChatWindow.BASE_URL}?{query}"


class PyQtBridge(QObject):
    notification_received = pyqtSignal(str, str)

    @pyqtSlot(str, str)
    def notify(self, title: str, message: str) -> None:
        self.notification_received.emit(title, message)


class ChatWindow(ChatUI):
    BASE_URL = "https://platform.plkhealth.go.th/chat/user"
    notification_received = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._is_quitting = False
        self._setup_logic()

    def _setup_logic(self) -> None:
        # ตั้งค่า QWebChannel เพื่อสื่อสารกับ JavaScript ใน QWebEngineView
        self.web_channel = QWebChannel()
        self.bridge = PyQtBridge(self)
        self.bridge.notification_received.connect(self.notification_received.emit)
        self.web_channel.registerObject("pyqtBridge", self.bridge)
        self.web_view.page().setWebChannel(self.web_channel)

        self.reload_chat_session()

    def reload_chat_session(self) -> None:
        hoscode = self._load_hoscode()
        self.web_view.setUrl(QUrl(build_chat_url(hoscode)))

    def _load_hoscode(self) -> str:
        settings = get_settings()
        value = settings.value("hoscode", "")
        return str(value).strip() if value else ""

    def closeEvent(self, event) -> None:
        if self._is_quitting:
            super().closeEvent(event)
        else:
            event.ignore()
            self.hide()
