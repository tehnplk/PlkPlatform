# 43 แฟ้ม: FUNCTIONAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'functional_test',
    'testresult',
    'dependent',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS date_serv, '' AS functional_test,
       '' AS testresult, '' AS dependent, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
