"""สร้าง F43.db (SQLite) — ตาราง 52 แฟ้ม โครงสร้างตาม temp.tmp_exp_3092_*
สำหรับจัดเก็บข้อมูลตอน import จาก ZIP 43 แฟ้ม
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pymysql

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path(__file__).parent / "F43.db"
TEMP_PREFIX = "tmp_exp_3093_"


def main() -> None:
    src = pymysql.connect(
        host="localhost", port=3306, user="root", password="112233",
        database="temp", charset="utf8mb4",
    )

    if DB_PATH.exists():
        DB_PATH.unlink()

    dst = sqlite3.connect(DB_PATH)
    dst.execute("PRAGMA journal_mode=WAL")

    with src.cursor() as cur:
        cur.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
            "FROM information_schema.columns "
            "WHERE table_schema='temp' AND table_name LIKE 'tmp_exp_3093\\_%' ESCAPE '\\\\' "
            "ORDER BY TABLE_NAME, ORDINAL_POSITION"
        )
        rows = cur.fetchall()

    # group by table
    tables: dict[str, list[tuple[str, int]]] = {}
    for tbl, col, dtype, length in rows:
        name = tbl[len(TEMP_PREFIX):].upper()
        tables.setdefault(name, []).append((col, length or 0))

    for name, cols in sorted(tables.items()):
        col_defs = ", ".join(f'"{c}" TEXT' for c, _ in cols)
        dst.execute(f'CREATE TABLE "{name}" ({col_defs})')
        print(f"created {name}: {len(cols)} cols")

    dst.commit()
    dst.close()
    src.close()
    print(f"\nF43.db created at {DB_PATH} with {len(tables)} tables")


if __name__ == "__main__":
    main()
