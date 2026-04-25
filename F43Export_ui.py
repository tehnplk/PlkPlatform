from __future__ import annotations

from PyQt6.QtCore import QDate, QLocale, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# 43 แฟ้มมาตรฐาน (ลบ prefix tmp_exp_3090_) — ตามตารางใน db `temp`
ALL_FILES = [
    "ACCIDENT", "ADDRESS", "ADMISSION", "ANC", "APPOINTMENT", "CARD",
    "CARE_REFER", "CHARGE_IPD", "CHARGE_OPD", "CHRONIC", "CHRONICFU",
    "CLINICAL_REFER", "COMMUNITY_ACTIVITY", "COMMUNITY_SERVICE",
    "DATA_CORRECT", "DEATH", "DENTAL", "DIAGNOSIS_IPD", "DIAGNOSIS_OPD",
    "DISABILITY", "DRUG_IPD", "DRUG_OPD", "DRUG_REFER", "DRUGALLERGY",
    "EPI", "FP", "FUNCTIONAL", "HOME", "ICF", "INVESTIGATION_REFER",
    "LABFU", "LABOR", "NCDSCREEN", "NEWBORN", "NEWBORNCARE", "NUTRITION",
    "PERSON", "POLICY", "POSTNATAL", "PRENATAL", "PROCEDURE_IPD",
    "PROCEDURE_OPD", "PROCEDURE_REFER", "PROVIDER", "REFER_HISTORY",
    "REFER_RESULT", "REHABILITATION", "SERVICE", "SPECIALPP",
    "SURVEILLANCE", "VILLAGE", "WOMEN",
]

# เฟสแรกเปิดเฉพาะ 3 แฟ้มนี้
ENABLED_FILES = {"PERSON", "SERVICE", "DIAGNOSIS_OPD"}


class F43ExportUI(QMainWindow):
    """UI สำหรับ F43Export — ส่งออก 43 แฟ้มจาก temp.tmp_exp_3090_* ตามช่วง visit_date"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ส่งออก 43 แฟ้ม")
        self.resize(1000, 720)
        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        en_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

        # --- Date range ---------------------------------------------------
        date_box = QGroupBox("ช่วงวันที่ (filter ด้วย date_serv = visit_date)")
        date_layout = QHBoxLayout(date_box)
        date_layout.setSpacing(8)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setLocale(en_locale)
        if self.date_from.calendarWidget() is not None:
            self.date_from.calendarWidget().setLocale(en_locale)
        today = QDate.currentDate()
        self.date_from.setDate(today.addDays(-7))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setLocale(en_locale)
        if self.date_to.calendarWidget() is not None:
            self.date_to.calendarWidget().setLocale(en_locale)
        self.date_to.setDate(today)

        date_layout.addWidget(QLabel("ตั้งแต่:"))
        date_layout.addWidget(self.date_from)
        date_layout.addSpacing(10)
        date_layout.addWidget(QLabel("ถึง:"))
        date_layout.addWidget(self.date_to)
        date_layout.addStretch(1)
        root.addWidget(date_box)

        # --- File selection ----------------------------------------------
        files_box = QGroupBox(
            "เลือกแฟ้มที่จะส่งออก (เฟสแรกเปิด PERSON / SERVICE / DIAGNOSIS_OPD)"
        )
        files_outer = QVBoxLayout(files_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(6, 6, 6, 6)

        self.file_checks: dict[str, QCheckBox] = {}
        cols = 10
        for idx, name in enumerate(ALL_FILES):
            cb = QCheckBox(name)
            enabled = name in ENABLED_FILES
            cb.setEnabled(enabled)
            cb.setChecked(enabled)
            if not enabled:
                cb.setToolTip("ยังไม่เปิดใช้งานในเฟสแรก")
            grid.addWidget(cb, idx // cols, idx % cols)
            self.file_checks[name] = cb

        scroll.setWidget(grid_host)
        files_outer.addWidget(scroll, 1)
        root.addWidget(files_box, 1)

        # --- Output folder ------------------------------------------------
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("โฟลเดอร์ส่งออก:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("เลือกโฟลเดอร์ที่จะเก็บไฟล์ส่งออก...")
        self.btn_browse = QPushButton("Browse...")
        out_row.addWidget(self.output_path, 1)
        out_row.addWidget(self.btn_browse)
        root.addLayout(out_row)

        # --- Action + progress -------------------------------------------
        action_row = QHBoxLayout()
        self.btn_export = QPushButton("เริ่มส่งออก")
        self.btn_export.setMinimumHeight(38)
        self.btn_cancel = QPushButton("ยกเลิก")
        self.btn_cancel.setEnabled(False)
        action_row.addWidget(self.btn_export)
        action_row.addWidget(self.btn_cancel)
        action_row.addStretch(1)
        root.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setLocale(en_locale)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(140)
        root.addWidget(self.log_view, 1)

    def selected_files(self) -> list[str]:
        return [
            name
            for name, cb in self.file_checks.items()
            if cb.isEnabled() and cb.isChecked()
        ]

    def append_log(self, message: str) -> None:
        self.log_view.append(message)

    def browse_output_folder(self) -> str:
        directory = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์ส่งออก")
        if directory:
            self.output_path.setText(directory)
        return directory

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f4f7f5; }
            QGroupBox {
                border: 1px solid #c4d6cc; border-radius: 6px;
                margin-top: 10px; padding: 10px;
                font-weight: 700; color: #1f5c3f;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QLabel { color: #1f5c3f; }
            QLineEdit, QDateEdit, QTextEdit, QScrollArea {
                border: 1px solid #c4d6cc; border-radius: 6px;
                background: #ffffff;
            }
            QLineEdit, QDateEdit, QTextEdit { padding: 4px 8px; }
            QLineEdit:focus, QDateEdit:focus { border: 1px solid #2f6b4c; }
            QCheckBox { color: #1f5c3f; padding: 2px; }
            QCheckBox:disabled { color: #98ada3; }
            QPushButton {
                background: #2f6b4c; color: #ffffff; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #3b8a61; }
            QPushButton:pressed { background: #255a3f; }
            QPushButton:disabled { background: #9eb7ac; color: #eef2ef; }
            QProgressBar {
                border: 1px solid #c4d6cc; border-radius: 6px;
                text-align: center; background: #ffffff;
            }
            QProgressBar::chunk { background: #2f6b4c; border-radius: 5px; }
            """
        )
