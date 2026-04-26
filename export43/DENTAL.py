# 43 แฟ้ม: DENTAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'denttype',
    'servplace',
    'pteeth',
    'pcaries',
    'pfilling',
    'pextract',
    'dteeth',
    'dcaries',
    'dfilling',
    'dextract',
    'need_fluoride',
    'need_scaling',
    'need_sealant',
    'need_pfilling',
    'need_dfilling',
    'need_pextract',
    'need_dextract',
    'nprosthesis',
    'permanent_permanent',
    'permanent_prosthesis',
    'prosthesis_prosthesis',
    'gum',
    'schooltype',
    'class',
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
  '' AS denttype, '1' AS servplace,
  '' AS pteeth, '' AS pcaries, '' AS pfilling, '' AS pextract,
  '' AS dteeth, '' AS dcaries, '' AS dfilling, '' AS dextract,
  '' AS need_fluoride, '' AS need_scaling, '' AS need_sealant,
  '' AS need_pfilling, '' AS need_dfilling, '' AS need_pextract, '' AS need_dextract,
  '' AS nprosthesis, '' AS permanent_permanent, '' AS permanent_prosthesis,
  '' AS prosthesis_prosthesis, '' AS gum, '' AS schooltype, '' AS class,
  COALESCE(dt.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(dt.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM dtmain dt
JOIN ovst o ON o.vn = dt.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
"""
