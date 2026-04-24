"""Factory that returns the right HIS connector based on DB_TYPE setting.

Kept in a separate module so importing `His_lib` (pymysql) does not force
`psycopg2` to be loaded, and vice versa.
"""
from __future__ import annotations

from Setting_helper import read_setting

_his_instance = None


def _resolve_db_type() -> str:
    db_type = (read_setting("DB_TYPE", "mysql") or "mysql").strip().lower()
    if db_type in ("postgres", "postgresql", "pg"):
        return "postgres"
    return "mysql"


def make_his(reset: bool = False):
    """Return a connected HIS instance (His2 or His2Pg) for the current DB_TYPE.

    The returned object is cached (singleton). Use reset=True to force a new connection.
    """
    global _his_instance
    if reset:
        _his_instance = None

    if _his_instance is None:
        if _resolve_db_type() == "postgres":
            from His_lib_pg import His2Pg
            _his_instance = His2Pg()
        else:
            from His_lib import His2
            _his_instance = His2()

    return _his_instance


def reset_his():
    """Clear the cached HIS instance so the next make_his() creates a new one."""
    global _his_instance
    _his_instance = None
