# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — รวม:
- ไฟล์ data: icon.ico/png, mysql_visit_type_count.sql, F43.db
- โมดูล plug-in ที่โหลดด้วย pkgutil.iter_modules (export43, export43_zip_sqlite)
- Hidden imports ของ pymysql/sqlite3/PyQt6 ที่ PyInstaller บางครั้งไม่ detect
"""
import os
from PyInstaller.utils.hooks import collect_submodules


# โมดูลใน export43/ และ export43_zip_sqlite/ — บรรจุทั้ง package เป็นทั้ง hiddenimports
# (รวมเข้า .pyz) และ datas (รวมเป็นไฟล์ในโฟลเดอร์ — เพื่อให้ __path__ ใช้งานได้)
hidden_export43 = collect_submodules('export43')
hidden_export43_zip = collect_submodules('export43_zip_sqlite')

# กำหนด explicit module list ให้ Analysis เห็นทุกตัว
explicit_export43 = [
    f'export43.{n[:-3]}'
    for n in os.listdir('export43')
    if n.endswith('.py') and n != '__init__.py'
]
explicit_export43_zip = [
    f'export43_zip_sqlite.{n[:-3]}'
    for n in os.listdir('export43_zip_sqlite')
    if n.endswith('.py') and n != '__init__.py'
]

a = Analysis(
    ['start.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('mysql_visit_type_count.sql', '.'),
        ('F43.db', '.'),
    ],
    hiddenimports=[
        *hidden_export43,
        *hidden_export43_zip,
        *explicit_export43,
        *explicit_export43_zip,
        'pymysql',
        'pymysql.cursors',
        'pymysql.connections',
        'pymysql.constants.CLIENT',
        'sqlite3',
        'pkgutil',
        'importlib',
        'F43_db_path',
        'F43Import_dlg',
        'F43Export_lib',
        'F43Export_lib_zip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'tkinter', 'matplotlib', 'IPython', 'jupyter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PlkPlatform',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    icon='icon.ico',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
