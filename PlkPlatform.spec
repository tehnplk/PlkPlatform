# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — รวม:
- ไฟล์ data: icon.ico/png, mysql_visit_type_count.sql, F43.db
- โมดูล plug-in ที่โหลดด้วย pkgutil.iter_modules (export43, export43_zip_sqlite)
- Hidden imports ของ pymysql/sqlite3/PyQt6 ที่ PyInstaller บางครั้งไม่ detect
"""
from PyInstaller.utils.hooks import collect_submodules


# โมดูลใน export43/ และ export43_zip_sqlite/ โหลดแบบ dynamic ผ่าน pkgutil
# จึงต้องบอก PyInstaller ให้บรรจุทุก submodule ด้วย
hidden_export43 = collect_submodules('export43')
hidden_export43_zip = collect_submodules('export43_zip_sqlite')

a = Analysis(
    ['start.py'],
    pathex=[],
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
