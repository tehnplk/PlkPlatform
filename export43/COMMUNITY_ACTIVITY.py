# 43 แฟ้ม: COMMUNITY_ACTIVITY
COLUMNS = [
    'hospcode',
    'vid',
    'date_start',
    'date_finish',
    'comactivity',
    'provider',
    'd_update',
]

SQL = """
SELECT '' AS hospcode, '' AS vid, '' AS date_start, '' AS date_finish,
       '' AS comactivity, '' AS provider, '' AS d_update
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
