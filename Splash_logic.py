from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QApplication

from Splash_ui import SplashUI


class SplashWindow(SplashUI):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowOpacity(0.0)

        # Setup fade-in animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(400)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Setup fade-out animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(400)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Setup progress simulation timer
        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.setInterval(20)  # Update progress every 20ms (~2 seconds total)
        self.timer.timeout.connect(self._update_progress_simulation)

    def show_splash(self) -> None:
        print("Showing splash screen...")
        self.show()
        # Position in the center of the primary screen
        self.center_on_screen()
        self.fade_in_animation.start()
        self.timer.start()

    def center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = (geom.width() - self.width()) // 2
            y = (geom.height() - self.height()) // 2
            self.move(x, y)

    def _update_progress_simulation(self) -> None:
        self.progress_value += 1
        if self.progress_value > 100:
            self.progress_value = 100
            self.timer.stop()
            self.finish_loading()
            return

        self.progress_bar.setValue(self.progress_value)

        # Dynamic loading messages based on progress
        if self.progress_value < 15:
            self.status_label.setText("กำลังเตรียมระบบข้อมูลหลัก...")
        elif self.progress_value < 35:
            self.status_label.setText("กำลังโหลดการตั้งค่าระบบ...")
        elif self.progress_value < 60:
            self.status_label.setText("กำลังตรวจสอบข้อมูลความปลอดภัยและการเชื่อมต่อ...")
        elif self.progress_value < 85:
            self.status_label.setText("กำลังจัดเตรียมโมดูลหลักและอินเทอร์เฟซผู้ใช้...")
        elif self.progress_value < 98:
            self.status_label.setText("เสร็จสิ้นการดาวน์โหลดข้อมูล...")
        else:
            self.status_label.setText("พร้อมเข้าใช้งานโปรแกรม")

    def finish_loading(self) -> None:
        print("Splash screen loading finished. Starting fade out...")
        # Fade out and close
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()
