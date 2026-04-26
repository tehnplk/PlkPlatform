# 43 แฟ้ม (SQLite/F43.db): LABOR
COLUMNS = [
    'hospcode',
    'pid',
    'gravida',
    'lmp',
    'edc',
    'bdate',
    'bresult',
    'bplace',
    'bhosp',
    'btype',
    'bdoctor',
    'lborn',
    'sborn',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "gravida", "lmp", "edc", "bdate", "bresult", "bplace", "bhosp", "btype", "bdoctor", "lborn", "sborn", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "LABOR"
WHERE "bdate" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
