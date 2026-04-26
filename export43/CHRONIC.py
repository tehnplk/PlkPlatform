# 43 แฟ้ม: CHRONIC
COLUMNS = [
    'hospcode',
    'pid',
    'date_diag',
    'chronic',
    'hosp_dx',
    'hosp_rx',
    'date_disch',
    'typedisch',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), cm.hn, '') AS pid,
  COALESCE(DATE_FORMAT(cm.begin_date, '%%Y%%m%%d'), DATE_FORMAT(cm.regdate, '%%Y%%m%%d'), '') AS date_diag,
  COALESCE(cm.clinic, '') AS chronic,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hosp_dx,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hosp_rx,
  COALESCE(DATE_FORMAT(cm.dchdate, '%%Y%%m%%d'), '') AS date_disch,
  COALESCE(CAST(cm.clinic_member_status_id AS CHAR), '') AS typedisch,
  COALESCE(DATE_FORMAT(cm.lastupdate, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM clinicmember cm
LEFT JOIN patient pt ON pt.hn = cm.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE EXISTS (
  SELECT 1 FROM ovst o2 WHERE o2.hn = cm.hn AND o2.vstdate BETWEEN %s AND %s
    AND (%s = '' OR o2.ovstist = %s)
)
"""
