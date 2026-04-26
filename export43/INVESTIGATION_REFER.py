# 43 แฟ้ม: INVESTIGATION_REFER
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'datetime_invest',
    'investcode',
    'investname',
    'datetime_report',
    'investvalue',
    'investresult',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS referid, '' AS referid_province, '' AS datetime_invest,
       '' AS investcode, '' AS investname, '' AS datetime_report, '' AS investvalue,
       '' AS investresult, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
