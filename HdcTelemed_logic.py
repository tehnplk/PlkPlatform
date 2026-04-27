from __future__ import annotations

import json
import ssl
from urllib import error as urlerror
from urllib import request as urlrequest

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from HdcTelemed_ui import HdcTelemedWindow
from Setting_helper import get_settings


HDC_API_URL = "https://opendata.moph.go.th/api/report_data"


class _HdcTelemedWorker(QObject):
    """Worker สำหรับดึงข้อมูลผลงาน Telemedicine จาก HDC Open Data"""

    finished = pyqtSignal(list, list, str)
    failed = pyqtSignal(str)

    def __init__(self, year: str, hoscode: str) -> None:
        super().__init__()
        self.year = year
        self.hoscode = hoscode

    def run(self) -> None:
        try:
            payload = json.dumps({
                "tableName": "s_telemed_hosp",
                "year": self.year,
                "province": "65",
                "type": "json"
            }).encode("utf-8")

            req = urlrequest.Request(
                HDC_API_URL,
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )

            ssl_context = ssl._create_unverified_context()

            with urlrequest.urlopen(req, timeout=30, context=ssl_context) as resp:
                raw = resp.read().decode("utf-8", errors="replace")

            data = json.loads(raw)

            if not isinstance(data, list):
                self.failed.emit("ข้อมูลจาก HDC ไม่ถูกต้อง")
                return

            if not data:
                self.finished.emit([], [], "HDC ไม่มีข้อมูลสำหรับปีงบประมาณนี้")
                return

            # Map เฉพาะคอลัมน์ที่ต้องการ
            col_map = {
                "hospcode": "hospcode(รหัส)",
                "date_com": "datecom(วันประมวลผล)",
                "result": "result(ยอดสะสม)",
            }
            columns = list(col_map.values())
            rows = []
            for item in data:
                hospcode = str(item.get("hospcode", "")).strip()
                if self.hoscode and hospcode != self.hoscode:
                    continue
                rows.append([str(item.get(k, "")) for k in col_map.keys()])

            if self.hoscode and not rows:
                rows.append([self.hoscode, "—", "ไม่มีข้อมูลใน HDC"])

            info = f"ข้อมูล {len(rows)} แถว"
            if not self.hoscode:
                info += " (แสดงทุกหน่วยบริการ — ยังไม่มี hoscode ใน Setting)"

            self.finished.emit(columns, rows, info)

        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            self.failed.emit(f"HDC API ตอบกลับ HTTP {exc.code}: {body}")
        except urlerror.URLError as exc:
            self.failed.emit(f"เชื่อมต่อ HDC ไม่สำเร็จ: {exc.reason}")
        except json.JSONDecodeError:
            self.failed.emit("ข้อมูลจาก HDC ไม่ถูกต้อง")
        except Exception as e:
            self.failed.emit(f"เกิดข้อผิดพลาด: {e}")


class HdcTelemedLogic(HdcTelemedWindow):
    """Controller สำหรับโมดูลผลงานใน HDC ปัจจุบัน"""

    def __init__(self) -> None:
        super().__init__()
        self.on_refresh()

    def on_refresh(self) -> None:
        super().on_refresh()

        settings = get_settings()
        hoscode = settings.value("hoscode", "")
        hoscode = str(hoscode).strip() if hoscode else ""

        self._update_hoscode_label(hoscode)

        self.thread = QThread()
        self.worker = _HdcTelemedWorker(self.selected_year, hoscode)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_load_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self._on_load_failed)
        self.worker.failed.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _update_hoscode_label(self, hoscode: str) -> None:
        if hoscode:
            self.hoscode_label.setText(f"หน่วยบริการ: {hoscode}")
        else:
            self.hoscode_label.setText("หน่วยบริการ: ยังไม่ได้ตั้งค่า (ไปที่ File → Setting)")

    def _on_load_finished(self, columns: list[str], rows: list[list[str]], info: str) -> None:
        self.model.clear()
        if columns and rows:
            self.load_data(columns, rows)
        self.status_label.setText(info)
        self.statusBar().showMessage(info, 5000)
        self.refresh_button.setEnabled(True)
        self.thread.quit()

    def _on_load_failed(self, message: str) -> None:
        self.status_label.setText("เกิดข้อผิดพลาด")
        self.statusBar().showMessage(message, 5000)
        self.refresh_button.setEnabled(True)
        self.thread.quit()
