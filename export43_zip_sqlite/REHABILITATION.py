# 43 แฟ้ม (SQLite/F43.db): REHABILITATION
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'an',
    'date_admit',
    'date_serv',
    'date_start',
    'date_finish',
    'rehabcode',
    'at_device',
    'at_no',
    'rehabplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "an", "date_admit", "date_serv", "date_start", "date_finish", "rehabcode", "at_device", "at_no", "rehabplace", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "REHABILITATION"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
