# 43 แฟ้ม (SQLite/F43.db): CHARGE_OPD
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'clinic',
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
SELECT "hospcode", "pid", "seq", "date_serv", "clinic", "chargeitem", "chargelist", "quantity", "instype", "cost", "price", "payprice", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "CHARGE_OPD"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
