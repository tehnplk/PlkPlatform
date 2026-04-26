# 43 แฟ้ม: PROCEDURE_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'procedcode',
    'timestart',
    'timefinish',
    'serviceprice',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), i.hn, '') AS pid,
  COALESCE(i.an, '') AS an,
  CONCAT(DATE_FORMAT(i.regdate, '%%Y%%m%%d'), COALESCE(DATE_FORMAT(i.regtime, '%%H%%i%%s'), '000000')) AS datetime_admit,
  COALESCE(i.ward, '') AS wardstay,
  COALESCE(op.icd9, '') AS procedcode,
  COALESCE(CONCAT(DATE_FORMAT(op.opdate, '%%Y%%m%%d'), DATE_FORMAT(op.optime, '%%H%%i%%s')), '') AS timestart,
  COALESCE(CONCAT(DATE_FORMAT(op.enddate, '%%Y%%m%%d'), DATE_FORMAT(op.endtime, '%%H%%i%%s')), '') AS timefinish,
  CAST(CAST(COALESCE(op.iprice, 0) AS DECIMAL(11,2)) AS CHAR) AS serviceprice,
  COALESCE(op.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(op.modify_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM iptoprt op
JOIN ipt i ON i.an = op.an
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE i.regdate BETWEEN %s AND %s
  AND CHAR_LENGTH(COALESCE(op.icd9, '')) >= 3
  AND (%s = '' OR %s = '')
"""
