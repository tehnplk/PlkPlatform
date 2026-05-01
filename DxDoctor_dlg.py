from __future__ import annotations

from datetime import date, datetime, time

from PyQt6.QtCore import QDate, QLocale, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class DxDoctorDialog(QDialog):
    """Dialog กลางสำหรับเปิด visit — ใช้ร่วมทุก module"""

    def __init__(
        self,
        dx_code: str,
        doctor_options: list[tuple[str, str]],
        ovstist_options: list[tuple[str, str]],
        default_doctor_code: str,
        default_ovstist: str,
        icode_options: list[tuple[str, str, str]] | None = None,
        default_price_code: str = "",
        default_visit_date: date | None = None,
        visit_date_editable: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("เปิด Visit")
        self.setModal(True)
        self.resize(560, 280)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        en_locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        self.date_edit.setLocale(en_locale)
        cal = self.date_edit.calendarWidget()
        if cal is not None:
            cal.setLocale(en_locale)
        d = default_visit_date or date.today()
        self.date_edit.setDate(QDate(d.year, d.month, d.day))
        self.date_edit.setEnabled(visit_date_editable)

        self.dx_input = QLineEdit(dx_code)
        self.dx_input.setPlaceholderText("เช่น Z718")

        self.doctor_combo = QComboBox()
        for code, name in doctor_options:
            label = f"{code} - {name}" if name else code
            self.doctor_combo.addItem(label, code)
        if default_doctor_code:
            index = self.doctor_combo.findData(default_doctor_code)
            if index >= 0:
                self.doctor_combo.setCurrentIndex(index)

        self.ovstist_combo = QComboBox()
        for code, name in ovstist_options:
            label = f"{code} - {name}" if name else code
            self.ovstist_combo.addItem(label, code)
        if default_ovstist:
            index = self.ovstist_combo.findData(default_ovstist)
            if index >= 0:
                self.ovstist_combo.setCurrentIndex(index)

        self._icode_options: list[tuple[str, str, str]] = icode_options or []
        self._user_changed_price = False
        # ถ้า caller ส่ง default มา = ผู้ใช้เคยเลือกแล้ว, ใช้ค่านั้นและถือว่า "ผู้ใช้เลือกเอง"
        # ถ้าไม่ส่ง = เลือกอัตโนมัติตามวันที่ (ส-อ → "นอกเวลา", จ-ศ → "ในเวลา")
        if default_price_code:
            initial_price_code = default_price_code
            self._user_changed_price = True
        else:
            initial_price_code = self._auto_pick_price_code(d)
        self.price_combo = self._build_icode_combo(self._icode_options, initial_price_code)
        # connect signal *หลัง* ตั้ง initial เสร็จ — เพื่อไม่ให้ flag ถูก set ก่อนผู้ใช้จะแตะ
        self.price_combo.currentIndexChanged.connect(self._on_price_changed)
        line_edit = self.price_combo.lineEdit()
        if line_edit is not None:
            line_edit.textEdited.connect(self._on_price_changed)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        form = QFormLayout()
        form.addRow("วันที่ visit", self.date_edit)
        form.addRow("รหัสวินิจฉัยหลัก", self.dx_input)
        form.addRow("ผู้ให้บริการ (Doctor)", self.doctor_combo)
        form.addRow("ประเภทการมา", self.ovstist_combo)
        form.addRow("รหัสค่าบริการ", self.price_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _auto_pick_price_code(self, d: date) -> str:
        """เลือก icode ตามวัน+เวลา:
        - ส-อ → 'นอกเวลา'
        - จ-ศ และเวลา < 08:30 หรือ >= 16:30 → 'นอกเวลา'
        - อื่นๆ → 'ในเวลา'
        """
        if not self._icode_options:
            return ""
        now_t = datetime.now().time()
        is_after_hours = now_t < time(8, 30) or now_t >= time(16, 30)
        is_weekend = d.weekday() >= 5
        keyword = "นอกเวลา" if (is_weekend or is_after_hours) else "ในเวลา"
        for code, name, _price in self._icode_options:
            if keyword in name:
                return code
        # ไม่พบ keyword → fallback เป็น icode แรกในรายการ
        return self._icode_options[0][0]

    def _on_date_changed(self, qd: QDate) -> None:
        if self._user_changed_price:
            return
        d = date(qd.year(), qd.month(), qd.day())
        code = self._auto_pick_price_code(d)
        if not code:
            return
        # block signals เพื่อไม่ให้ trigger _on_price_changed
        self.price_combo.blockSignals(True)
        line_edit = self.price_combo.lineEdit()
        if line_edit is not None:
            line_edit.blockSignals(True)
        try:
            index = self.price_combo.findData(code)
            if index >= 0:
                self.price_combo.setCurrentIndex(index)
        finally:
            self.price_combo.blockSignals(False)
            if line_edit is not None:
                line_edit.blockSignals(False)

    def _on_price_changed(self, *_args) -> None:
        self._user_changed_price = True

    def _build_icode_combo(
        self, options: list[tuple[str, str, str]], default_code: str
    ) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        line_edit = combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText("ค้นหาด้วยรหัสหรือชื่อ (เช่น ถอดเล็บ)")
        for code, name, price in options:
            label = f"{code} - {name}"
            if price:
                label += f" ({price} บ.)"
            combo.addItem(label, code)
        completer = QCompleter(combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setModel(combo.model())
        combo.setCompleter(completer)

        if default_code:
            index = combo.findData(default_code)
            if index >= 0:
                combo.setCurrentIndex(index)
            elif line_edit is not None:
                line_edit.setText(default_code)
        return combo

    def _current_icode(self, combo: QComboBox) -> str:
        data = combo.currentData()
        if data:
            return str(data).strip()
        line_edit = combo.lineEdit()
        text = line_edit.text().strip() if line_edit is not None else combo.currentText().strip()
        return text.split(" ", 1)[0] if text else ""

    def values(self) -> tuple[date, str, str, str, str]:
        qd = self.date_edit.date()
        visit_date = date(qd.year(), qd.month(), qd.day())
        dx_code = self.dx_input.text().strip().upper()
        doctor_code = str(self.doctor_combo.currentData() or "").strip()
        ovstist_code = str(self.ovstist_combo.currentData() or "").strip()
        price_code = self._current_icode(self.price_combo)
        return visit_date, dx_code, doctor_code, ovstist_code, price_code
