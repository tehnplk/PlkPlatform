from __future__ import annotations

import sys

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtWidgets import QApplication

from BuddyCareExcel_logic import BuddyCareExcelWindow
from HisSetting_dlg import DlgHisSetting
from Main_ui import MainUI


class MainWindow(MainUI):
    def __init__(self) -> None:
        super().__init__()
        self._buddycare_subwindow = None

    def open_buddycare_excel(self) -> None:
        if self._buddycare_subwindow is not None:
            self._resize_subwindow_to_parent(self._buddycare_subwindow, scale=0.9)
            self.mdi_area.setActiveSubWindow(self._buddycare_subwindow)
            self._buddycare_subwindow.widget().show()
            return

        buddycare_widget = BuddyCareExcelWindow()
        subwindow = self.mdi_area.addSubWindow(buddycare_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("BuddyCare Excel")
        subwindow.destroyed.connect(self._clear_buddycare_reference)
        buddycare_widget.show()
        self._resize_subwindow_to_parent(subwindow, scale=0.9)
        self._buddycare_subwindow = subwindow
        self.statusBar().showMessage("เปิด BuddyCare Excel แล้ว", 3000)

    def _clear_buddycare_reference(self) -> None:
        self._buddycare_subwindow = None

    def _resize_subwindow_to_parent(self, subwindow, *, scale: float) -> None:
        viewport_size = self.mdi_area.viewport().size()
        if viewport_size.width() <= 0 or viewport_size.height() <= 0:
            return

        target_width = max(640, int(viewport_size.width() * scale))
        target_height = max(480, int(viewport_size.height() * scale))
        target_width = min(target_width, viewport_size.width())
        target_height = min(target_height, viewport_size.height())

        subwindow.resize(QSize(target_width, target_height))

        x = max((viewport_size.width() - target_width) // 2, 0)
        y = max((viewport_size.height() - target_height) // 2, 0)
        subwindow.move(QPoint(x, y))

    def open_his_setting(self) -> None:
        dialog = DlgHisSetting(self)
        if dialog.exec():
            self.statusBar().showMessage("บันทึกการตั้งค่า HIS แล้ว", 3000)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
