# 43 แฟ้ม: DISABILITY
COLUMNS = [
    'hospcode',
    'disabid',
    'pid',
    'disabtype',
    'disabcause',
    'diagcode',
    'date_detect',
    'date_disab',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS disabid, '' AS pid, '' AS disabtype, '' AS disabcause,
       '' AS diagcode, '' AS date_detect, '' AS date_disab, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
