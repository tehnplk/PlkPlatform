from __future__ import annotations

from PyQt6.QtCore import QDate, QLocale, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from Theme_helper import current_theme

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
# เฟสแรกเปิดเฉพาะแฟ้มของผลงาน TELEMED
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
        self.date_from.setMinimumWidth(120)
        self.date_from.setLocale(en_locale)
        if self.date_from.calendarWidget() is not None:
            self.date_from.calendarWidget().setLocale(en_locale)
        today = QDate.currentDate()
        self.date_from.setDate(today)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setMinimumWidth(120)
        self.date_to.setLocale(en_locale)
        if self.date_to.calendarWidget() is not None:
            self.date_to.calendarWidget().setLocale(en_locale)
        self.date_to.setDate(today)

        date_layout.addWidget(QLabel("ตั้งแต่:"))
        date_layout.addWidget(self.date_from)
        date_layout.addSpacing(10)
        date_layout.addWidget(QLabel("ถึง:"))
        date_layout.addWidget(self.date_to)
        date_layout.addSpacing(16)
        date_layout.addWidget(QLabel("ประเภทการมา:"))
        self.ovstist_combo = QComboBox()
        self.ovstist_combo.addItem("ทั้งหมด", "")
        self.ovstist_combo.setMinimumWidth(280)
        date_layout.addWidget(self.ovstist_combo)
        date_layout.addSpacing(16)
        date_layout.addWidget(QLabel("PERSON:"))
        self.person_scope_combo = QComboBox()
        self.person_scope_combo.addItem("ส่งออกเฉพาะคนที่มีบริการ", "visit")
        self.person_scope_combo.addItem("ส่งออกทั้งหมด", "all")
        self.person_scope_combo.setMinimumWidth(220)
        date_layout.addWidget(self.person_scope_combo)
        date_layout.addStretch(1)
        root.addWidget(date_box)

        # --- File selection ----------------------------------------------
        files_box = QGroupBox("เลือกแฟ้มที่จะส่งออก")
        files_outer = QVBoxLayout(files_box)

        # ปุ่มเลือก/ยกเลิกทั้งหมด + presets
        toolbar = QHBoxLayout()
        self.select_all_check = QCheckBox("เลือกทั้งหมด")
        self.select_all_check.setChecked(False)
        self.select_all_check.setEnabled(False)
        self.select_all_check.setToolTip("ยังไม่เปิดใช้งาน")
        self.select_all_check.stateChanged.connect(self._on_select_all_changed)
        toolbar.addWidget(self.select_all_check)

        toolbar.addSpacing(16)

        # presets: ชื่อ → (รายการแฟ้ม, ovstist หรือ None)
        self._presets: dict[str, tuple[list[str], str | None]] = {
            "ผลงาน EPI": (["PERSON", "SERVICE", "EPI"], None),
            "ผลงาน ANC": (["PERSON", "SERVICE", "ANC"], None),
            "ผลงาน TELEMED": (["PERSON", "SERVICE", "DIAGNOSIS_OPD"], "05"),
        }
        # เฟสแรกเปิดเฉพาะ TELEMED
        ENABLED_PRESETS = {"ผลงาน TELEMED"}
        self.preset_checks: dict[str, QCheckBox] = {}
        for label in self._presets:
            cb = QCheckBox(label)
            cb.setChecked(False)
            enabled = label in ENABLED_PRESETS
            cb.setEnabled(enabled)
            if not enabled:
                cb.setToolTip("ยังไม่เปิดใช้งาน")
            cb.stateChanged.connect(lambda s, n=label: self._on_preset_changed(n, s))
            toolbar.addWidget(cb)
            self.preset_checks[label] = cb

        toolbar.addStretch(1)
        files_outer.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(280)
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
            cb.setChecked(False)
            if not enabled:
                cb.setToolTip("ยังไม่เปิดใช้งาน")
            cb.stateChanged.connect(self._on_file_check_changed)
            grid.addWidget(cb, idx // cols, idx % cols)
            self.file_checks[name] = cb

        scroll.setWidget(grid_host)
        files_outer.addWidget(scroll, 1)
        root.addWidget(files_box, 3)

        # --- Output folder ------------------------------------------------
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("โฟลเดอร์ส่งออก:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("เลือกโฟลเดอร์ที่จะเก็บไฟล์ส่งออก...")
        self.btn_browse = QPushButton("Browse...")
        out_row.addWidget(self.output_path, 1)
        out_row.addWidget(self.btn_browse)
        root.addLayout(out_row)

        # --- Action row: ZIP buttons ซ้าย, ศูนย์ข้อมูลอำเภอ ขวา -----------
        action_row = QHBoxLayout()
        self.btn_export = QPushButton("ส่งออกไฟล์ ZIP")
        self.btn_export.setMinimumHeight(38)
        self.btn_cancel = QPushButton("ยกเลิก")
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setEnabled(False)
        self.btn_send_dho = QPushButton("ส่งศูนย์ข้อมูลอำเภอ")
        self.btn_send_dho.setMinimumHeight(38)
        self.btn_send_dho.setEnabled(False)
        self.btn_send_dho.setToolTip("ยังไม่เปิดใช้งาน")
        action_row.addWidget(self.btn_export)
        action_row.addWidget(self.btn_cancel)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_send_dho)
        root.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setLocale(en_locale)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(90)
        root.addWidget(self.log_view, 1)

    def populate_ovstist(self, items: list[tuple[str, str]]) -> None:
        """items = [(ovstist_code, label), ...] — appended after 'ทั้งหมด'"""
        # ตัวแรก 'ทั้งหมด' (data='') ไว้แล้ว
        for code, label in items:
            self.ovstist_combo.addItem(label, code)

    def selected_ovstist(self) -> str:
        return str(self.ovstist_combo.currentData() or "")

    def is_export_all_persons(self) -> bool:
        return str(self.person_scope_combo.currentData() or "") == "all"

    def selected_files(self) -> list[str]:
        return [
            name
            for name, cb in self.file_checks.items()
            if cb.isEnabled() and cb.isChecked()
        ]

    def append_log(self, message: str) -> None:
        self.log_view.append(message)

    def _on_select_all_changed(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self.file_checks.values():
            if cb.isEnabled():
                cb.blockSignals(True)
                cb.setChecked(checked)
                cb.blockSignals(False)
        if checked:
            self._clear_presets()

    def _on_file_check_changed(self) -> None:
        enabled_cbs = [cb for cb in self.file_checks.values() if cb.isEnabled()]
        if not enabled_cbs:
            return
        all_checked = all(cb.isChecked() for cb in enabled_cbs)
        self.select_all_check.blockSignals(True)
        self.select_all_check.setChecked(all_checked)
        self.select_all_check.blockSignals(False)

    def _on_preset_changed(self, label: str, state: int) -> None:
        if state != Qt.CheckState.Checked.value:
            # uncheck preset → ล้างแฟ้มทั้งหมด + reset combo ประเภทการมา
            for cb in self.file_checks.values():
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
            self.ovstist_combo.setCurrentIndex(0)
            return
        # exclusive: ปิด preset อื่น + select_all
        for other_label, other_cb in self.preset_checks.items():
            if other_label != label:
                other_cb.blockSignals(True)
                other_cb.setChecked(False)
                other_cb.blockSignals(False)
        self.select_all_check.blockSignals(True)
        self.select_all_check.setChecked(False)
        self.select_all_check.blockSignals(False)

        files, ovstist = self._presets[label]
        # uncheck all → check เฉพาะแฟ้มใน preset
        for name, cb in self.file_checks.items():
            cb.blockSignals(True)
            cb.setChecked(name in files and cb.isEnabled())
            cb.blockSignals(False)
        # set ประเภทการมา ถ้า preset กำหนด
        if ovstist is not None:
            for i in range(self.ovstist_combo.count()):
                if self.ovstist_combo.itemData(i) == ovstist:
                    self.ovstist_combo.setCurrentIndex(i)
                    break

    def _clear_presets(self) -> None:
        for cb in self.preset_checks.values():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)

    def browse_output_folder(self) -> str:
        directory = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์ส่งออก")
        if directory:
            self.output_path.setText(directory)
        return directory

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {theme.window}; }}
            QGroupBox {{
                border: 1px solid {theme.border}; border-radius: 6px;
                margin-top: 10px; padding: 10px;
                font-weight: 700; color: {theme.primary};
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
            QLabel {{ color: {theme.primary}; }}
            QLineEdit, QDateEdit, QTextEdit, QScrollArea, QComboBox {{
                border: 1px solid {theme.border}; border-radius: 6px;
                background: {theme.surface};
                color: {theme.text};
            }}
            QLineEdit, QDateEdit, QTextEdit, QComboBox {{ padding: 4px 8px; }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ border: 1px solid {theme.primary}; }}
            QCheckBox {{ color: {theme.primary}; padding: 2px; }}
            QCheckBox:disabled {{ color: {theme.primary}; }}
            QPushButton {{
                background: {theme.primary}; color: {theme.primary_text}; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.primary_hover}; }}
            QPushButton:pressed {{ background: {theme.primary_pressed}; }}
            QPushButton:disabled {{ background: {theme.disabled}; color: {theme.disabled_text}; }}
            QProgressBar {{
                border: 1px solid {theme.border}; border-radius: 6px;
                text-align: center; background: {theme.surface};
                color: {theme.text};
            }}
            QProgressBar::chunk {{ background: {theme.primary}; border-radius: 5px; }}
            """
        )
