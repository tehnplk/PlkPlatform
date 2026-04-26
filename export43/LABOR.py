# 43 แฟ้ม: LABOR
COLUMNS = [
    'hospcode',
    'pid',
    'gravida',
    'lmp',
    'edc',
    'bdate',
    'bresult',
    'bplace',
    'bhosp',
    'btype',
    'bdoctor',
    'lborn',
    'sborn',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), i.hn, '') AS pid,
  COALESCE(CAST(ip.preg_number AS CHAR), '') AS gravida,
  '' AS lmp, '' AS edc,
  COALESCE(DATE_FORMAT(ip.labor_date, '%%Y%%m%%d'), '') AS bdate,
  '' AS bresult, '1' AS bplace,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS bhosp,
  COALESCE(ip.deliver_type, '') AS btype,
  '' AS bdoctor, '' AS lborn, '' AS sborn,
  DATE_FORMAT(NOW(), '%%Y%%m%%d%%H%%i%%s') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM ipt_pregnancy ip
JOIN ipt i ON i.an = ip.an
LEFT JOIN patient pt ON pt.hn = i.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE ip.labor_date BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
