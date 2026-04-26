# 43 แฟ้ม (SQLite/F43.db): PROVIDER
COLUMNS = [
    'hospcode',
    'provider',
    'registerno',
    'council',
    'cid',
    'prename',
    'name',
    'lname',
    'sex',
    'birth',
    'providertype',
    'startdate',
    'outdate',
    'movefrom',
    'moveto',
    'd_update',
]

SQL = """
SELECT "hospcode", "provider", "registerno", "council", "cid", "prename", "name", "lname", "sex", "birth", "providertype", "startdate", "outdate", "movefrom", "moveto", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "PROVIDER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
