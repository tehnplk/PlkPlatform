# 43 แฟ้ม (SQLite/F43.db): PROCEDURE_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'procedcode',
    'timestart',
    'timefinish',
    'serviceprice',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "an", "datetime_admit", "wardstay", "procedcode", "timestart", "timefinish", "serviceprice", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "PROCEDURE_IPD"
WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
