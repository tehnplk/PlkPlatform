# 43 แฟ้ม: REHABILITATION
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'an',
    'date_admit',
    'date_serv',
    'date_start',
    'date_finish',
    'rehabcode',
    'at_device',
    'at_no',
    'rehabplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS an, '' AS date_admit, '' AS date_serv,
       '' AS date_start, '' AS date_finish, '' AS rehabcode, '' AS at_device, '' AS at_no,
       '' AS rehabplace, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
