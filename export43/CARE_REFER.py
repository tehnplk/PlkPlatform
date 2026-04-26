# 43 แฟ้ม: CARE_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'caretype',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid, '' AS referid_province, '' AS caretype, '' AS d_update
FROM dual
WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
