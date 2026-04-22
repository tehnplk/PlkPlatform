from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values

try:
    from PyQt6.QtCore import QSettings
except ImportError:  # pragma: no cover
    from PyQt5.QtCore import QSettings

SETTINGS_NAME = "PlkPlatformSetting"
SETTINGS_APP = "PlkPlatformSetting"


def get_settings() -> QSettings:
    return QSettings(SETTINGS_NAME, SETTINGS_APP)


def load_env_defaults(base_path: Path | None = None) -> dict[str, str]:
    env_path = (base_path or Path(__file__).resolve().parent) / ".env"
    env_values = dotenv_values(env_path) if env_path.exists() else {}
    return {
        "DB_HOST": str(env_values.get("DB_HOST", "") or ""),
        "DB_PORT": str(env_values.get("DB_PORT", "3306") or "3306"),
        "DB_USER": str(env_values.get("DB_USER", "") or ""),
        "DB_PASSWORD": str(env_values.get("DB_PASSWORD", "") or ""),
        "DB_NAME": str(env_values.get("DB_NAME", "") or ""),
        "DB_CHARSET": str(env_values.get("DB_CHARSET", "utf8mb4") or "utf8mb4"),
        "HIS_VENDOR": str(env_values.get("HIS_VENDOR", "hosxp_pcu") or "hosxp_pcu"),
    }


def read_setting(key: str, default: str = "", base_path: Path | None = None) -> str:
    env_defaults = load_env_defaults(base_path)
    settings = get_settings()
    fallback = env_defaults.get(key, default)
    value = settings.value(key, fallback)
    return str(value or fallback)


def load_db_settings(base_path: Path | None = None) -> dict[str, str | int]:
    return {
        "host": read_setting("DB_HOST", base_path=base_path),
        "port": int(read_setting("DB_PORT", "3306", base_path=base_path)),
        "user": read_setting("DB_USER", base_path=base_path),
        "password": read_setting("DB_PASSWORD", base_path=base_path),
        "database": read_setting("DB_NAME", base_path=base_path),
        "charset": read_setting("DB_CHARSET", "utf8mb4", base_path=base_path),
    }


def load_his_settings(base_path: Path | None = None) -> dict[str, str | int]:
    db_settings = load_db_settings(base_path)
    db_settings["his"] = read_setting("HIS_VENDOR", "hosxp_pcu", base_path=base_path)
    return db_settings


def save_settings(values: dict[str, str]) -> None:
    settings = get_settings()
    for key, value in values.items():
        settings.setValue(key, value)
    settings.sync()
