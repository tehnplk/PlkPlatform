# 43 แฟ้ม (SQLite/F43.db): NEWBORNCARE
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'bdate',
    'bcare',
    'bcplace',
    'bcareresult',
    'food',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "bdate", "bcare", "bcplace", "bcareresult", "food", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "NEWBORNCARE"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
