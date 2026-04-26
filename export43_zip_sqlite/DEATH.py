# 43 แฟ้ม (SQLite/F43.db): DEATH
COLUMNS = [
    'hospcode',
    'pid',
    'hospdeath',
    'an',
    'seq',
    'ddeath',
    'cdeath_a',
    'cdeath_b',
    'cdeath_c',
    'cdeath_d',
    'odisease',
    'cdeath',
    'pregdeath',
    'pdeath',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "hospdeath", "an", "seq", "ddeath", "cdeath_a", "cdeath_b", "cdeath_c", "cdeath_d", "odisease", "cdeath", "pregdeath", "pdeath", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "DEATH"
WHERE "ddeath" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
