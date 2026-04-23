from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from BuddyCareExcel_logic import BuddyCareExcelWindow
from HisSetting_dlg import DlgHisSetting
from Main_ui import MainUI


def resolve_app_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


class MainWindow(MainUI):
    def __init__(self) -> None:
        super().__init__()
        self._buddycare_subwindow = None

    def open_buddycare_excel(self) -> None:
        if self._buddycare_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._buddycare_subwindow)
            self._buddycare_subwindow.widget().show()
            self._buddycare_subwindow.showMaximized()
            return

        buddycare_widget = BuddyCareExcelWindow()
        subwindow = self.mdi_area.addSubWindow(buddycare_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("BuddyCare Excel")
        subwindow.destroyed.connect(self._clear_buddycare_reference)
        buddycare_widget.show()
        subwindow.showMaximized()
        self._buddycare_subwindow = subwindow
        self.statusBar().showMessage("เปิด BuddyCare Excel แล้ว", 3000)

    def _clear_buddycare_reference(self) -> None:
        self._buddycare_subwindow = None

    def open_his_setting(self) -> None:
        dialog = DlgHisSetting(self)
        if dialog.exec():
            self.statusBar().showMessage("บันทึกการตั้งค่า HIS แล้ว", 3000)


    def open_authen_module(self) -> None:
        self._show_pending_module("Authen")

    def open_central_data_module(self) -> None:
        self._show_pending_module("ศูนย์ข้อมูลกลาง")

    def open_ai_assistant_module(self) -> None:
        self._show_pending_module("AI Assistant")

    def open_data_quality_module(self) -> None:
        self._show_pending_module("คุณภาพข้อมูล")

    def open_revenue_storage_module(self) -> None:
        self._show_pending_module("จัดเก็บรายได้")

    def _show_pending_module(self, module_name: str) -> None:
        self.statusBar().showMessage(f"เปิดโมดูล {module_name}", 3000)
        QMessageBox.information(
            self,
            module_name,
            f"โมดูล {module_name} พร้อมสำหรับเชื่อมต่อหน้าจอถัดไป",
        )


def main() -> None:
    app = QApplication(sys.argv)
    icon_path = resolve_app_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    QTimer.singleShot(0, window.showMaximized)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
