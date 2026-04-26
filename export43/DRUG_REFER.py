# 43 แฟ้ม: DRUG_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_dstart',
    'datetime_dfinish',
    'didstd',
    'dname',
    'ddescription',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid, '' AS referid_province, '' AS datetime_dstart,
       '' AS datetime_dfinish, '' AS didstd, '' AS dname, '' AS ddescription, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
