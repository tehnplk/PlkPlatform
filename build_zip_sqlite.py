"""Generator: สร้าง export43_zip_sqlite/{NAME}.py สำหรับทุกตารางใน F43.db

ใช้ pattern filter:
- date_serv → WHERE date_serv BETWEEN ? AND ? + (? = '' OR seq IN ...) ถ้ามี seq
- datetime_admit → WHERE datetime_admit BETWEEN ?14char AND ?14char + ovstist filter ผ่าน SERVICE
- pid only (PERSON-linked) → WHERE pid IN (SELECT pid FROM SERVICE filter)
- เนื้อหาอื่นๆ (refer/policy/etc) → no filter (4 placeholder no-op)

placeholder: 4 ตัว (date_from, date_to, ovstist, ovstist) เหมือน export43/
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = Path(__file__).parent / "export43_zip_sqlite"
OUT_DIR.mkdir(exist_ok=True)
DB_PATH = Path(__file__).parent / "F43.db"

DATE_SERV_TABLES = set()       # มี date_serv (8-char YYYYMMDD)
DATETIME_ADMIT_TABLES = set()  # มี datetime_admit (14-char)
PID_TABLES = set()             # มี pid + seq → join SERVICE
PID_ONLY_TABLES = set()        # มี pid แต่ไม่มี seq → person-linked
NO_DATE_TABLES = set()         # ไม่มี date / pid → no filter

# ตารางพิเศษ filter ผ่านวันที่อื่น
SPECIAL_DATE_COL = {
    "ACCIDENT": "datetime_serv",
    "CHRONIC": "date_diag",
    "DRUGALLERGY": "daterecord",
    "DEATH": "ddeath",
    "NEWBORN": "bdate",
    "LABOR": "bdate",
    "DISABILITY": "date_detect",
    "PRENATAL": "lmp",
}


def build_sql(name: str, cols: list[str]) -> str:
    has_date_serv = "date_serv" in cols
    has_datetime_admit = "datetime_admit" in cols
    has_pid = "pid" in cols
    has_seq = "seq" in cols
    special_date = SPECIAL_DATE_COL.get(name)

    # d_update ที่ว่าง → fallback เป็น strftime ปัจจุบัน (YYYYMMDDHHMMSS)
    def _col_expr(c: str) -> str:
        if c == "d_update":
            return (
                "COALESCE(NULLIF(\"d_update\", ''), "
                "strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS \"d_update\""
            )
        return f'"{c}"'

    col_list = ", ".join(_col_expr(c) for c in cols)
    select = f'SELECT {col_list} FROM "{name}"'

    # 1) มี date_serv → กรองด้วย date_serv + ovstist ผ่าน SERVICE (ถ้ามี seq)
    if has_date_serv and name == "SERVICE":
        return (
            f'{select}\n'
            'WHERE "date_serv" BETWEEN ? AND ?\n'
            '  AND (? = \'\' OR CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER))\n'
        )
    if has_date_serv and has_seq:
        return (
            f'{select}\n'
            'WHERE "date_serv" BETWEEN ? AND ?\n'
            '  AND (? = \'\' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER)))\n'
        )
    if has_date_serv:
        return (
            f'{select}\n'
            'WHERE "date_serv" BETWEEN ? AND ?\n'
            '  AND (? = \'\' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER)))\n'
        )

    # 2) datetime_admit (14-char) → SUBSTR(1..8) เปรียบเทียบช่วงวัน
    if has_datetime_admit:
        return (
            f'{select}\n'
            'WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?\n'
            '  AND (? = \'\' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER)))\n'
        )

    # 3) special date column (ddeath, bdate, etc.)
    if special_date and special_date in cols:
        return (
            f'{select}\n'
            f'WHERE "{special_date}" BETWEEN ? AND ?\n'
            '  AND (? = \'\' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER)))\n'
        )

    # 4) มี pid แต่ไม่มี date column → person-linked filter ผ่าน SERVICE date+typein
    if has_pid:
        return (
            f'{select}\n'
            'WHERE "pid" IN (\n'
            '  SELECT DISTINCT "pid" FROM "SERVICE"\n'
            '  WHERE "date_serv" BETWEEN ? AND ?\n'
            '    AND (? = \'\' OR CAST(NULLIF("typein", \'\') AS INTEGER) = CAST(? AS INTEGER))\n'
            ')\n'
        )

    # 5) no date / no pid (refer/policy/village/community_activity/data_correct/provider) → no filter
    return f'{select}\nWHERE ? = ? OR ? = ?  -- no real filter\n'


def main() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} ไม่พบ — รัน build_f43_db.py ก่อน")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    tables = sorted(
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    )
    # __init__.py is written at end with ALL_FILES manifest (frozen-friendly)

    for name in tables:
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]
        if not cols:
            continue
        sql = build_sql(name, cols)
        cols_repr = "[\n    " + ",\n    ".join(repr(c) for c in cols) + ",\n]"
        text = (
            f"# 43 แฟ้ม (SQLite/F43.db): {name}\n"
            f"COLUMNS = {cols_repr}\n\n"
            f'SQL = """\n{sql}"""\n'
        )
        (OUT_DIR / f"{name}.py").write_text(text, encoding="utf-8")
        print(f"wrote {name} ({len(cols)} cols)")

    # write manifest
    with open(OUT_DIR / "__init__.py", "w", encoding="utf-8") as f:
        f.write("# Auto-generated manifest — รายการ submodule ทั้งหมด (frozen-friendly)\n")
        f.write(f"ALL_FILES = {sorted(tables)!r}\n")

    conn.close()
    print(f"\n{len(tables)} files in {OUT_DIR}")


if __name__ == "__main__":
    main()
