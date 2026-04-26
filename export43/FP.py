# 43 แฟ้ม: FP
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'fptype',
    'fpplace',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  COALESCE(fv.fp_code, '') AS fptype,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS fpplace,
  COALESCE(o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM fp_visit fv
JOIN ovst o ON o.vn = fv.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
