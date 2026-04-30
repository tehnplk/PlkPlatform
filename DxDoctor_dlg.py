from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class DxDoctorDialog(QDialog):
    def __init__(
        self,
        dx_code: str,
        doctor_options: list[tuple[str, str]],
        ovstist_options: list[tuple[str, str]],
        default_doctor_code: str,
        default_ovstist: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ระบุรหัสวินิจฉัย")
        self.setModal(True)
        self.resize(460, 180)

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

        form = QFormLayout()
        form.addRow("รหัสวินิจฉัย", self.dx_input)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("ประเภทการมา", self.ovstist_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str]:
        dx_code = self.dx_input.text().strip().upper()
        doctor_code = str(self.doctor_combo.currentData() or "").strip()
        ovstist_code = str(self.ovstist_combo.currentData() or "").strip()
        return dx_code, doctor_code, ovstist_code
