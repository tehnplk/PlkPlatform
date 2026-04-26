"""F43Import_dlg — Dialog นำเข้าไฟล์ ZIP 43 แฟ้ม และแสดงแต่ละแฟ้มเป็น tab

โหลดไฟล์ TXT ใน ZIP → ล้างทุกตารางใน F43.db → INSERT แถวใหม่ทั้งหมด
"""
from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path

F43_DB_PATH = Path(__file__).parent / "F43.db"

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from Theme_helper import current_theme


class F43ImportDialog(QDialog):
    """เลือกไฟล์ ZIP 43 แฟ้ม → แสดงเนื้อหาทุกแฟ้มเป็น tab"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("นำเข้า ZIP 43 แฟ้ม - F43Import")
        self.resize(1100, 720)
        self._zip_path: Path | None = None
        self._init_ui()
        self._apply_theme()

    # ------------------------------------------------------------------ UI
    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # แถวเลือกไฟล์
        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("ไฟล์ ZIP:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("เลือกไฟล์ ZIP 43 แฟ้ม...")
        self.btn_browse = QPushButton("เลือกไฟล์...")
        self.btn_browse.clicked.connect(self._on_browse)
        file_row.addWidget(self.path_edit, 1)
        file_row.addWidget(self.btn_browse)
        root.addLayout(file_row)

        # Tab สำหรับแต่ละแฟ้ม
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        root.addWidget(self.tabs, 1)

        # ปุ่มปิด
        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        self.btn_close = QPushButton("ปิด")
        self.btn_close.setMinimumHeight(34)
        self.btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_close)
        root.addLayout(bottom_row)

    # ---------------------------------------------------------------- handlers
    def _on_browse(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "เลือกไฟล์ ZIP 43 แฟ้ม",
            "",
            "ZIP Files (*.zip);;All Files (*)",
        )
        if not path_str:
            return
        self._load_zip(Path(path_str))

    def _load_zip(self, zip_path: Path) -> None:
        self.tabs.clear()
        self._zip_path = zip_path
        self.path_edit.setText(str(zip_path))
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                txt_names = sorted(
                    n for n in zf.namelist() if n.upper().endswith(".TXT")
                )
                if not txt_names:
                    QMessageBox.warning(
                        self, "ไม่พบไฟล์ TXT",
                        "ไม่พบไฟล์ .TXT ใน ZIP — โปรดเลือกไฟล์ ZIP 43 แฟ้มที่ถูกต้อง",
                    )
                    return

                # อ่านเนื้อหาทุกไฟล์ก่อน (เก็บใน dict ชื่อแฟ้ม → text)
                contents: dict[str, str] = {}
                for name in txt_names:
                    with zf.open(name) as fp:
                        contents[Path(name).stem.upper()] = fp.read().decode("utf-8-sig", errors="replace")

                # ล้าง F43.db และเขียนใหม่ทั้งหมด
                inserted = self._import_to_sqlite(contents)

                # แสดงผลทุกแฟ้มเป็น tab
                for tab_label in sorted(contents):
                    n = inserted.get(tab_label, 0)
                    self.tabs.addTab(self._build_table_tab(contents[tab_label]), f"{tab_label} ({n})")
        except zipfile.BadZipFile:
            QMessageBox.critical(self, "ไฟล์เสียหาย", "ไม่สามารถอ่านไฟล์ ZIP")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", str(exc))

    def imported_date_range(self) -> tuple[str, str] | None:
        """คืน (min, max) date_serv จาก SERVICE ใน F43.db หรือ None ถ้าไม่มี"""
        if not F43_DB_PATH.exists():
            return None
        conn = sqlite3.connect(F43_DB_PATH)
        try:
            row = conn.execute(
                'SELECT MIN(date_serv), MAX(date_serv) FROM "SERVICE" '
                'WHERE date_serv IS NOT NULL AND date_serv <> \'\''
            ).fetchone()
            if row and row[0] and row[1]:
                return (str(row[0]), str(row[1]))
            return None
        finally:
            conn.close()

    def _import_to_sqlite(self, contents: dict[str, str]) -> dict[str, int]:
        """ล้างทุกตารางใน F43.db แล้ว INSERT แถวจาก contents
        คืน mapping ชื่อแฟ้ม → จำนวนแถวที่ insert"""
        if not F43_DB_PATH.exists():
            QMessageBox.warning(
                self, "ไม่พบ F43.db",
                f"ไม่พบไฟล์ {F43_DB_PATH.name} — สร้างด้วย build_f43_db.py ก่อน",
            )
            return {}

        result: dict[str, int] = {}
        conn = sqlite3.connect(F43_DB_PATH)
        try:
            db_tables = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            # ล้างทุกตาราง (ไม่เฉพาะที่จะเขียน — รับประกัน "ก่อนนำเข้าใหม่ทุกครั้ง")
            for tbl in db_tables:
                conn.execute(f'DELETE FROM "{tbl}"')

            # INSERT ตามไฟล์ใน ZIP
            for name, text in contents.items():
                if name not in db_tables:
                    continue  # ไฟล์ที่ไม่มีตารางใน F43.db → ข้าม
                lines = [ln for ln in text.splitlines() if ln.strip()]
                if len(lines) < 2:
                    result[name] = 0
                    continue
                header = [h.strip() for h in lines[0].split("|")]
                rows = [ln.split("|") for ln in lines[1:]]

                placeholders = ",".join(["?"] * len(header))
                col_list = ",".join(f'"{h.lower()}"' for h in header)
                sql = f'INSERT INTO "{name}" ({col_list}) VALUES ({placeholders})'

                # pad/truncate to header width
                normalized = [
                    (r + [""] * len(header))[: len(header)] for r in rows
                ]
                conn.executemany(sql, normalized)
                result[name] = len(rows)

            conn.commit()
        finally:
            conn.close()
        return result

    # ---------------------------------------------------------------- helpers
    def _build_table_tab(self, text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        lines = [ln for ln in text.splitlines() if ln.strip()]
        if not lines:
            layout.addWidget(QLabel("(ไฟล์ว่าง)"))
            return page

        header = lines[0].split("|")
        rows = [ln.split("|") for ln in lines[1:]]

        info = QLabel(f"จำนวนแถว: {len(rows)}  |  คอลัมน์: {len(header)}")
        info.setStyleSheet("color: #1f5c3f; font-weight: 600;")
        layout.addWidget(info)

        table = QTableWidget()
        table.setColumnCount(len(header))
        table.setHorizontalHeaderLabels(header)
        table.setRowCount(len(rows))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setDefaultSectionSize(22)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(True)

        for r, fields in enumerate(rows):
            for c in range(len(header)):
                value = fields[c] if c < len(fields) else ""
                table.setItem(r, c, QTableWidgetItem(value))

        table.resizeColumnsToContents()
        layout.addWidget(table, 1)
        return page

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QDialog {{ background: {theme.window}; }}
            QLabel {{ color: {theme.text}; }}
            QLineEdit, QTabWidget::pane {{
                border: 1px solid {theme.border}; border-radius: 6px;
                background: {theme.surface};
            }}
            QLineEdit {{ padding: 4px 8px; }}
            QPushButton {{
                background: {theme.primary}; color: {theme.primary_text}; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.primary_hover}; }}
            QTabBar::tab {{
                background: {theme.surface}; color: {theme.text};
                padding: 6px 12px; border: 1px solid {theme.border};
                border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {theme.primary}; color: {theme.primary_text};
            }}
            QTableWidget {{
                gridline-color: {theme.border}; background: {theme.surface};
                alternate-background-color: #f4faf6;
            }}
            QHeaderView::section {{
                background: {theme.primary}; color: {theme.primary_text};
                padding: 4px 6px; border: none; font-weight: 600;
            }}
            """
        )
