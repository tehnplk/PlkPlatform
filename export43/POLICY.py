# 43 แฟ้ม: POLICY
COLUMNS = [
    'hospcode',
    'policy_id',
    'policy_year',
    'policy_data',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS policy_id, '' AS policy_year, '' AS policy_data, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
