# 43 แฟ้ม (SQLite/F43.db): WOMEN
COLUMNS = [
    'hospcode',
    'pid',
    'fptype',
    'nofpcause',
    'totalson',
    'numberson',
    'abortion',
    'stillbirth',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "fptype", "nofpcause", "totalson", "numberson", "abortion", "stillbirth", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "WOMEN"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
