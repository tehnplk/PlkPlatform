from __future__ import annotations

from typing import Optional
import csv
import json
import ssl
from datetime import datetime
from pathlib import Path
import zipfile

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from urllib import error as urlerror
from urllib import request as urlrequest


class TelemedDailyWindow(QMainWindow):
    """หน้าต่างสำหรับโมดูล อัพเดทTelemed Daily"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("อัพเดทTelemed Daily")
        self.resize(1200, 700)
        
        self.df: Optional[pd.DataFrame] = None
        self.current_file_path: Optional[str] = None
        
        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # Header section - File upload
        header_layout = QHBoxLayout()
        
        self.file_label = QLabel("ยังไม่ได้เลือกไฟล์")
        self.file_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.upload_button = QPushButton("เลือกไฟล์ .zip")
        self.upload_button.setMinimumWidth(150)
        self.upload_button.clicked.connect(self.on_upload_file)
        self.upload_button.setStyleSheet(
            """
            QPushButton {
                background: #2f6b4c;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #3b8a61;
            }
            QPushButton:pressed {
                background: #255a3f;
            }
            """
        )
        
        header_layout.addWidget(QLabel("ไฟล์ที่เลือก:"))
        header_layout.addWidget(self.file_label, 1)
        header_layout.addWidget(self.upload_button)
        
        main_layout.addLayout(header_layout)
        
        # Table section
        table_label = QLabel("ข้อมูลทะเบียน")
        table_label.setStyleSheet("font-weight: 600; color: #1f5c3f;")
        main_layout.addWidget(table_label)
        
        self.model = QStandardItemModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setColumnWidth(0, 60)
        
        main_layout.addWidget(self.table_view)
        
        # Action buttons section
        action_layout = QHBoxLayout()
        
        self.send_button = QPushButton("ส่งข้อมูลเข้าจังหวัด")
        self.send_button.setMinimumWidth(150)
        self.send_button.setEnabled(False)  # Disabled until data is loaded
        self.send_button.clicked.connect(self.on_send_data)
        self.send_button.setStyleSheet(
            """
            QPushButton {
                background: #dc3545;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #c82333;
            }
            QPushButton:pressed {
                background: #a02622;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
            """
        )
        
        action_layout.addStretch()
        action_layout.addWidget(self.send_button)
        action_layout.addStretch()
        
        main_layout.addLayout(action_layout)
        
        # Status bar
        self.statusBar().showMessage("พร้อมอัพโหลดไฟล์")

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #eefaf3;
            }
            QTableView {
                background: #ffffff;
                color: #000000;
                alternate-background-color: #f0faf6;
                gridline-color: #d0e8df;
                border: 1px solid #a7dabc;
                border-radius: 4px;
            }
            QTableView::item {
                color: #000000;
                padding: 4px;
            }
            QTableView::item:selected {
                background: #c8f0d8;
                color: #1f5c3f;
            }
            QHeaderView::section {
                background: #d8f4e4;
                color: #1f5c3f;
                padding: 5px;
                border: 1px solid #a7dabc;
                font-weight: 600;
            }
            QPushButton {
                background: #8ed1ad;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #7bc89c;
            }
            QPushButton:pressed {
                background: #6dbf8b;
            }
            QLabel {
                color: #2f6b4c;
            }
            """
        )

    def on_upload_file(self) -> None:
        """เลือกและอ่านไฟล์ ZIP ที่ขึ้นต้นด้วย F43_ และอ่าน SERVICE.txt"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "เลือกไฟล์ทะเบียน",
            "",
            "Zip Files (*.zip);;All Files (*)"
        )

        if not file_path:
            return

        file_name = Path(file_path).name
        if not file_name.startswith("F43_"):
            self._show_error("ชื่อไฟล์ต้องขึ้นต้นด้วย F43_ และเป็น .zip เท่านั้น")
            return

        if not file_path.lower().endswith(".zip"):
            self._show_error("รองรับเฉพาะไฟล์ .zip เท่านั้น")
            return

        try:
            with zipfile.ZipFile(file_path, "r") as archive:
                service_file = None
                for entry in archive.namelist():
                    if Path(entry).name.upper() == "SERVICE.TXT":
                        service_file = entry
                        break

                if service_file is None:
                    self._show_error("ไม่พบไฟล์ SERVICE.txt ในไฟล์ ZIP")
                    return

                with archive.open(service_file) as service_stream:
                    raw_data = service_stream.read()

                try:
                    content = raw_data.decode("utf-8-sig")
                except UnicodeDecodeError:
                    content = raw_data.decode("cp874", errors="replace")

            rows = self._parse_service_text(content)
            if not rows:
                self._show_error("SERVICE.txt ไม่มีข้อมูลให้แสดง")
                return

            self.df = pd.DataFrame(rows[1:], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows)
            self.current_file_path = file_path
            self.file_label.setText(f"{file_name} ({len(self.df)} แถว)")
            self._display_data_in_table()
            self.send_button.setEnabled(True)  # Enable send button after data is loaded
            self.statusBar().showMessage(f"อัพโหลดไฟล์สำเร็จ: {file_name}", 3000)

        except Exception as e:
            self._show_error(f"เกิดข้อผิดพลาด: {e}")

    def _parse_service_text(self, content: str) -> list[list[str]]:
        """Parse SERVICE.txt content into rows for display."""
        raw_lines = [line for line in content.splitlines() if line.strip()]
        if not raw_lines:
            return []

        delimiter = "\t"
        if "\t" in raw_lines[0]:
            delimiter = "\t"
        elif "|" in raw_lines[0]:
            delimiter = "|"
        elif "," in raw_lines[0]:
            delimiter = ","
        else:
            return [[line] for line in raw_lines]

        reader = csv.reader(raw_lines, delimiter=delimiter)
        rows = [list(map(str.strip, row)) for row in reader if any(cell.strip() for cell in row)]
        if not rows:
            return []

        first_row = rows[0]
        if len(rows) > 1 and any(cell.isalpha() for cell in first_row):
            return rows

        headers = [f"Field {idx + 1}" for idx in range(len(first_row))]
        return [headers] + rows

    def _show_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)
        QMessageBox.warning(self, "ข้อผิดพลาด", message)

    def _display_data_in_table(self) -> None:
        """แสดงข้อมูล DataFrame ในตาราง"""
        if self.df is None or self.df.empty:
            return
        
        # ตั้งค่า header
        columns = list(self.df.columns)
        self.model.setColumnCount(len(columns))
        self.model.setHorizontalHeaderLabels(columns)
        
        # เพิ่มข้อมูล
        self.model.setRowCount(len(self.df))
        for row_idx, (_, row) in enumerate(self.df.iterrows()):
            for col_idx, col_name in enumerate(columns):
                value = str(row[col_name]) if pd.notna(row[col_name]) else ""
                item = self.model.item(row_idx, col_idx)
                if item is None:
                    item = QStandardItem(value)
                    self.model.setItem(row_idx, col_idx, item)
                else:
                    item.setText(value)
        
        # ปรับขนาดคอลัมน์
        self.table_view.resizeColumnsToContents()

    def on_send_data(self) -> None:
        """ส่งข้อมูลเข้าจังหวัดตาม API VISIT_TYPE_DAILY_API.md"""
        if self.df is None or self.df.empty:
            self._show_error("ไม่มีข้อมูลให้ส่ง")
            return

        try:
            # นับจำนวน visit types ตามวันที่และรหัสโรงพยาบาล
            visit_counts = self._count_visit_types()
            
            if not visit_counts:
                self._show_error("ไม่มีข้อมูลให้ส่งหลังการนับ")
                return

            # ส่งข้อมูลไปยัง API
            self._send_to_api(visit_counts)

        except Exception as e:
            self._show_error(f"เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")

    def _count_visit_types(self) -> list[dict]:
        """นับจำนวน visit types จากข้อมูล SERVICE.txt"""
        if self.df is None or self.df.empty:
            return []

        # ตรวจสอบคอลัมน์ที่มีอยู่
        required_cols = ['HOSPCODE', 'DATE_SERV', 'TYPEIN', 'TYPEOUT']
        available_cols = [col.upper() for col in self.df.columns]
        
        # Map คอลัมน์ที่มีอยู่
        col_mapping = {}
        for req_col in required_cols:
            if req_col in available_cols:
                col_mapping[req_col] = req_col
            elif req_col.lower() in available_cols:
                col_mapping[req_col] = req_col.lower()
            else:
                # หาคอลัมน์ที่คล้ายกัน
                for avail_col in available_cols:
                    if req_col.lower() in avail_col.lower():
                        col_mapping[req_col] = avail_col
                        break

        if 'HOSPCODE' not in col_mapping or 'DATE_SERV' not in col_mapping:
            raise ValueError("ไม่พบคอลัมน์ HOSPCODE หรือ DATE_SERV ที่จำเป็น")

        # นับจำนวนตามกลุ่ม
        counts = {}
        
        for _, row in self.df.iterrows():
            try:
                hoscode = str(row[col_mapping['HOSPCODE']]).strip()
                date_serv = str(row[col_mapping['DATE_SERV']]).strip()
                
                # แปลงวันที่เป็น YYYY-MM-DD
                if len(date_serv) == 8:  # รูปแบบ YYYYMMDD
                    date_serv = f"{date_serv[:4]}-{date_serv[4:6]}-{date_serv[6:8]}"
                
                # ตรวจสอบ TYPEIN และ TYPEOUT
                typein = str(row.get(col_mapping.get('TYPEIN', ''), '')).strip()
                typeout = str(row.get(col_mapping.get('TYPEOUT', ''), '')).strip()
                
                # ใช้ TYPEIN เป็นหลัก ถ้าไม่มีใช้ TYPEOUT
                visit_type = typein or typeout
                
                key = (hoscode, date_serv)
                if key not in counts:
                    counts[key] = {'hoscode': hoscode, 'visit_date': date_serv, 
                                 'visit_type_2': 0, 'visit_type_3': 0, 'visit_type_5': 0}
                
                # นับตาม visit type
                if visit_type == '2':
                    counts[key]['visit_type_2'] += 1
                elif visit_type == '3':
                    counts[key]['visit_type_3'] += 1
                elif visit_type == '5':
                    counts[key]['visit_type_5'] += 1
                    
            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        return list(counts.values())

    def _send_to_api(self, visit_counts: list[dict]) -> None:
        """ส่งข้อมูลไปยัง VISIT_TYPE_DAILY_API"""
        API_URL = "https://dashboard.plkhealth.go.th/telemedicine/api/visit-type-daily"
        
        # เตรียม payload
        payload = visit_counts if len(visit_counts) > 1 else visit_counts[0]
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        # สร้าง request
        req = urlrequest.Request(
            API_URL,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        self.statusBar().showMessage("กำลังส่งข้อมูลเข้าจังหวัด...", 3000)
        self.send_button.setEnabled(False)

        try:
            # สร้าง SSL context ที่ไม่ verify certificate (สำหรับ development)
            ssl_context = ssl._create_unverified_context()
            
            with urlrequest.urlopen(req, timeout=30, context=ssl_context) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                status_code = resp.status
        except urlerror.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            status_code = exc.code
        except urlerror.URLError as exc:
            self.send_button.setEnabled(True)
            self._show_error(f"เชื่อมต่อไม่สำเร็จ: {exc.reason}")
            return

        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw}

        sent_count = len(visit_counts)
        if 200 <= status_code < 300 and parsed.get("status") == "success":
            self.statusBar().showMessage(
                f"ส่งข้อมูลเข้าจังหวัดสำเร็จ ({sent_count} รายการ)", 5000
            )
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("ส่งข้อมูลเข้าจังหวัด")
            msg.setText(f"ส่งข้อมูล {sent_count} รายการสำเร็จ")
            msg.setStyleSheet("QLabel { color: white; } QMessageBox { background-color: #2f6b4c; }")
            msg.exec()
        else:
            self.statusBar().showMessage("ส่งข้อมูลเข้าจังหวัดไม่สำเร็จ", 5000)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("ส่งข้อมูลเข้าจังหวัด")
            msg.setText(f"HTTP {status_code}\n\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
            msg.setStyleSheet("QLabel { color: white; } QMessageBox { background-color: #dc3545; }")
            msg.exec()
        
        self.send_button.setEnabled(True)
