"""F43 Queries registry — โหลด COLUMNS + SQL ของแต่ละแฟ้มจาก export43/{NAME}.py

ปฏิบัติการ: เพิ่ม/แก้แฟ้มใดๆ ให้แก้ไฟล์ใน export43/{NAME}.py โดยตรง
ไม่ต้องแก้ไฟล์นี้
"""
from __future__ import annotations

import importlib
import pkgutil

import export43

# ค้นหา submodule ทั้งหมดใน export43/
QUERIES: dict[str, tuple[list[str], str]] = {}

for module_info in pkgutil.iter_modules(export43.__path__):
    module = importlib.import_module(f"export43.{module_info.name}")
    columns = getattr(module, "COLUMNS", None)
    sql = getattr(module, "SQL", None)
    if columns is None or sql is None:
        continue
    QUERIES[module_info.name.upper()] = (columns, sql)
