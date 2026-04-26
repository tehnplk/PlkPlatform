# 43 แฟ้ม (SQLite/F43.db): PROCEDURE_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'timestart',
    'timefinish',
    'procedurename',
    'procedcode',
    'pdescription',
    'procedresult',
    'provider',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "timestart", "timefinish", "procedurename", "procedcode", "pdescription", "procedresult", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "PROCEDURE_REFER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
