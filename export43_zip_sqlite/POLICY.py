# 43 แฟ้ม (SQLite/F43.db): POLICY
COLUMNS = [
    'hospcode',
    'policy_id',
    'policy_year',
    'policy_data',
    'd_update',
]

SQL = """
SELECT "hospcode", "policy_id", "policy_year", "policy_data", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "POLICY"
WHERE ? = ? OR ? = ?  -- no real filter
"""
