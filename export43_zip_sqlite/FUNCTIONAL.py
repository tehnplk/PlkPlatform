# 43 แฟ้ม (SQLite/F43.db): FUNCTIONAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'functional_test',
    'testresult',
    'dependent',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "functional_test", "testresult", "dependent", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "FUNCTIONAL"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
