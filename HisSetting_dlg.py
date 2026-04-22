from __future__ import annotations

from pathlib import Path

import pymysql
import pymysql.cursors
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from Setting_helper import (
    get_settings,
    load_env_defaults,
    read_setting,
    save_settings,
)


class DlgHisSetting(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.env_path = Path(__file__).with_name(".env")
        self.settings = get_settings()
        self.setWindowTitle("HIS Connection Setting")
        self.setModal(True)
        self.resize(460, 260)

        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.database_input = QLineEdit()
        self.charset_input = QLineEdit()
        for field in (
            self.host_input,
            self.port_input,
            self.user_input,
            self.password_input,
            self.database_input,
            self.charset_input,
        ):
            field.setMinimumHeight(38)

        form_layout = QFormLayout()
        form_layout.addRow("Host", self.host_input)
        form_layout.addRow("Port", self.port_input)
        form_layout.addRow("User", self.user_input)
        form_layout.addRow("Password", self.password_input)
        form_layout.addRow("Database", self.database_input)
        form_layout.addRow("Charset", self.charset_input)

        self.test_button = QPushButton("ทดสอบการเชื่อมต่อ")
        self.test_button.clicked.connect(self.test_connection)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)

        action_row = QHBoxLayout()
        action_row.addWidget(self.test_button)
        action_row.addStretch(1)
        action_row.addWidget(button_box)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addStretch(1)
        layout.addLayout(action_row)

        self.load_settings()

    def load_settings(self) -> None:
        env_values = load_env_defaults(self.env_path.parent)
        self.host_input.setText(self._read_setting("DB_HOST", env_values["DB_HOST"]))
        self.port_input.setText(self._read_setting("DB_PORT", env_values["DB_PORT"]))
        self.user_input.setText(self._read_setting("DB_USER", env_values["DB_USER"]))
        self.password_input.setText(
            self._read_setting("DB_PASSWORD", env_values["DB_PASSWORD"])
        )
        self.database_input.setText(
            self._read_setting("DB_NAME", env_values["DB_NAME"])
        )
        self.charset_input.setText(
            self._read_setting("DB_CHARSET", env_values["DB_CHARSET"])
        )

    def _read_setting(self, key: str, default: str) -> str:
        return read_setting(key, default, self.env_path.parent)

    def _get_form_values(self) -> dict[str, str]:
        return {
            "DB_HOST": self.host_input.text().strip(),
            "DB_PORT": self.port_input.text().strip() or "3306",
            "DB_USER": self.user_input.text().strip(),
            "DB_PASSWORD": self.password_input.text(),
            "DB_NAME": self.database_input.text().strip(),
            "DB_CHARSET": self.charset_input.text().strip() or "utf8mb4",
        }

    def _validate(self) -> dict[str, str] | None:
        values = self._get_form_values()
        required_keys = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME", "DB_CHARSET"]
        missing = [key for key in required_keys if not values[key]]
        if missing:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่ครบ",
                f"กรุณากรอกค่าให้ครบ: {', '.join(missing)}",
            )
            return None

        try:
            int(values["DB_PORT"])
        except ValueError:
            QMessageBox.warning(self, "Port ไม่ถูกต้อง", "กรุณากรอก DB_PORT เป็นตัวเลข")
            return None

        return values

    def test_connection(self) -> None:
        values = self._validate()
        if values is None:
            return

        try:
            conn = pymysql.connect(
                host=values["DB_HOST"],
                port=int(values["DB_PORT"]),
                user=values["DB_USER"],
                password=values["DB_PASSWORD"],
                database=values["DB_NAME"],
                charset=values["DB_CHARSET"],
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5,
            )
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"[SettingsDialog.test_connection] error: {exc}")
            QMessageBox.critical(
                self,
                "เชื่อมต่อไม่สำเร็จ",
                f"ไม่สามารถเชื่อมต่อ HIS ได้\n{exc}",
            )
            return

        QMessageBox.information(self, "สำเร็จ", "ทดสอบการเชื่อมต่อ HIS สำเร็จ")

    def save_settings(self) -> None:
        values = self._validate()
        if values is None:
            return

        save_settings(values)
        self.accept()
