from __future__ import annotations

import io
import traceback
import zipfile
from datetime import date, datetime
from pathlib import Path

import pymysql
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from F43Export_ui import F43ExportUI
from Setting_helper import load_db_settings


TABLE_PREFIX = "tmp_exp_3090_"
TEMP_DB_NAME = "temp"
DATE_COLUMN = "date_serv"  # YYYYMMDD


def _open_temp_connection() -> pymysql.connections.Connection:
    """เปิด connection ไปที่ db `temp` ด้วยพารามิเตอร์ host/user/password ของ HIS"""
    s = load_db_settings()
    return pymysql.connect(
        host=str(s["host"]) or "localhost",
        port=int(s["port"]),
        user=str(s["user"]),
        password=str(s["password"]),
        database=TEMP_DB_NAME,
        charset=str(s["charset"]) or "utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
    )


def _table_has_date_column(cursor, table: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s AND column_name = %s LIMIT 1",
        (TEMP_DB_NAME, table, DATE_COLUMN),
    )
    return cursor.fetchone() is not None


def _format_value(value) -> str:
    if value is None:
        return ""
    text = str(value)
    # ป้องกัน delimiter / newline หลุดเข้าไปในไฟล์
    return text.replace("|", " ").replace("\r", " ").replace("\n", " ")


class _ExportWorker(QObject):
    progress = pyqtSignal(int, int, str)  # current, total, message
    log = pyqtSignal(str)
    finished = pyqtSignal(int, int)  # success_count, failed_count
    failed = pyqtSignal(str)

    def __init__(
        self,
        files: list[str],
        date_from: str,
        date_to: str,
        output_dir: Path,
    ) -> None:
        super().__init__()
        self.files = files
        self.date_from = date_from
        self.date_to = date_to
        self.output_dir = output_dir
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            conn = _open_temp_connection()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.failed.emit(f"เชื่อมต่อ db `temp` ไม่สำเร็จ: {exc}")
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

    def _lookup_hospcode(self, conn) -> str:
        """ดึง hospcode จากตาราง person — ใช้สร้างชื่อไฟล์ zip"""
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT hospcode FROM `{TABLE_PREFIX}person` "
                "WHERE hospcode IS NOT NULL AND hospcode <> '' LIMIT 1"
            )
            row = cursor.fetchone()
            return str(row[0]).strip() if row and row[0] else ""

    def _export_one(self, conn, file_name: str, zf: zipfile.ZipFile, bundle_name: str) -> int:
        table = f"{TABLE_PREFIX}{file_name.lower()}"
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = %s LIMIT 1",
                (TEMP_DB_NAME, table),
            )
            if cursor.fetchone() is None:
                raise RuntimeError(f"ไม่พบตาราง {table}")

            has_date = _table_has_date_column(cursor, table)

            # ดึงรายชื่อคอลัมน์ตามลำดับจริง
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (TEMP_DB_NAME, table),
            )
            columns = [row[0] for row in cursor.fetchall()]
            col_list = ", ".join(f"`{c}`" for c in columns)

            if has_date:
                sql = (
                    f"SELECT {col_list} FROM `{table}` "
                    f"WHERE {DATE_COLUMN} BETWEEN %s AND %s"
                )
                params: tuple = (self.date_from, self.date_to)
            else:
                sql = f"SELECT {col_list} FROM `{table}`"
                params = ()

            cursor.execute(sql, params)

            buffer = io.StringIO()
            # header แถวแรก — ชื่อฟิลด์ตัวพิมพ์ใหญ่ pipe-delimited
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

        self.btn_browse.clicked.connect(self.browse_output_folder)
        self.btn_export.clicked.connect(self._on_export_clicked)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

    # ------------------------------------------------------------------ ui
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

        self.log_view.clear()
        self.append_log(
            f"เริ่มส่งออก {len(files)} แฟ้ม | ช่วงวันที่ {date_from_str} - {date_to_str}"
        )
        self.append_log(f"โฟลเดอร์ส่งออก: {out_dir}")

        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self.btn_export.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self._thread = QThread(self)
        self._worker = _ExportWorker(files, date_from_str, date_to_str, out_dir)
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
