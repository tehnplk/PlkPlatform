# 43 แฟ้ม: ACCIDENT
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'datetime_serv',
    'datetime_ae',
    'aetype',
    'aeplace',
    'typein_ae',
    'traffic',
    'vehicle',
    'alcohol',
    'nacrotic_drug',
    'belt',
    'helmet',
    'airway',
    'stopbleed',
    'splint',
    'fluid',
    'urgency',
    'coma_eye',
    'coma_speak',
    'coma_movement',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(CONCAT(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), DATE_FORMAT(o.vsttime, '%%H%%i%%s')), '') AS datetime_serv,
  COALESCE(CONCAT(DATE_FORMAT(va.odate, '%%Y%%m%%d'), DATE_FORMAT(va.otime, '%%H%%i%%s')), '') AS datetime_ae,
  '' AS aetype, '' AS aeplace, '' AS typein_ae, '' AS traffic, '' AS vehicle,
  '' AS alcohol, '' AS nacrotic_drug, '' AS belt, '' AS helmet,
  '' AS airway, '' AS stopbleed, '' AS splint, '' AS fluid, '' AS urgency,
  '' AS coma_eye, '' AS coma_speak, '' AS coma_movement,
  COALESCE(DATE_FORMAT(va.odate, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM ovaccident va
JOIN ovst o ON o.vn = va.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
"""
