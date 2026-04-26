# 43 แฟ้ม: POSTNATAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'gravida',
    'bdate',
    'ppcare',
    'ppplace',
    'ppresult',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS gravida, '' AS bdate,
       '' AS ppcare, '' AS ppplace, '' AS ppresult, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
