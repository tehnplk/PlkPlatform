# 43 แฟ้ม (SQLite/F43.db): NEWBORN
COLUMNS = [
    'hospcode',
    'pid',
    'mpid',
    'gravida',
    'ga',
    'bdate',
    'btime',
    'bplace',
    'bhosp',
    'birthno',
    'btype',
    'bdoctor',
    'bweight',
    'asphyxia',
    'vitk',
    'tsh',
    'tshresult',
    'd_update',
    'cid',
    'length',
    'headcircum',
]

SQL = """
SELECT "hospcode", "pid", "mpid", "gravida", "ga", "bdate", "btime", "bplace", "bhosp", "birthno", "btype", "bdoctor", "bweight", "asphyxia", "vitk", "tsh", "tshresult", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid", "length", "headcircum" FROM "NEWBORN"
WHERE "bdate" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
