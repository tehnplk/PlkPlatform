from __future__ import annotations

import io
import re
import sqlite3
import traceback
import zipfile
from datetime import date, datetime
from pathlib import Path

import pymysql
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from F43Export_lib import QUERIES
from F43Export_lib_zip import QUERIES_ZIP
from F43Export_ui import F43ExportUI
from Setting_helper import load_db_settings

F43_DB_PATH = Path(__file__).parent / "F43.db"


def _open_his_connection() -> pymysql.connections.Connection:
    """เปิด connection ไป HIS database ตามที่ตั้งค่าไว้ใน Settings (เช่น hos_07547)"""
    s = load_db_settings()
    return pymysql.connect(
        host=str(s["host"]) or "localhost",
        port=int(s["port"]),
        user=str(s["user"]),
        password=str(s["password"]),
        database=str(s["database"]),
        charset=str(s["charset"]) or "utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
    )


def _format_value(value) -> str:
    if value is None:
        return ""
    text = str(value)
    return text.replace("|", " ").replace("\r", " ").replace("\n", " ")


def _to_iso_date(yyyymmdd: str) -> str:
    """'20260425' → '2026-04-25' ใช้กับ DATE column ใน MySQL"""
    if len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
        return yyyymmdd
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


class _ExportWorker(QObject):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(int, int)
    failed = pyqtSignal(str)

    def __init__(
        self,
        files: list[str],
        date_from: str,
        date_to: str,
        output_dir: Path,
        ovstist: str = "",
        export_all_persons: bool = False,
        source: str = "his",
    ) -> None:
        super().__init__()
        self.files = files
        self.date_from = date_from   # YYYYMMDD
        self.date_to = date_to       # YYYYMMDD
        self.output_dir = output_dir
        self.ovstist = ovstist
        self.export_all_persons = export_all_persons
        self.source = source         # "his" หรือ "zip"
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        if self.source == "zip":
            self._run_from_sqlite()
            return
        try:
            conn = _open_his_connection()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.failed.emit(f"เชื่อมต่อ HIS database ไม่สำเร็จ: {exc}")
            return

        try:
            hospcode = self._lookup_hospcode(conn) or "00000"
        except Exception:  # noqa: BLE001
            hospcode = "00000"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        bundle_name = f"F43_{hospcode}_{timestamp}"
        zip_path = self.output_dir / f"{bundle_name}.zip"

        success = 0
        failed = 0
        try:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for i, file_name in enumerate(self.files):
                    if self._cancel:
                        self.log.emit("ยกเลิกการส่งออก")
                        break

                    self.progress.emit(i, len(self.files), f"กำลังส่งออก {file_name}...")
                    try:
                        rows_written = self._export_one(conn, file_name, zf, bundle_name)
                        self.log.emit(f"  ✓ {file_name}.TXT — {rows_written} แถว")
                        success += 1
                    except Exception as exc:  # noqa: BLE001
                        traceback.print_exc()
                        self.log.emit(f"  ✗ {file_name}: {exc}")
                        failed += 1

            self.progress.emit(len(self.files), len(self.files), "เสร็จสิ้น")
            if success > 0:
                self.log.emit(f"\nบรรจุลง zip: {zip_path}")
            else:
                try:
                    zip_path.unlink(missing_ok=True)
                except OSError:
                    pass
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
            self.finished.emit(success, failed)

    def _run_from_sqlite(self) -> None:
        """ส่งออก ZIP โดยอ่านจาก F43.db (ที่ import มาจาก ZIP ก่อนหน้า)"""
        if not F43_DB_PATH.exists():
            self.failed.emit(f"ไม่พบ {F43_DB_PATH.name} — โปรดนำเข้า ZIP ผ่าน dialog ก่อน")
            return

        # ดึง hospcode จากแถวแรกของ PERSON ใน F43.db (col=hospcode); ไม่งั้นใช้ '00000'
        hospcode = "00000"
        sconn = sqlite3.connect(F43_DB_PATH)
        try:
            try:
                row = sconn.execute('SELECT hospcode FROM "PERSON" LIMIT 1').fetchone()
                if row and row[0]:
                    hospcode = str(row[0]).strip()
            except sqlite3.Error:
                pass

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            bundle_name = f"F43_{hospcode}_{timestamp}"
            zip_path = self.output_dir / f"{bundle_name}.zip"

            success = 0
            failed = 0
            try:
                with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for i, file_name in enumerate(self.files):
                        if self._cancel:
                            self.log.emit("ยกเลิกการส่งออก")
                            break
                        self.progress.emit(i, len(self.files), f"กำลังส่งออก {file_name}...")
                        try:
                            n = self._export_one_sqlite(sconn, file_name, zf, bundle_name)
                            self.log.emit(f"  ✓ {file_name}.TXT — {n} แถว")
                            success += 1
                        except Exception as exc:  # noqa: BLE001
                            traceback.print_exc()
                            self.log.emit(f"  ✗ {file_name}: {exc}")
                            failed += 1
                self.progress.emit(len(self.files), len(self.files), "เสร็จสิ้น")
                if success > 0:
                    self.log.emit(f"\nบรรจุลง zip: {zip_path}")
                else:
                    try:
                        zip_path.unlink(missing_ok=True)
                    except OSError:
                        pass
            finally:
                self.finished.emit(success, failed)
        finally:
            sconn.close()

    def _export_one_sqlite(self, conn: sqlite3.Connection, file_name: str, zf: zipfile.ZipFile, bundle_name: str) -> int:
        key = file_name.upper()
        if key not in QUERIES_ZIP:
            raise RuntimeError(f"ยังไม่มี mapping (zip) สำหรับแฟ้ม {key}")

        columns, sql = QUERIES_ZIP[key]
        ph_count = sql.count("?")
        # 4 placeholders ต่อ block: (date_from, date_to, ovstist, ovstist)
        params = (self.date_from, self.date_to, self.ovstist, self.ovstist)
        if ph_count % len(params) != 0:
            raise RuntimeError(f"จำนวน placeholder ของ {key} (zip) ไม่ถูกต้อง: {ph_count}")

        rows = conn.execute(sql, params * (ph_count // len(params))).fetchall()

        buffer = io.StringIO()
        buffer.write("|".join(c.upper() for c in columns) + "\n")
        for row in rows:
            buffer.write("|".join("" if v is None else str(v) for v in row) + "\n")
        zf.writestr(f"{bundle_name}/{key}.TXT", buffer.getvalue())
        return len(rows)

    def _lookup_hospcode(self, conn) -> str:
        """ดึง hospcode จาก opdconfig.hospitalcode"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT hospitalcode FROM opdconfig "
                "WHERE hospitalcode IS NOT NULL AND hospitalcode <> '' LIMIT 1"
            )
            row = cursor.fetchone()
            return str(row[0]).strip() if row and row[0] else ""

    def _export_one(self, conn, file_name: str, zf: zipfile.ZipFile, bundle_name: str) -> int:
        key = file_name.upper()
        if key not in QUERIES:
            raise RuntimeError(f"ยังไม่มี mapping สำหรับแฟ้ม {key}")

        columns, sql = QUERIES[key]
        date_from_iso = _to_iso_date(self.date_from)
        date_to_iso = _to_iso_date(self.date_to)

        # ส่งออกทั้งหมด: ใช้ช่วงวันที่ open (1900-01-01..9999-12-31)
        # ใช้กับ PERSON และแฟ้มที่ผูกกับ PID เดียวกัน (CHRONIC, CARD, ADDRESS, HOME, DEATH)
        person_linked = {"PERSON", "CHRONIC", "CARD", "ADDRESS", "HOME", "DEATH"}
        if key in person_linked and self.export_all_persons:
            date_from_iso = "1900-01-01"
            date_to_iso = "9999-12-31"

        with conn.cursor() as cursor:
            # แต่ละชุด filter ใช้ 4 placeholder: date_from, date_to, ovstist, ovstist
            params = (date_from_iso, date_to_iso, self.ovstist, self.ovstist)
            placeholder_count = len(re.findall(r"(?<!%)%s", sql))
            if placeholder_count % len(params) != 0:
                raise RuntimeError(f"จำนวน placeholder ของ {key} ไม่ถูกต้อง: {placeholder_count}")
            cursor.execute(
                sql,
                params * (placeholder_count // len(params)),
            )

            buffer = io.StringIO()
            buffer.write("|".join(c.upper() for c in columns) + "\n")
            count = 0
            while True:
                if self._cancel:
                    break
                chunk = cursor.fetchmany(2000)
                if not chunk:
                    break
                for row in chunk:
                    buffer.write("|".join(_format_value(v) for v in row) + "\n")
                    count += 1

            zf.writestr(f"{bundle_name}/{file_name.upper()}.TXT", buffer.getvalue())
            return count


class F43ExportWindow(F43ExportUI):
    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _ExportWorker | None = None

        # default output folder = user's Desktop
        desktop = Path.home() / "Desktop"
        if desktop.is_dir():
            self.output_path.setText(str(desktop))

        self._load_ovstist_options()

        self.btn_browse.clicked.connect(self.browse_output_folder)
        self.btn_export.clicked.connect(self._on_export_clicked)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)

    def _on_source_changed(self, _index: int) -> None:
        if self.selected_source() != "zip":
            return
        from F43Import_dlg import F43ImportDialog
        dlg = F43ImportDialog(self)
        dlg.exec()
        # ไม่เปลี่ยนช่วงวันที่อัตโนมัติ — ปล่อยให้ user เลือกเอง (default = วันนี้)

    def _load_ovstist_options(self) -> None:
        try:
            conn = _open_his_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT ovstist, name FROM ovstist "
                        "WHERE ovstist IS NOT NULL AND ovstist <> '' "
                        "ORDER BY ovstist"
                    )
                    items = [(str(c), f"{c} - {n}") for c, n in cursor.fetchall()]
            finally:
                conn.close()
            self.populate_ovstist(items)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def _on_export_clicked(self) -> None:
        files = self.selected_files()
        if not files:
            QMessageBox.warning(self, "ยังไม่ได้เลือกแฟ้ม", "กรุณาเลือกอย่างน้อย 1 แฟ้ม")
            return

        out_dir_text = self.output_path.text().strip()
        if not out_dir_text:
            QMessageBox.warning(self, "ยังไม่ได้เลือกโฟลเดอร์", "กรุณาเลือกโฟลเดอร์ส่งออก")
            return
        out_dir = Path(out_dir_text)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "สร้างโฟลเดอร์ไม่สำเร็จ", str(exc))
            return

        d_from = self.date_from.date()
        d_to = self.date_to.date()
        if d_from > d_to:
            QMessageBox.warning(self, "ช่วงวันที่ไม่ถูกต้อง", "วันที่เริ่มต้องไม่เกินวันที่สิ้นสุด")
            return

        date_from_str = date(d_from.year(), d_from.month(), d_from.day()).strftime("%Y%m%d")
        date_to_str = date(d_to.year(), d_to.month(), d_to.day()).strftime("%Y%m%d")

        ovstist = self.selected_ovstist()
        self.log_view.clear()
        ovstist_label = ovstist if ovstist else "ทั้งหมด"
        source = self.selected_source()
        source_label = "HIS" if source == "his" else "ZIP 43 แฟ้ม"
        self.append_log(
            f"เริ่มส่งออก {len(files)} แฟ้ม | แหล่งข้อมูล: {source_label}"
            f" | ช่วงวันที่ {date_from_str} - {date_to_str}"
            f" | ประเภทการมา: {ovstist_label}"
        )
        self.append_log(f"โฟลเดอร์ส่งออก: {out_dir}")

        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self.btn_export.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self._thread = QThread(self)
        self._worker = _ExportWorker(
            files, date_from_str, date_to_str, out_dir, ovstist,
            export_all_persons=self.is_export_all_persons(),
            source=self.selected_source(),
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self.append_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()

    def _on_cancel_clicked(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self.btn_cancel.setEnabled(False)
            self.append_log("กำลังยกเลิก...")

    def _on_progress(self, current: int, total: int, message: str) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        if message:
            self.statusBar().showMessage(message)

    def _on_finished(self, success: int, failed: int) -> None:
        self.append_log(f"\nสรุป: สำเร็จ {success} แฟ้ม, ล้มเหลว {failed} แฟ้ม")
        self.btn_export.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.statusBar().showMessage("เสร็จสิ้น", 5000)
        if failed and not success:
            QMessageBox.critical(self, "ส่งออกไม่สำเร็จ", f"ล้มเหลวทั้งหมด {failed} แฟ้ม")
        elif failed:
            QMessageBox.warning(self, "ส่งออกสำเร็จบางส่วน", f"สำเร็จ {success} / ล้มเหลว {failed}")
        else:
            QMessageBox.information(self, "ส่งออกสำเร็จ", f"ส่งออก {success} แฟ้มเรียบร้อย")

    def _on_failed(self, message: str) -> None:
        self.append_log(f"ผิดพลาด: {message}")
        self.btn_export.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        QMessageBox.critical(self, "ส่งออกไม่สำเร็จ", message)

    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
