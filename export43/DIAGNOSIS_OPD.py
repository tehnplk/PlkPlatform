# 43 แฟ้ม: DIAGNOSIS_OPD
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'diagtype',
    'diagcode',
    'clinic',
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
  COALESCE(d.diagtype, '')                                     AS diagtype,
  COALESCE(d.icd10, '')                                        AS diagcode,
  COALESCE(sp.provis_code, '')                                 AS clinic,
  COALESCE(d.doctor, '')                                       AS provider,
  COALESCE(DATE_FORMAT(d.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '')                                         AS cid
FROM ovstdiag d
JOIN ovst o          ON o.vn = d.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps  ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp  ON sp.spclty = o.spclty
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
  AND CHAR_LENGTH(COALESCE(d.icd10, '')) >= 3
ORDER BY o.vn, d.diagtype
"""
