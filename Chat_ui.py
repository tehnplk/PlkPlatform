import os

from PyQt6.QtCore import QStandardPaths, QSize, Qt
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QVBoxLayout
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtWebEngineWidgets import QWebEngineView

from Theme_helper import current_theme


class ChatUI(QWidget):
    INITIAL_SIZE = QSize(760, 772)
    MINIMUM_SIZE = QSize(330, 480)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("แชท")
        self.setMinimumSize(self.MINIMUM_SIZE)
        self.resize(self.INITIAL_SIZE)
        self._active_downloads: list[QWebEngineDownloadRequest] = []
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView(self)
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.page().profile().downloadRequested.connect(
            self._handle_download_requested
        )
        layout.addWidget(self.web_view)

    def resizeEvent(self, event) -> None:
        size = event.size()
        print(f"[ChatWindow] resize {size.width()}x{size.height()}")
        super().resizeEvent(event)

    def _handle_download_requested(self, download: QWebEngineDownloadRequest) -> None:
        suggested_name = os.path.basename(download.suggestedFileName()) or "download"
        download_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not download_dir:
            download_dir = os.path.expanduser("~")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "บันทึกไฟล์",
            os.path.join(download_dir, suggested_name),
        )
        if not file_path:
            download.cancel()
            return

        download.setDownloadDirectory(os.path.dirname(file_path))
        download.setDownloadFileName(os.path.basename(file_path))
        download.isFinishedChanged.connect(
            lambda *args, item=download: self._handle_download_finished(item)
        )
        self._active_downloads.append(download)
        download.accept()

    def _handle_download_finished(self, download: QWebEngineDownloadRequest) -> None:
        if not download.isFinished():
            return

        if download in self._active_downloads:
            self._active_downloads.remove(download)

        if (
            download.interruptReason()
            != QWebEngineDownloadRequest.DownloadInterruptReason.NoReason
        ):
            QMessageBox.warning(
                self,
                "ดาวน์โหลดไม่สำเร็จ",
                f"ไม่สามารถดาวน์โหลดไฟล์ได้\n{download.interruptReasonString()}",
            )

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {theme.window};
            }}
            """
        )
