from __future__ import annotations

from pathlib import Path

import pymysql
import pymysql.cursors

try:
    import psycopg2
except ImportError:  # psycopg2 is optional at import-time
    psycopg2 = None  # type: ignore[assignment]

from PyQt6.QtWidgets import (
    QComboBox,
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
from His_factory import reset_his
from Theme_helper import button_style, current_theme

DB_TYPE_MYSQL = "mysql"
DB_TYPE_POSTGRES = "postgres"

DEFAULT_PORT = {
    DB_TYPE_MYSQL: "3306",
    DB_TYPE_POSTGRES: "5432",
}


class DlgHisSetting(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.env_path = Path(__file__).with_name(".env")
        self.settings = get_settings()
        self.setWindowTitle("HIS Connection Setting")
        self.setModal(True)
        self.resize(460, 300)
        self._apply_theme()

        self.db_type_combo = QComboBox()
        self.db_type_combo.addItem("MySQL", DB_TYPE_MYSQL)
        self.db_type_combo.addItem("PostgreSQL", DB_TYPE_POSTGRES)
        self.db_type_combo.currentIndexChanged.connect(self._on_db_type_changed)

        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.database_input = QLineEdit()
        self.charset_input = QLineEdit()
        for field in (
            self.db_type_combo,
            self.host_input,
            self.port_input,
            self.user_input,
            self.password_input,
            self.database_input,
            self.charset_input,
        ):
            field.setMinimumHeight(38)

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Database Type", self.db_type_combo)
        self.form_layout.addRow("Host", self.host_input)
        self.form_layout.addRow("Port", self.port_input)
        self.form_layout.addRow("User", self.user_input)
        self.form_layout.addRow("Password", self.password_input)
        self.form_layout.addRow("Database", self.database_input)
        self._charset_label = "Charset"
        self.form_layout.addRow(self._charset_label, self.charset_input)

        self.test_button = QPushButton("ทดสอบการเชื่อมต่อ")
        self.test_button.setStyleSheet(button_style("primary"))
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
        layout.addLayout(self.form_layout)
        layout.addStretch(1)
        layout.addLayout(action_row)

        self.load_settings()

    def _apply_theme(self) -> None:
        theme = current_theme()
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {theme.window};
            }}
            QLabel {{
                color: {theme.text};
                font-weight: 600;
            }}
            QLineEdit, QComboBox {{
                background: {theme.surface};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {theme.primary};
            }}
            QDialogButtonBox QPushButton {{
                background: {theme.surface};
                color: {theme.primary};
                border: 1px solid {theme.border};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }}
            QDialogButtonBox QPushButton:hover {{
                background: {theme.surface_alt};
            }}
            """
        )

    # ------------------------------------------------------------------ helpers
    def _current_db_type(self) -> str:
        return str(self.db_type_combo.currentData() or DB_TYPE_MYSQL)

    def _set_db_type(self, db_type: str) -> None:
        target = (db_type or DB_TYPE_MYSQL).lower()
        if target in ("postgres", "postgresql", "pg"):
            target = DB_TYPE_POSTGRES
        else:
            target = DB_TYPE_MYSQL
        index = self.db_type_combo.findData(target)
        if index >= 0:
            self.db_type_combo.setCurrentIndex(index)

    def _on_db_type_changed(self) -> None:
        db_type = self._current_db_type()
        is_pg = db_type == DB_TYPE_POSTGRES

        # Toggle charset (MySQL-only field)
        charset_row = self.form_layout.labelForField(self.charset_input)
        self.charset_input.setVisible(not is_pg)
        if charset_row is not None:
            charset_row.setVisible(not is_pg)

        # Auto-fill default port when it still matches the other driver's default
        current_port = self.port_input.text().strip()
        other_default = DEFAULT_PORT[DB_TYPE_MYSQL if is_pg else DB_TYPE_POSTGRES]
        if not current_port or current_port == other_default:
            self.port_input.setText(DEFAULT_PORT[db_type])

    # ------------------------------------------------------------------ load/save
    def load_settings(self) -> None:
        env_values = load_env_defaults(self.env_path.parent)
        self._set_db_type(self._read_setting("DB_TYPE", env_values["DB_TYPE"]))
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
        self._on_db_type_changed()

    def _read_setting(self, key: str, default: str) -> str:
        return read_setting(key, default, self.env_path.parent)

    def _get_form_values(self) -> dict[str, str]:
        db_type = self._current_db_type()
        default_port = DEFAULT_PORT[db_type]
        return {
            "DB_TYPE": db_type,
            "DB_HOST": self.host_input.text().strip(),
            "DB_PORT": self.port_input.text().strip() or default_port,
            "DB_USER": self.user_input.text().strip(),
            "DB_PASSWORD": self.password_input.text(),
            "DB_NAME": self.database_input.text().strip(),
            "DB_CHARSET": self.charset_input.text().strip() or "utf8mb4",
        }

    def _validate(self) -> dict[str, str] | None:
        values = self._get_form_values()
        required_keys = ["DB_TYPE", "DB_HOST", "DB_PORT", "DB_USER", "DB_NAME"]
        if values["DB_TYPE"] == DB_TYPE_MYSQL:
            required_keys.append("DB_CHARSET")
        missing = [key for key in required_keys if not values[key]]
        if missing:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่ครบ",
                f"กรุณากรอกข้อมูลให้ครบ: {', '.join(missing)}",
            )
            return None

        try:
            int(values["DB_PORT"])
        except ValueError:
            QMessageBox.warning(self, "Port ไม่ถูกต้อง", "กรุณากรอก DB_PORT เป็นตัวเลข")
            return None

        return values

    # ------------------------------------------------------------------ actions
    def test_connection(self) -> None:
        values = self._validate()
        if values is None:
            return

        try:
            if values["DB_TYPE"] == DB_TYPE_POSTGRES:
                if psycopg2 is None:
                    raise RuntimeError(
                        "ไม่พบ psycopg2 (รัน `uv sync` หรือ `uv add psycopg2-binary`)"
                    )
                conn = psycopg2.connect(
                    host=values["DB_HOST"],
                    port=int(values["DB_PORT"]),
                    user=values["DB_USER"],
                    password=values["DB_PASSWORD"],
                    dbname=values["DB_NAME"],
                    connect_timeout=5,
                )
                hoscode = self._fetch_hoscode_pg(conn)
                conn.close()
            else:
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
                hoscode = self._fetch_hoscode_mysql(conn)
                conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"[SettingsDialog.test_connection] error: {exc}")
            QMessageBox.critical(
                self,
                "เชื่อมต่อไม่สำเร็จ",
                f"ไม่สามารถเชื่อมต่อ HIS ได้\n{exc}",
            )
            return

        if hoscode:
            self.settings.setValue("hoscode", hoscode)
            self.settings.sync()
            QMessageBox.information(
                self,
                "สำเร็จ",
                f"ทดสอบการเชื่อมต่อ HIS สำเร็จ\nรหัสหน่วยบริการ (hoscode): {hoscode}",
            )
        else:
            QMessageBox.information(self, "สำเร็จ", "ทดสอบการเชื่อมต่อ HIS สำเร็จ")

    def _fetch_hoscode_mysql(self, conn) -> str | None:
        """ดึงรหัสหน่วยบริการจากฐานข้อมูล MySQL (HOSxP/HOSxP_PCU)"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT hospitalcode AS hoscode FROM opdconfig LIMIT 1")
                row = cursor.fetchone()
                if row and "hoscode" in row:
                    return str(row["hoscode"]).strip()
        except Exception:  # noqa: BLE001
            pass
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT hospcode FROM hospital LIMIT 1")
                row = cursor.fetchone()
                if row and "hospcode" in row:
                    return str(row["hospcode"]).strip()
        except Exception:  # noqa: BLE001
            pass
        return None

    def _fetch_hoscode_pg(self, conn) -> str | None:
        """ดึงรหัสหน่วยบริการจากฐานข้อมูล PostgreSQL"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT hospitalcode AS hoscode FROM opdconfig LIMIT 1")
                row = cursor.fetchone()
                if row and row[0]:
                    return str(row[0]).strip()
        except Exception:  # noqa: BLE001
            pass
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT hospcode FROM hospital LIMIT 1")
                row = cursor.fetchone()
                if row and row[0]:
                    return str(row[0]).strip()
        except Exception:  # noqa: BLE001
            pass
        return None

    def save_settings(self) -> None:
        values = self._validate()
        if values is None:
            return

        save_settings(values)
        reset_his()
        self.accept()
