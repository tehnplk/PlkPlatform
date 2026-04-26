# 43 แฟ้ม: CHRONICFU
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'weight',
    'height',
    'waist_cm',
    'sbp',
    'dbp',
    'foot',
    'retina',
    'provider',
    'd_update',
    'chronicfuplace',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  CAST(CAST(COALESCE(s.bw, 0) AS DECIMAL(5,2)) AS CHAR) AS weight,
  CAST(CAST(COALESCE(s.height, 0) AS UNSIGNED) AS CHAR) AS height,
  CAST(CAST(COALESCE(s.waist, 0) AS UNSIGNED) AS CHAR) AS waist_cm,
  CAST(CAST(COALESCE(s.bps, 0) AS UNSIGNED) AS CHAR) AS sbp,
  CAST(CAST(COALESCE(s.bpd, 0) AS UNSIGNED) AS CHAR) AS dbp,
  '' AS foot,
  '' AS retina,
  COALESCE(o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(s.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS chronicfuplace,
  COALESCE(pt.cid, '') AS cid
FROM ovst o
JOIN clinicmember cm ON cm.hn = o.hn
LEFT JOIN opdscreen s ON s.vn = o.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
GROUP BY o.vn
"""
