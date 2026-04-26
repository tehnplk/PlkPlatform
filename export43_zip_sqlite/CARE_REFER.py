# 43 แฟ้ม (SQLite/F43.db): CARE_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'caretype',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "caretype", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "CARE_REFER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
