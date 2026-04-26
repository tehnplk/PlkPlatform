# 43 แฟ้ม: ICF
COLUMNS = [
    'hospcode',
    'disabid',
    'pid',
    'seq',
    'date_serv',
    'icf',
    'qualifier',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS disabid, '' AS pid, '' AS seq, '' AS date_serv,
       '' AS icf, '' AS qualifier, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
