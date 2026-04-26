# 43 แฟ้ม (SQLite/F43.db): DRUG_OPD
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'clinic',
    'didstd',
    'dname',
    'amount',
    'unit',
    'unit_packing',
    'drugprice',
    'drugcost',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "clinic", "didstd", "dname", "amount", "unit", "unit_packing", "drugprice", "drugcost", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "DRUG_OPD"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
