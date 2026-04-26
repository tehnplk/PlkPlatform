# 43 แฟ้ม (SQLite/F43.db): DATA_CORRECT
COLUMNS = [
    'hospcode',
    'tablename',
    'data_correct',
    'd_update',
]

SQL = """
SELECT "hospcode", "tablename", "data_correct", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "DATA_CORRECT"
WHERE ? = ? OR ? = ?  -- no real filter
"""
