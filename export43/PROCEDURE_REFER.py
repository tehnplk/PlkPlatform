# 43 แฟ้ม: PROCEDURE_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'timestart',
    'timefinish',
    'procedurename',
    'procedcode',
    'pdescription',
    'procedresult',
    'provider',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid, '' AS referid_province, '' AS timestart, '' AS timefinish,
       '' AS procedurename, '' AS procedcode, '' AS pdescription, '' AS procedresult,
       '' AS provider, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
