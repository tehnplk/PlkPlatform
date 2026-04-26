# 43 แฟ้ม: NEWBORN
COLUMNS = [
    'hospcode',
    'pid',
    'mpid',
    'gravida',
    'ga',
    'bdate',
    'btime',
    'bplace',
    'bhosp',
    'birthno',
    'btype',
    'bdoctor',
    'bweight',
    'asphyxia',
    'vitk',
    'tsh',
    'tshresult',
    'd_update',
    'cid',
    'length',
    'headcircum',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), i.hn, '') AS pid,
  '' AS mpid, '' AS gravida, '' AS ga,
  COALESCE(DATE_FORMAT(nb.born_date, '%%Y%%m%%d'), '') AS bdate,
  COALESCE(DATE_FORMAT(nb.born_time, '%%H%%i%%s'), '') AS btime,
  '1' AS bplace,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS bhosp,
  '' AS birthno, '' AS btype,
  COALESCE(nb.doctor, '') AS bdoctor,
  CAST(CAST(COALESCE(nb.birth_weight, 0) AS UNSIGNED) AS CHAR) AS bweight,
  COALESCE(CAST(nb.has_asphyxia AS CHAR), '') AS asphyxia,
  '' AS vitk, '' AS tsh, '' AS tshresult,
  DATE_FORMAT(NOW(), '%%Y%%m%%d%%H%%i%%s') AS d_update,
  COALESCE(pt.cid, '') AS cid,
  '' AS length, '' AS headcircum
FROM ipt_newborn nb
JOIN ipt i ON i.an = nb.an
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE nb.born_date BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
