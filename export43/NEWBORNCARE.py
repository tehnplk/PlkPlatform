# 43 แฟ้ม: NEWBORNCARE
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'bdate',
    'bcare',
    'bcplace',
    'bcareresult',
    'food',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS bdate, '' AS bcare,
       '' AS bcplace, '' AS bcareresult, '' AS food, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
