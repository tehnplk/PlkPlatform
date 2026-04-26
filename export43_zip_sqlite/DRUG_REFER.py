# 43 แฟ้ม (SQLite/F43.db): DRUG_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_dstart',
    'datetime_dfinish',
    'didstd',
    'dname',
    'ddescription',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "datetime_dstart", "datetime_dfinish", "didstd", "dname", "ddescription", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "DRUG_REFER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
