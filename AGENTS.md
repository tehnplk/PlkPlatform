# AGENTS.md

## PlkPlatform Repo
ระบบ Utility จัดการ HIS (Hospital Information System utility)

## Agent Role
- You are a PyQt6 expert in Python.
- Act as an expert in PyQt6 with Python.

## Commands

| Task | Command |
|------|---------|
| Run application | `uv run start.py` |
| Build executable | `uv run --group dev pyinstaller PlkPlatform.spec` |
| Install deps | `uv sync` |
| Research tech stack | `npx ctx7 --help` |
| Query database | `db-cli --skill` |

## Codebase Style

- `ModuleName_logic.py` — business logic, database queries, controller classes
- `ModuleName_ui.py` — PyQt6 UI classes (QMainWindow, QWidget, QDialog)
- `ModuleName_dlg.py` — standalone dialog windows

UI messages and docstrings are in Thai.

## Architecture

**Entry point:** `start.py` → `Main_logic.main()` → `MainWindow(MainUI)`

`MainWindow` (`Main_logic.py`) inherits `MainUI` (`Main_ui.py`) and manages feature subwindows in a QMdiArea. Subwindows are created on-demand and cached:

```
MainWindow
├── BuddyCareExcel_logic.BuddyCareExcelWindow  — Excel/patient import
├── DataCenter_logic.DataCenterWindow          — API submission & Excel export
├── TelemedDaily_ui.TelemedDailyWindow         — Telemedicine daily (ZIP upload)
└── AutoUpdate_logic.AutoUpdateController      — Version checks & installer
```

**Database layer:**
- `His_lib.His2` — HOSxP / HOSxP_PCU on **MySQL** (pymysql)
- `His_lib_pg.His2Pg` — HOSxP on **PostgreSQL** (psycopg2). Uses parameterised queries per statement instead of MySQL session variables; assumes `get_serialnumber()` stored function exists.

Settings are loaded by `Setting_helper.py` with priority: QSettings (Windows registry) > `.env` > hardcoded defaults. Connection dialog is `HisSetting_dlg.py`.

**Threading:** QThread for background work; use `pyqtSignal` for async result delivery.

**UI theming:** `Main_ui.py` sets a frameless window (`FramelessWindowHint`) with a green/teal stylesheet. New subwindows should match.

## Database Credentials
Read `docs/hosxp.md`, `docs/hosxp_pcu.md`, or `docs/jhcis.md` for host/port/user/password/database per HIS vendor.

## Dependencies
- Runtime: PyQt6 ≥ 6.11, pandas ≥ 3.0, openpyxl ≥ 3.1, pymysql ≥ 1.1, psycopg2-binary ≥ 2.9.9, python-dotenv ≥ 1.2
- Dev (group `dev`): pyinstaller ≥ 6.20
- Python ≥ 3.12
