# 43 แฟ้ม (SQLite/F43.db): NCDSCREEN
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'servplace',
    'smoke',
    'alcohol',
    'dmfamily',
    'htfamily',
    'weight',
    'height',
    'waist_cm',
    'sbp_1',
    'dbp_1',
    'sbp_2',
    'dbp_2',
    'bslevel',
    'bstest',
    'screenplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "servplace", "smoke", "alcohol", "dmfamily", "htfamily", "weight", "height", "waist_cm", "sbp_1", "dbp_1", "sbp_2", "dbp_2", "bslevel", "bstest", "screenplace", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "NCDSCREEN"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
