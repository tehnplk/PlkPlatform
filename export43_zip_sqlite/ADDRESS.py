# 43 แฟ้ม (SQLite/F43.db): ADDRESS
COLUMNS = [
    'hospcode',
    'pid',
    'addresstype',
    'house_id',
    'housetype',
    'roomno',
    'condo',
    'houseno',
    'soisub',
    'soimain',
    'road',
    'villaname',
    'village',
    'tambon',
    'ampur',
    'changwat',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "addresstype", "house_id", "housetype", "roomno", "condo", "houseno", "soisub", "soimain", "road", "villaname", "village", "tambon", "ampur", "changwat", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "ADDRESS"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
