# 43 แฟ้ม (SQLite/F43.db): CARD
COLUMNS = [
    'hospcode',
    'pid',
    'instype_old',
    'instype_new',
    'insid',
    'startdate',
    'expiredate',
    'main',
    'sub',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "instype_old", "instype_new", "insid", "startdate", "expiredate", "main", "sub", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "CARD"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
