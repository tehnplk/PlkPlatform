# 43 แฟ้ม (SQLite/F43.db): ACCIDENT
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'datetime_serv',
    'datetime_ae',
    'aetype',
    'aeplace',
    'typein_ae',
    'traffic',
    'vehicle',
    'alcohol',
    'nacrotic_drug',
    'belt',
    'helmet',
    'airway',
    'stopbleed',
    'splint',
    'fluid',
    'urgency',
    'coma_eye',
    'coma_speak',
    'coma_movement',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "datetime_serv", "datetime_ae", "aetype", "aeplace", "typein_ae", "traffic", "vehicle", "alcohol", "nacrotic_drug", "belt", "helmet", "airway", "stopbleed", "splint", "fluid", "urgency", "coma_eye", "coma_speak", "coma_movement", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "ACCIDENT"
WHERE "datetime_serv" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
