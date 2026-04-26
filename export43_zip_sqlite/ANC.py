# 43 แฟ้ม (SQLite/F43.db): ANC
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'gravida',
    'ancno',
    'ga',
    'ancresult',
    'ancplace',
    'provider',
    'd_update',
    'cid',
    'weight',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "gravida", "ancno", "ga", "ancresult", "ancplace", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid", "weight" FROM "ANC"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
