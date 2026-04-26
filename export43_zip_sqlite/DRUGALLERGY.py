# 43 แฟ้ม (SQLite/F43.db): DRUGALLERGY
COLUMNS = [
    'hospcode',
    'pid',
    'daterecord',
    'drugallergy',
    'dname',
    'typedx',
    'alevel',
    'symptom',
    'informant',
    'informhosp',
    'd_update',
    'provider',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "daterecord", "drugallergy", "dname", "typedx", "alevel", "symptom", "informant", "informhosp", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "provider", "cid" FROM "DRUGALLERGY"
WHERE "daterecord" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
