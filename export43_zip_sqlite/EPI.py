# 43 แฟ้ม (SQLite/F43.db): EPI
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'vaccinetype',
    'vaccineplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "vaccinetype", "vaccineplace", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "EPI"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
