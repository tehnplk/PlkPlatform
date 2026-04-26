# 43 แฟ้ม (SQLite/F43.db): REFER_RESULT
COLUMNS = [
    'hospcode',
    'referid_source',
    'referid_province',
    'hosp_source',
    'refer_result',
    'datetime_in',
    'pid_in',
    'an_in',
    'reason',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid_source", "referid_province", "hosp_source", "refer_result", "datetime_in", "pid_in", "an_in", "reason", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "REFER_RESULT"
WHERE ? = ? OR ? = ?  -- no real filter
"""
