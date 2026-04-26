# 43 แฟ้ม (SQLite/F43.db): APPOINTMENT
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'seq',
    'date_serv',
    'clinic',
    'apdate',
    'aptype',
    'apdiag',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "an", "seq", "date_serv", "clinic", "apdate", "aptype", "apdiag", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "APPOINTMENT"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
