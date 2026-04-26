"""F43 Queries registry — โหลด COLUMNS + SQL ของแต่ละแฟ้มจาก export43/{NAME}.py

ใช้ ALL_FILES manifest ใน export43/__init__.py (frozen-friendly)
ปฏิบัติการ: เพิ่ม/แก้แฟ้มใดๆ ให้แก้ไฟล์ใน export43/{NAME}.py โดยตรง
แล้วรัน build_zip_sqlite.py เพื่อ regenerate __init__.py manifest
"""
from __future__ import annotations

import importlib

import export43

QUERIES: dict[str, tuple[list[str], str]] = {}

for name in export43.ALL_FILES:
    module = importlib.import_module(f"export43.{name}")
    columns = getattr(module, "COLUMNS", None)
    sql = getattr(module, "SQL", None)
    if columns is None or sql is None:
        continue
    QUERIES[name.upper()] = (columns, sql)
