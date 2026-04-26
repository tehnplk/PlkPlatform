# 43 แฟ้ม: SURVEILLANCE
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'an',
    'datetime_admit',
    'syndrome',
    'diagcode',
    'code506',
    'diagcodelast',
    'code506last',
    'illdate',
    'illhouse',
    'illvillage',
    'illtambon',
    'illampur',
    'illchangwat',
    'latitude',
    'longitude',
    'ptstatus',
    'date_death',
    'complication',
    'organism',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT '' AS hospcode, '' AS pid, '' AS seq, '' AS date_serv, '' AS an, '' AS datetime_admit,
       '' AS syndrome, '' AS diagcode, '' AS code506, '' AS diagcodelast, '' AS code506last,
       '' AS illdate, '' AS illhouse, '' AS illvillage, '' AS illtambon, '' AS illampur,
       '' AS illchangwat, '' AS latitude, '' AS longitude, '' AS ptstatus, '' AS date_death,
       '' AS complication, '' AS organism, '' AS provider, '' AS d_update, '' AS cid
FROM dual WHERE 1=0 AND %s='' AND %s='' AND %s='' AND %s=''
"""
