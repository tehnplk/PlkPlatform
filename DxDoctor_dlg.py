from __future__ import annotations

from datetime import date, datetime, time

from PyQt6.QtCore import QDate, QLocale, QStringListModel, Qt
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

        self.doctor_input = self._build_doctor_input(doctor_options, default_doctor_code)

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
        self.price_input = self._build_icode_input(self._icode_options, initial_price_code)
        # connect signal *หลัง* ตั้ง initial เสร็จ — เพื่อไม่ให้ flag ถูก set ก่อนผู้ใช้จะแตะ
        self.price_input.textEdited.connect(self._on_price_changed)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        form = QFormLayout()
        form.addRow("วันที่ visit", self.date_edit)
        form.addRow("รหัสวินิจฉัยหลัก", self.dx_input)
        form.addRow("ผู้ให้บริการ (Doctor)", self.doctor_input)
        form.addRow("ประเภทการมา", self.ovstist_combo)
        form.addRow("รหัสค่าบริการ", self.price_input)

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
        self.price_input.blockSignals(True)
        try:
            self.price_input.setText(self._icode_code_to_label.get(code, code))
        finally:
            self.price_input.blockSignals(False)

    def _on_price_changed(self, *_args) -> None:
        self._user_changed_price = True

    def _build_icode_input(
        self, options: list[tuple[str, str, str]], default_code: str
    ) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("ค้นหาด้วยรหัสหรือชื่อ (เช่น ถอดเล็บ)")

        self._icode_label_to_code: dict[str, str] = {}
        self._icode_code_to_label: dict[str, str] = {}
        labels: list[str] = []
        for code, name, price in options:
            label = f"{code} - {name}"
            if price:
                label += f" ({price} บ.)"
            labels.append(label)
            self._icode_label_to_code[label] = code
            self._icode_code_to_label[code] = label

        self._icode_model = QStringListModel(labels, self)
        completer = QCompleter(self._icode_model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        line_edit.setCompleter(completer)
        self._icode_completer = completer

        if default_code:
            line_edit.setText(self._icode_code_to_label.get(default_code, default_code))
        return line_edit

    def _build_doctor_input(
        self, options: list[tuple[str, str]], default_code: str
    ) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("ค้นหาด้วยรหัสหรือชื่อ Doctor")

        self._doctor_label_to_code: dict[str, str] = {}
        self._doctor_code_to_label: dict[str, str] = {}
        labels: list[str] = []
        for code, name in options:
            label = f"{code} - {name}" if name else code
            labels.append(label)
            self._doctor_label_to_code[label] = code
            self._doctor_code_to_label[code] = label

        self._doctor_model = QStringListModel(labels, self)
        self._doctor_completer = QCompleter(self._doctor_model, self)
        self._doctor_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._doctor_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._doctor_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        line_edit.setCompleter(self._doctor_completer)

        if default_code:
            line_edit.setText(self._doctor_code_to_label.get(default_code, default_code))
        return line_edit

    def _current_doctor_code(self) -> str:
        text = self.doctor_input.text().strip()
        if not text:
            return ""
        code = self._doctor_label_to_code.get(text)
        if code:
            return code.strip()
        return text.split(" ", 1)[0].strip()

    def _current_icode(self) -> str:
        text = self.price_input.text().strip()
        if not text:
            return ""
        code = self._icode_label_to_code.get(text)
        if code:
            return code.strip()
        return text.split(" ", 1)[0] if text else ""

    def values(self) -> tuple[date, str, str, str, str]:
        qd = self.date_edit.date()
        visit_date = date(qd.year(), qd.month(), qd.day())
        dx_code = self.dx_input.text().strip().upper()
        doctor_code = self._current_doctor_code()
        ovstist_code = str(self.ovstist_combo.currentData() or "").strip()
        price_code = self._current_icode()
        return visit_date, dx_code, doctor_code, ovstist_code, price_code
