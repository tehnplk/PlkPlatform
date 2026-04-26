# 43 แฟ้ม (SQLite/F43.db): CLINICAL_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_assess',
    'clinicalcode',
    'clinicalname',
    'clinicalvalue',
    'clinicalresult',
    'd_update',
]

SQL = """
SELECT "hospcode", "referid", "referid_province", "datetime_assess", "clinicalcode", "clinicalname", "clinicalvalue", "clinicalresult", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "CLINICAL_REFER"
WHERE ? = ? OR ? = ?  -- no real filter
"""
