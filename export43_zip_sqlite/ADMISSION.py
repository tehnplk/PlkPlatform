# 43 แฟ้ม (SQLite/F43.db): ADMISSION
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'an',
    'datetime_admit',
    'wardadmit',
    'instype',
    'typein',
    'referinhosp',
    'causein',
    'admitweight',
    'admitheight',
    'datetime_disch',
    'warddisch',
    'dischstatus',
    'dischtype',
    'referouthosp',
    'causeout',
    'cost',
    'price',
    'payprice',
    'actualpay',
    'provider',
    'd_update',
    'drg',
    'rw',
    'adjrw',
    'error',
    'warning',
    'actlos',
    'grouper_version',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "an", "datetime_admit", "wardadmit", "instype", "typein", "referinhosp", "causein", "admitweight", "admitheight", "datetime_disch", "warddisch", "dischstatus", "dischtype", "referouthosp", "causeout", "cost", "price", "payprice", "actualpay", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "drg", "rw", "adjrw", "error", "warning", "actlos", "grouper_version", "cid" FROM "ADMISSION"
WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
