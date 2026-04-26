# 43 แฟ้ม: COMMUNITY_SERVICE
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'comservice',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS date_serv,
       '' AS comservice, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
