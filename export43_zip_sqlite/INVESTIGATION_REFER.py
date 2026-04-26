# 43 แฟ้ม (SQLite/F43.db): INVESTIGATION_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_invest',
    'investcode',
    'investname',
    'datetime_report',
    'investvalue',
    'investresult',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "datetime_invest", "investcode", "investname", "datetime_report", "investvalue", "investresult", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "INVESTIGATION_REFER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
