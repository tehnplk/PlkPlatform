# 43 แฟ้ม (SQLite/F43.db): DISABILITY
COLUMNS = [
    'hospcode',
    'disabid',
    'pid',
    'disabtype',
    'disabcause',
    'diagcode',
    'date_detect',
    'date_disab',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "disabid", "pid", "disabtype", "disabcause", "diagcode", "date_detect", "date_disab", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "DISABILITY"
WHERE "date_detect" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
