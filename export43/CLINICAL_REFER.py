# 43 แฟ้ม: CLINICAL_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_assess',
    'clinicalcode',
    'clinicalname',
    'clinicalvalue',
    'clinicalresult',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid, '' AS referid_province, '' AS datetime_assess,
       '' AS clinicalcode, '' AS clinicalname, '' AS clinicalvalue, '' AS clinicalresult, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
