# 43 แฟ้ม: NUTRITION
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'nutritionplace',
    'weight',
    'height',
    'headcircum',
    'childdevelop',
    'food',
    'bottle',
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
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS nutritionplace,
  CAST(CAST(COALESCE(s.bw, 0) AS DECIMAL(5,2)) AS CHAR) AS weight,
  CAST(CAST(COALESCE(s.height, 0) AS UNSIGNED) AS CHAR) AS height,
  CAST(CAST(COALESCE(s.head_cricumference, 0) AS DECIMAL(5,2)) AS CHAR) AS headcircum,
  '' AS childdevelop, '' AS food, '' AS bottle,
  COALESCE(o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(s.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM opdscreen s
JOIN ovst o ON o.vn = s.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (s.bw IS NOT NULL OR s.height IS NOT NULL)
  AND (%s = '' OR o.ovstist = %s)
"""
