# 43 แฟ้ม (SQLite/F43.db): CHRONIC
COLUMNS = [
    'hospcode',
    'pid',
    'date_diag',
    'chronic',
    'hosp_dx',
    'hosp_rx',
    'date_disch',
    'typedisch',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "date_diag", "chronic", "hosp_dx", "hosp_rx", "date_disch", "typedisch", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "CHRONIC"
WHERE "date_diag" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
