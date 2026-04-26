# 43 แฟ้ม: DIAGNOSIS_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'warddiag',
    'diagtype',
    'diagcode',
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
  COALESCE(i.ward, '') AS warddiag,
  COALESCE(d.diagtype, '') AS diagtype,
  COALESCE(d.icd10, '') AS diagcode,
  COALESCE(d.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(d.modify_datetime, '%%Y%%m%%d%%H%%i%%s'), DATE_FORMAT(d.entry_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM iptdiag d
JOIN ipt i ON i.an = d.an
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE i.regdate BETWEEN %s AND %s
  AND CHAR_LENGTH(COALESCE(d.icd10, '')) >= 3
  AND (%s = '' OR %s = '')
"""
