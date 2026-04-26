# 43 แฟ้ม: CHARGE_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'chargeitem',
    'chargelist',
    'quantity',
    'instype',
    'cost',
    'price',
    'payprice',
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
  COALESCE(ie.group2, '') AS chargeitem,
  COALESCE(opi.icode, '') AS chargelist,
  CAST(CAST(COALESCE(opi.qty, 0) AS DECIMAL(11,2)) AS CHAR) AS quantity,
  COALESCE(pts.pttype_std_code, y.nhso_code, '') AS instype,
  CAST(CAST(COALESCE(opi.cost, 0) AS DECIMAL(11,2)) AS CHAR) AS cost,
  CAST(CAST(COALESCE(opi.sum_price, 0) AS DECIMAL(11,2)) AS CHAR) AS price,
  CAST(CAST(COALESCE(opi.sum_price, 0) AS DECIMAL(11,2)) AS CHAR) AS payprice,
  COALESCE(DATE_FORMAT(opi.last_modified, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM opitemrece opi
JOIN ipt i ON i.an = opi.an AND opi.an IS NOT NULL AND opi.an <> ''
LEFT JOIN income ie ON ie.income = opi.income
LEFT JOIN pttype y ON y.pttype = opi.pttype
LEFT JOIN provis_instype pts ON pts.code = y.nhso_code
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE i.regdate BETWEEN %s AND %s
  AND opi.qty <> 0
  AND (%s = '' OR %s = '')
"""
