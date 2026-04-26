# 43 แฟ้ม: NCDSCREEN
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'servplace',
    'smoke',
    'alcohol',
    'dmfamily',
    'htfamily',
    'weight',
    'height',
    'waist_cm',
    'sbp_1',
    'dbp_1',
    'sbp_2',
    'dbp_2',
    'bslevel',
    'bstest',
    'screenplace',
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
  '1' AS servplace,
  COALESCE(CAST(s.smoking_type_id AS CHAR), '') AS smoke,
  COALESCE(CAST(s.drinking_type_id AS CHAR), '') AS alcohol,
  '' AS dmfamily, '' AS htfamily,
  CAST(CAST(COALESCE(s.bw, 0) AS DECIMAL(5,2)) AS CHAR) AS weight,
  CAST(CAST(COALESCE(s.height, 0) AS UNSIGNED) AS CHAR) AS height,
  CAST(CAST(COALESCE(s.waist, 0) AS UNSIGNED) AS CHAR) AS waist_cm,
  CAST(CAST(COALESCE(s.bps, 0) AS UNSIGNED) AS CHAR) AS sbp_1,
  CAST(CAST(COALESCE(s.bpd, 0) AS UNSIGNED) AS CHAR) AS dbp_1,
  '' AS sbp_2, '' AS dbp_2,
  CAST(CAST(COALESCE(s.fbs, 0) AS DECIMAL(6,2)) AS CHAR) AS bslevel,
  '' AS bstest,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS screenplace,
  COALESCE(o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(s.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM opdscreen s
JOIN ovst o ON o.vn = s.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
"""
