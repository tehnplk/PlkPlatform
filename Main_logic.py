from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from AutoUpdate_logic import AutoUpdateController, DownloadedUpdate, is_packaged_app, launch_update_installer
from BuddyCareExcel_logic import BuddyCareExcelWindow
from DataCenter_logic import DataCenterWindow
from F43Export_logic import F43ExportWindow
from HdcTelemed_logic import HdcTelemedLogic
from HisSetting_dlg import DlgHisSetting
from Main_ui import MainUI
from PatientList_logic import PatientListWindow
from QuickVisit_logic import QuickVisitWindow
from Query_logic import QueryWindow
from TelemedDaily_ui import TelemedDailyWindow
from Theme_helper import apply_application_palette
from Chat_logic import ChatWindow
from version import VERSION, RELEASE


def resolve_app_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


class MainWindow(MainUI):
    def __init__(self) -> None:
        super().__init__()
        self._buddycare_subwindow = None
        self._datacenter_subwindow = None
        self._telemed_daily_subwindow = None
        self._quick_visit_subwindow = None
        self._patient_list_subwindow = None
        self._f43_export_subwindow = None
        self._chat_subwindow = None
        self._hdc_telemed_subwindow = None
        self._query_subwindow = None
        self._auto_update = AutoUpdateController(parent=self)
        self._auto_update.update_ready.connect(self._apply_downloaded_update)
        self._auto_update.no_update.connect(self._hide_update_progress)
        self._auto_update.progress.connect(self._handle_update_progress)
        self._auto_update.failed.connect(self._handle_update_error)

        # ตรวจอัปเดตทุก 1 ชั่วโมง (เพิ่มเติมจากตอนเปิดโปรแกรม)
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(60 * 60 * 1000)  # 1 ชั่วโมง
        self._update_timer.timeout.connect(self.check_for_updates)
        self._update_timer.start()

    def open_buddycare_excel(self) -> None:
        if self._buddycare_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._buddycare_subwindow)
            self._buddycare_subwindow.widget().show()
            self._buddycare_subwindow.showMaximized()
            return

        buddycare_widget = BuddyCareExcelWindow()
        subwindow = self.mdi_area.addSubWindow(buddycare_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("BuddyCare Excel - BuddyCareExcel")
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
        if self._datacenter_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._datacenter_subwindow)
            self._datacenter_subwindow.widget().show()
            self._datacenter_subwindow.showMaximized()
            return

        datacenter_widget = DataCenterWindow()
        subwindow = self.mdi_area.addSubWindow(datacenter_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("ศูนย์ข้อมูลกลาง - DataCenter")
        subwindow.destroyed.connect(self._clear_datacenter_reference)
        datacenter_widget.show()
        subwindow.showMaximized()
        self._datacenter_subwindow = subwindow
        self.statusBar().showMessage("เปิดศูนย์ข้อมูลกลางแล้ว", 3000)

    def _clear_datacenter_reference(self) -> None:
        self._datacenter_subwindow = None

    def open_ai_assistant_module(self) -> None:
        self._show_pending_module("AI Assistant")

    def open_data_quality_module(self) -> None:
        self._show_pending_module("คุณภาพข้อมูล")

    def open_revenue_storage_module(self) -> None:
        self._show_pending_module("จัดเก็บรายได้")

    def open_telemed_daily_module(self) -> None:
        if self._telemed_daily_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._telemed_daily_subwindow)
            self._telemed_daily_subwindow.widget().show()
            self._telemed_daily_subwindow.showMaximized()
            return

        telemed_widget = TelemedDailyWindow()
        subwindow = self.mdi_area.addSubWindow(telemed_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("อัพเดท Telemed Daily - TelemedDaily")
        subwindow.destroyed.connect(self._clear_telemed_daily_reference)
        telemed_widget.show()
        subwindow.showMaximized()
        self._telemed_daily_subwindow = subwindow
        self.statusBar().showMessage("เปิดอัพเดทTelemed Daily แล้ว", 3000)

    def _clear_telemed_daily_reference(self) -> None:
        self._telemed_daily_subwindow = None

    def open_quick_visit_module(self) -> None:
        if self._quick_visit_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._quick_visit_subwindow)
            self._quick_visit_subwindow.widget().show()
            self._quick_visit_subwindow.showMaximized()
            return

        quick_visit_widget = QuickVisitWindow()
        subwindow = self.mdi_area.addSubWindow(quick_visit_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("Quick Visit - QuickVisit")
        subwindow.destroyed.connect(self._clear_quick_visit_reference)
        quick_visit_widget.show()
        subwindow.showMaximized()
        self._quick_visit_subwindow = subwindow
        self.statusBar().showMessage("เปิด Quick Visit แล้ว", 3000)

    def _clear_quick_visit_reference(self) -> None:
        self._quick_visit_subwindow = None

    def open_patient_list_module(self) -> None:
        if self._patient_list_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._patient_list_subwindow)
            self._patient_list_subwindow.widget().show()
            self._patient_list_subwindow.showMaximized()
            return

        patient_list_widget = PatientListWindow()
        subwindow = self.mdi_area.addSubWindow(patient_list_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("Patient List - PatientList")
        subwindow.destroyed.connect(self._clear_patient_list_reference)
        patient_list_widget.show()
        subwindow.showMaximized()
        self._patient_list_subwindow = subwindow
        self.statusBar().showMessage("เปิด Patient List แล้ว", 3000)

    def _clear_patient_list_reference(self) -> None:
        self._patient_list_subwindow = None

    def open_query_module(self) -> None:
        if self._query_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._query_subwindow)
            self._query_subwindow.widget().show()
            self._query_subwindow.showMaximized()
            return

        query_widget = QueryWindow()
        subwindow = self.mdi_area.addSubWindow(query_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("Query - Query")
        subwindow.destroyed.connect(self._clear_query_reference)
        query_widget.show()
        subwindow.showMaximized()
        self._query_subwindow = subwindow
        self.statusBar().showMessage("เปิด Query แล้ว", 3000)

    def _clear_query_reference(self) -> None:
        self._query_subwindow = None

    def open_f43_export_module(self) -> None:
        if self._f43_export_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._f43_export_subwindow)
            self._f43_export_subwindow.widget().show()
            self._f43_export_subwindow.showMaximized()
            return

        widget = F43ExportWindow()
        subwindow = self.mdi_area.addSubWindow(widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("ส่งออก 43 แฟ้ม - F43Export")
        subwindow.destroyed.connect(self._clear_f43_export_reference)
        widget.show()
        subwindow.showMaximized()
        self._f43_export_subwindow = subwindow
        self.statusBar().showMessage("เปิดโมดูลส่งออก 43 แฟ้มแล้ว", 3000)

    def _clear_f43_export_reference(self) -> None:
        self._f43_export_subwindow = None

    def open_chat_module(self) -> None:
        if self._chat_subwindow is not None:
            self._chat_subwindow.show()
            self._chat_subwindow.raise_()
            self._chat_subwindow.activateWindow()
            return

        chat_window = ChatWindow()
        chat_window.setWindowFlag(Qt.WindowType.Window, True)
        chat_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        chat_window.setWindowTitle("แชท - Chat")
        chat_window.destroyed.connect(self._clear_chat_reference)

        screen = self.screen() or QApplication.primaryScreen()
        avail = screen.availableGeometry()
        parent_geom = self.geometry()
        chat_w = parent_geom.width() // 3 + 40
        chat_h = int(avail.height() * 0.8) + 40
        chat_x = avail.x() + avail.width() - chat_w - 3
        chat_y = avail.y() + avail.height() - chat_h
        chat_window.setGeometry(chat_x, chat_y, chat_w, chat_h)

        chat_window.show()
        self._chat_subwindow = chat_window
        self.statusBar().showMessage("เปิดโมดูลแชทแล้ว", 3000)

    def _clear_chat_reference(self) -> None:
        self._chat_subwindow = None

    def closeEvent(self, event) -> None:
        if self._chat_subwindow is not None:
            self._chat_subwindow.close()
        super().closeEvent(event)

    def open_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "เกี่ยวกับ PlkPlatform",
            (
                f"<h3>PlkPlatform</h3>"
                f"<p>ระบบ Utility จัดการ HIS</p>"
                f"<p><b>เวอร์ชัน:</b> {VERSION}<br>"
                f"<b>วันที่เผยแพร่:</b> {RELEASE}</p>"
                f"<p>สำนักงานสาธารณสุขจังหวัดพิษณุโลก</p>"
            ),
        )

    def open_hdc_telemed_module(self) -> None:
        if self._hdc_telemed_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._hdc_telemed_subwindow)
            self._hdc_telemed_subwindow.widget().show()
            self._hdc_telemed_subwindow.showMaximized()
            return

        hdc_widget = HdcTelemedLogic()
        subwindow = self.mdi_area.addSubWindow(hdc_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("ผลงานใน HDC ปัจจุบัน - HdcTelemed")
        subwindow.destroyed.connect(self._clear_hdc_telemed_reference)
        hdc_widget.show()
        subwindow.showMaximized()
        self._hdc_telemed_subwindow = subwindow
        self.statusBar().showMessage("เปิดผลงานใน HDC ปัจจุบันแล้ว", 3000)

    def _clear_hdc_telemed_reference(self) -> None:
        self._hdc_telemed_subwindow = None

    def open_hdc_telemed_module(self) -> None:
        if self._hdc_telemed_subwindow is not None:
            self.mdi_area.setActiveSubWindow(self._hdc_telemed_subwindow)
            self._hdc_telemed_subwindow.widget().show()
            self._hdc_telemed_subwindow.showMaximized()
            return

        hdc_widget = HdcTelemedLogic()
        subwindow = self.mdi_area.addSubWindow(hdc_widget)
        subwindow.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        subwindow.setWindowTitle("ผลงานใน HDC ปัจจุบัน - HdcTelemed")
        subwindow.destroyed.connect(self._clear_hdc_telemed_reference)
        hdc_widget.show()
        subwindow.showMaximized()
        self._hdc_telemed_subwindow = subwindow
        self.statusBar().showMessage("เปิดผลงานใน HDC ปัจจุบันแล้ว", 3000)

    def _clear_hdc_telemed_reference(self) -> None:
        self._hdc_telemed_subwindow = None

    def _show_pending_module(self, module_name: str) -> None:
        self.statusBar().showMessage(f"เปิดโมดูล {module_name}", 3000)
        QMessageBox.information(
            self,
            module_name,
            f"โมดูล {module_name} พร้อมสำหรับเชื่อมต่อหน้าจอถัดไป",
        )

    def check_for_updates(self) -> None:
        self.statusBar().showMessage("Checking for updates...", 3000)
        self._auto_update.check_in_background()

    def _handle_update_progress(self, value: int, message: str) -> None:
        self.statusBar().clearMessage()
        self.update_progress_label.setText(message)
        self.update_progress_label.setVisible(True)

        if value < 0:
            self.update_progress_bar.setRange(0, 0)
            self.update_progress_bar.setFormat("")
        else:
            self.update_progress_bar.setRange(0, 100)
            self.update_progress_bar.setValue(value)
            self.update_progress_bar.setFormat(f"{value}%")

        self.update_progress_bar.setVisible(True)

    def _hide_update_progress(self) -> None:
        self.update_progress_label.setVisible(False)
        self.update_progress_label.setText("กำลังดาวน์โหลดเวอร์ชันใหม่...")
        self.update_progress_bar.setVisible(False)
        self.update_progress_bar.setRange(0, 100)
        self.update_progress_bar.setValue(0)
        self.update_progress_bar.setFormat("%p%")

    def _apply_downloaded_update(self, downloaded_update: DownloadedUpdate) -> None:
        self._hide_update_progress()
        if not is_packaged_app():
            self.statusBar().showMessage(
                f"Downloaded version {downloaded_update.info.version}. Installer skipped in dev mode.",
                5000,
            )
            return

        version = downloaded_update.info.version
        notes = downloaded_update.info.notes
        detail = f"\n\n{notes}" if notes else ""
        message_box = QMessageBox(
            QMessageBox.Icon.Information,
            "มีเวอร์ชันใหม่พร้อมติดตั้ง",
            (
                f"ดาวน์โหลด Plk Platform เวอร์ชัน {version} เรียบร้อยแล้ว{detail}\n\n"
                "กด OK เพื่อปิดโปรแกรมและติดตั้งเวอร์ชันใหม่\n"
                "เมื่อเปิดโปรแกรมอีกครั้งจะเป็นเวอร์ชันใหม่"
            ),
            QMessageBox.StandardButton.Ok,
            self,
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        message_box.exec()

        if not launch_update_installer(downloaded_update.staged_path):
            self.statusBar().showMessage("ไม่สามารถเริ่มตัวติดตั้งได้", 5000)
            return

        self.statusBar().showMessage(
            f"กำลังปิดโปรแกรมเพื่อติดตั้งเวอร์ชัน {version}...",
            5000,
        )
        QApplication.instance().quit()

    def _handle_update_error(self, message: str) -> None:
        self._hide_update_progress()
        self.statusBar().showMessage(f"Update check failed: {message}", 5000)


def main() -> None:
    app = QApplication(sys.argv)
    apply_application_palette(app)
    icon_path = resolve_app_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    QTimer.singleShot(0, window.showMaximized)
    QTimer.singleShot(1500, window.check_for_updates)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
