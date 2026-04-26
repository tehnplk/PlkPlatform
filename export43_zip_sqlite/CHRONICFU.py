# 43 แฟ้ม (SQLite/F43.db): CHRONICFU
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'weight',
    'height',
    'waist_cm',
    'sbp',
    'dbp',
    'foot',
    'retina',
    'provider',
    'd_update',
    'chronicfuplace',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "weight", "height", "waist_cm", "sbp", "dbp", "foot", "retina", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "chronicfuplace", "cid" FROM "CHRONICFU"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
