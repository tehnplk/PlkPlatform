# 43 แฟ้ม (SQLite/F43.db): CHARGE_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'chargeitem',
    'chargelist',
    'quantity',
    'instype',
    'cost',
    'price',
    'payprice',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "an", "datetime_admit", "wardstay", "chargeitem", "chargelist", "quantity", "instype", "cost", "price", "payprice", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "CHARGE_IPD"
WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
