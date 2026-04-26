# 43 แฟ้ม: ADMISSION
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'an',
    'datetime_admit',
    'wardadmit',
    'instype',
    'typein',
    'referinhosp',
    'causein',
    'admitweight',
    'admitheight',
    'datetime_disch',
    'warddisch',
    'dischstatus',
    'dischtype',
    'referouthosp',
    'causeout',
    'cost',
    'price',
    'payprice',
    'actualpay',
    'provider',
    'd_update',
    'drg',
    'rw',
    'adjrw',
    'error',
    'warning',
    'actlos',
    'grouper_version',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), i.hn, '') AS pid,
  '' AS seq,
  COALESCE(i.an, '') AS an,
  CONCAT(DATE_FORMAT(i.regdate, '%%Y%%m%%d'), COALESCE(DATE_FORMAT(i.regtime, '%%H%%i%%s'), '000000')) AS datetime_admit,
  COALESCE(i.ward, '') AS wardadmit,
  COALESCE(pts.pttype_std_code, y.nhso_code, '') AS instype,
  '1' AS typein,
  COALESCE(rf.refer_hospcode, '') AS referinhosp,
  '' AS causein,
  CAST(CAST(COALESCE(i.bw, 0) AS DECIMAL(5,2)) AS CHAR) AS admitweight,
  CAST(CAST(COALESCE(i.body_height, 0) AS UNSIGNED) AS CHAR) AS admitheight,
  COALESCE(CONCAT(DATE_FORMAT(i.dchdate, '%%Y%%m%%d'), DATE_FORMAT(i.dchtime, '%%H%%i%%s')), '') AS datetime_disch,
  COALESCE(i.ward, '') AS warddisch,
  COALESCE(CAST(i.dchstts AS CHAR), '') AS dischstatus,
  COALESCE(CAST(i.dchtype AS CHAR), '') AS dischtype,
  '' AS referouthosp,
  '' AS causeout,
  '0.00' AS cost, '0.00' AS price, '0.00' AS payprice, '0.00' AS actualpay,
  COALESCE(i.admdoctor, i.rxdoctor, '') AS provider,
  COALESCE(DATE_FORMAT(i.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(i.drg, '') AS drg,
  CAST(CAST(COALESCE(i.rw, 0) AS DECIMAL(11,4)) AS CHAR) AS rw,
  CAST(CAST(COALESCE(i.adjrw, 0) AS DECIMAL(11,4)) AS CHAR) AS adjrw,
  COALESCE(CAST(i.grouper_err AS CHAR), '') AS error,
  COALESCE(CAST(i.grouper_warn AS CHAR), '') AS warning,
  CAST(CAST(COALESCE(i.grouper_actlos, 0) AS UNSIGNED) AS CHAR) AS actlos,
  COALESCE(i.grouper_version, '') AS grouper_version,
  COALESCE(pt.cid, '') AS cid
FROM ipt i
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN pttype y ON y.pttype = i.pttype
LEFT JOIN provis_instype pts ON pts.code = y.nhso_code
LEFT JOIN referin rf ON rf.vn = i.vn
WHERE i.regdate BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
