# 43 แฟ้ม (SQLite/F43.db): SERVICE
COLUMNS = [
    'hospcode',
    'pid',
    'hn',
    'seq',
    'date_serv',
    'time_serv',
    'location',
    'intime',
    'instype',
    'insid',
    'main',
    'typein',
    'referinhosp',
    'causein',
    'chiefcomp',
    'servplace',
    'btemp',
    'sbp',
    'dbp',
    'pr',
    'rr',
    'typeout',
    'referouthosp',
    'causeout',
    'cost',
    'price',
    'payprice',
    'actualpay',
    'd_update',
    'hsub',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "hn", "seq", "date_serv", "time_serv", "location", "intime", "instype", "insid", "main", "typein", "referinhosp", "causein", "chiefcomp", "servplace", "btemp", "sbp", "dbp", "pr", "rr", "typeout", "referouthosp", "causeout", "cost", "price", "payprice", "actualpay", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "hsub", "cid" FROM "SERVICE"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
"""
