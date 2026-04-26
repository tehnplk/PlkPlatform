# 43 แฟ้ม: SPECIALPP
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'servplace',
    'ppspecial',
    'ppsplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS date_serv, '' AS servplace,
       '' AS ppspecial, '' AS ppsplace, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
