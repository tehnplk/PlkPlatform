# 43 แฟ้ม: WOMEN
COLUMNS = [
    'hospcode',
    'pid',
    'fptype',
    'nofpcause',
    'totalson',
    'numberson',
    'abortion',
    'stillbirth',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS fptype, '' AS nofpcause, '' AS totalson,
       '' AS numberson, '' AS abortion, '' AS stillbirth, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
