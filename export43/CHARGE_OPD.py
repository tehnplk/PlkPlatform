# 43 แฟ้ม: CHARGE_OPD
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'clinic',
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
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  COALESCE(sp.provis_code, '') AS clinic,
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
JOIN ovst o ON o.vn = opi.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp ON sp.spclty = o.spclty
LEFT JOIN income ie ON ie.income = opi.income
LEFT JOIN pttype y ON y.pttype = opi.pttype
LEFT JOIN provis_instype pts ON pts.code = y.nhso_code
WHERE o.vstdate BETWEEN %s AND %s
  AND opi.qty <> 0
  AND (%s = '' OR o.ovstist = %s)
"""
