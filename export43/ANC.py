# 43 แฟ้ม: ANC
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'gravida',
    'ancno',
    'ga',
    'ancresult',
    'ancplace',
    'provider',
    'd_update',
    'cid',
    'weight',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  '' AS gravida, '' AS ancno, '' AS ga,
  '' AS ancresult,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS ancplace,
  COALESCE(o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid,
  '0' AS weight
FROM anc_visit av
LEFT JOIN anc_head ah ON ah.anc_number = av.anc_number
JOIN ovst o ON o.vn = av.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = ah.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
