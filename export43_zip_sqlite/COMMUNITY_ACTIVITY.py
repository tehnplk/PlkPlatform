# 43 แฟ้ม (SQLite/F43.db): COMMUNITY_ACTIVITY
COLUMNS = [
    'hospcode',
    'vid',
    'date_start',
    'date_finish',
    'comactivity',
    'provider',
    'd_update',
]

SQL = """
SELECT "hospcode", "vid", "date_start", "date_finish", "comactivity", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "COMMUNITY_ACTIVITY"
WHERE ? = ? OR ? = ?  -- no real filter
"""
