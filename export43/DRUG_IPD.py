# 43 แฟ้ม: DRUG_IPD
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'datetime_admit',
    'wardstay',
    'typedrug',
    'didstd',
    'dname',
    'datestart',
    'datefinish',
    'amount',
    'unit',
    'unit_packing',
    'drugprice',
    'drugcost',
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
  '1' AS typedrug,
  COALESCE(di.did, '') AS didstd,
  COALESCE(di.name, '') AS dname,
  COALESCE(DATE_FORMAT(opi.rxdate, '%%Y%%m%%d'), '') AS datestart,
  COALESCE(DATE_FORMAT(opi.rxdate, '%%Y%%m%%d'), '') AS datefinish,
  CAST(CAST(opi.qty AS DECIMAL(12,2)) AS CHAR) AS amount,
  COALESCE(di.provis_medication_unit_code, '') AS unit,
  COALESCE(CAST(di.packqty AS CHAR), '') AS unit_packing,
  CAST(CAST(COALESCE(opi.unitprice, 0) AS DECIMAL(11,2)) AS CHAR) AS drugprice,
  CAST(CAST(COALESCE(opi.cost, 0) AS DECIMAL(11,2)) AS CHAR) AS drugcost,
  COALESCE(NULLIF(opi.doctor, ''), i.admdoctor, i.rxdoctor, '') AS provider,
  COALESCE(DATE_FORMAT(opi.last_modified, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM opitemrece opi
JOIN drugitems di ON di.icode = opi.icode
JOIN ipt i ON i.an = opi.an AND opi.an IS NOT NULL AND opi.an <> ''
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE i.regdate BETWEEN %s AND %s
  AND opi.qty <> 0
  AND (%s = '' OR %s = '')
"""
