# 43 แฟ้ม (SQLite/F43.db): DRUG_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'typedrug',
    'didstd',
    'dname',
    'datestart',
    'datefinish',
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
SELECT "hospcode", "pid", "an", "datetime_admit", "wardstay", "typedrug", "didstd", "dname", "datestart", "datefinish", "amount", "unit", "unit_packing", "drugprice", "drugcost", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "DRUG_IPD"
WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
