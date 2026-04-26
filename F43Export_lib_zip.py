"""F43Export ZIP Source Registry — โหลด COLUMNS + SQL จาก export43_zip_sqlite/{NAME}.py

ใช้สำหรับ source = "zip" — query F43.db (SQLite) ที่ import มาจาก ZIP
"""
from __future__ import annotations

import importlib

import export43_zip_sqlite

QUERIES_ZIP: dict[str, tuple[list[str], str]] = {}

for name in export43_zip_sqlite.ALL_FILES:
    module = importlib.import_module(f"export43_zip_sqlite.{name}")
    columns = getattr(module, "COLUMNS", None)
    sql = getattr(module, "SQL", None)
    if columns is None or sql is None:
        continue
    QUERIES_ZIP[name.upper()] = (columns, sql)
