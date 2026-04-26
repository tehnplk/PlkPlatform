# 43 แฟ้ม: DRUG_OPD
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'clinic',
    'didstd',
    'dname',
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
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '')   AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR)                         AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '')            AS date_serv,
  COALESCE(sp.provis_code, '')                                 AS clinic,
  COALESCE(di.did, '')                                         AS didstd,
  COALESCE(di.name, '')                                        AS dname,
  CAST(CAST(opi.qty AS DECIMAL(15,2)) AS CHAR)                 AS amount,
  COALESCE(di.provis_medication_unit_code, '')                 AS unit,
  COALESCE(CAST(di.packqty AS CHAR), '')                       AS unit_packing,
  CAST(CAST(COALESCE(opi.unitprice, 0) AS DECIMAL(15,2)) AS CHAR) AS drugprice,
  CAST(CAST(COALESCE(opi.cost, 0) AS DECIMAL(15,2)) AS CHAR)   AS drugcost,
  COALESCE(NULLIF(opi.doctor, ''), o.doctor, '')               AS provider,
  COALESCE(DATE_FORMAT(opi.last_modified, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '')                                         AS cid
FROM opitemrece opi
JOIN drugitems di    ON di.icode = opi.icode
JOIN ovst o          ON o.vn = opi.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps  ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp  ON sp.spclty = o.spclty
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
  AND opi.qty <> 0
ORDER BY o.vn, opi.icode
"""
