# 43 แฟ้ม (SQLite/F43.db): POSTNATAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'gravida',
    'bdate',
    'ppcare',
    'ppplace',
    'ppresult',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "gravida", "bdate", "ppcare", "ppplace", "ppresult", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "POSTNATAL"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
