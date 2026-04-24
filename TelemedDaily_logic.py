from __future__ import annotations

from TelemedDaily_ui import TelemedDailyWindow


class TelemedDailyController:
    """Controller สำหรับโมดูล อัพเดทTelemed Daily"""

    def __init__(self) -> None:
        self.window: TelemedDailyWindow | None = None

    def create_window(self) -> TelemedDailyWindow:
        """สร้างและส่งกลับ TelemedDaily window"""
        if self.window is None:
            self.window = TelemedDailyWindow()
        return self.window

    def process_service_data(self, service_content: str) -> list[dict]:
        """ประมวลผลข้อมูล SERVICE.txt และส่งกลับข้อมูลสำหรับ API"""
        if self.window:
            return self.window._count_visit_types()
        return []

    def send_to_province_api(self, visit_counts: list[dict]) -> bool:
        """ส่งข้อมูลไปยัง API จังหวัด"""
        if self.window:
            try:
                self.window._send_to_api(visit_counts)
                return True
            except Exception:
                return False
        return False
