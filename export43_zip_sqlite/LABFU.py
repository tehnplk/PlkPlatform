# 43 แฟ้ม (SQLite/F43.db): LABFU
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'labtest',
    'labresult',
    'd_update',
    'labplace',
    'cid',
    'provider',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "labtest", "labresult", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "labplace", "cid", "provider" FROM "LABFU"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
