import sys
from pathlib import Path

# Fix: QtWebEngineWidgets must be imported before a QApplication instance is created
import PyQt6.QtWebEngineWidgets

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication


def resolve_app_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    print(f"[Unhandled Exception] {exc_type.__name__}: {exc_value}", file=sys.stderr)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_uncaught_exception


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # กำหนดชื่อแอปพลิเคชัน (ส่งผลต่อชื่อหัวข้อการแจ้งเตือนบนระบบ)
    app.setApplicationName("ข้อความใหม่")
    app.setApplicationDisplayName("ข้อความใหม่")

    # กำหนด AppUserModelID บน Windows เพื่อความเข้ากันได้กับการแจ้งเตือนระบบ
    import sys
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ข้อความใหม่")
        except Exception:
            pass

    # กำหนดไอคอนหลักให้ตัวแอป
    icon_path = resolve_app_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # ป้องกันไม่ให้แอปปิดตัวเมื่อ splash screen ปิด/ซ่อน
    app.setQuitOnLastWindowClosed(False)

    # โหลดและแสดง Splash Screen ทันที (มีขนาดเล็ก โหลดเร็วมาก)
    from Splash_logic import SplashWindow

    splash = SplashWindow()
    splash.show_splash()

    # ประมวลผลอีเวนต์เพื่อให้ Splash Screen แสดงผลบนหน้าจอทันที
    app.processEvents()

    # ทำการโหลดโมดูลหลักและอินเทอร์เฟซตัวเต็ม (ซึ่งมีขนาดใหญ่และใช้เวลาโหลด)
    # หลังจากที่ Splash Screen แสดงผลแล้ว
    from Main_logic import MainWindow, apply_application_palette

    apply_application_palette(app)

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    # แสดงหน้าต่างหลักหลังปิด Splash Screen อย่างนุ่มนวล
    def on_splash_finished() -> None:
        print("Splash screen finished, showing main window...")
        window.show()
        # คืนค่ากลับเป็น True เพื่อให้แอปปิดเมื่อปิดหน้าต่างหลัก
        app.setQuitOnLastWindowClosed(True)
        QTimer.singleShot(0, window.showMaximized)
        QTimer.singleShot(500, window.on_startup_complete)
        QTimer.singleShot(1500, window.check_for_updates)

    splash.fade_out_animation.finished.connect(on_splash_finished)

    sys.exit(app.exec())
