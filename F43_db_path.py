"""F43_db_path — resolve path ของ F43.db ให้ได้ตำแหน่ง writable

Dev mode  : <project>/F43.db (ไฟล์ในโปรเจกต์)
Frozen exe: <exe_dir>/F43.db (ข้าง PlkPlatform.exe — writable)

ครั้งแรกที่รัน: ถ้า F43.db ที่ writable ยังไม่มี ให้ copy template จาก bundle (_MEIPASS)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_writable_db_path() -> Path:
    """Path ของ F43.db ที่ใช้ runtime (writable)"""
    if is_frozen():
        # ข้าง .exe — user-writable เมื่อ exe อยู่ใน folder ปกติ (ไม่ใช่ Program Files)
        return Path(sys.executable).resolve().parent / "F43.db"
    # Dev mode: ในโปรเจกต์
    return Path(__file__).resolve().parent / "F43.db"


def get_template_db_path() -> Path:
    """Path ของ F43.db template ที่ bundled มาใน frozen exe (อยู่ใน _MEIPASS)"""
    if is_frozen():
        meipass = Path(getattr(sys, "_MEIPASS", "."))
        return meipass / "F43.db"
    return Path(__file__).resolve().parent / "F43.db"


def ensure_db_exists() -> Path:
    """รับประกันว่ามี F43.db ที่ writable — ถ้ายังไม่มี copy จาก template"""
    target = get_writable_db_path()
    if target.exists():
        return target
    template = get_template_db_path()
    if template.exists() and template.resolve() != target.resolve():
        shutil.copy2(template, target)
    return target


F43_DB_PATH = ensure_db_exists()
