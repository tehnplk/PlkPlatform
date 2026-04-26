# 43 แฟ้ม (SQLite/F43.db): ICF
COLUMNS = [
    'hospcode',
    'disabid',
    'pid',
    'seq',
    'date_serv',
    'icf',
    'qualifier',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "disabid", "pid", "seq", "date_serv", "icf", "qualifier", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "ICF"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
