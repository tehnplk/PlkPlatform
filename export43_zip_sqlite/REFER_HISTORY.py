# 43 แฟ้ม (SQLite/F43.db): REFER_HISTORY
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'pid',
    'seq',
    'an',
    'referid_origin',
    'hospcode_origin',
    'datetime_serv',
    'datetime_admit',
    'datetime_refer',
    'clinic_refer',
    'hosp_destination',
    'chiefcomp',
    'physicalexam',
    'diagfirst',
    'diaglast',
    'pstatus',
    'ptype',
    'emergency',
    'ptypedis',
    'causeout',
    'request',
    'provider',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "pid", "seq", "an", "referid_origin", "hospcode_origin", "datetime_serv", "datetime_admit", "datetime_refer", "clinic_refer", "hosp_destination", "chiefcomp", "physicalexam", "diagfirst", "diaglast", "pstatus", "ptype", "emergency", "ptypedis", "causeout", "request", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "REFER_HISTORY"
WHERE SUBSTR("datetime_admit", 1, 8) BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
