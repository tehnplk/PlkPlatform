# 43 แฟ้ม: REFER_RESULT
COLUMNS = [
    'hospcode',
    'referid_source',
    'referid_province',
    'hosp_source',
    'refer_result',
    'datetime_in',
    'pid_in',
    'an_in',
    'reason',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid_source, '' AS referid_province, '' AS hosp_source,
       '' AS refer_result, '' AS datetime_in, '' AS pid_in, '' AS an_in,
       '' AS reason, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
