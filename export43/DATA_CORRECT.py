# 43 แฟ้ม: DATA_CORRECT
COLUMNS = [
    'hospcode',
    'tablename',
    'data_correct',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS tablename, '' AS data_correct, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
