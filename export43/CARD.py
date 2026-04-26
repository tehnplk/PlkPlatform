# 43 แฟ้ม: CARD
COLUMNS = [
    'hospcode',
    'pid',
    'instype_old',
    'instype_new',
    'insid',
    'startdate',
    'expiredate',
    'main',
    'sub',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), pc.hn, '') AS pid,
  COALESCE(pc.cardtype, '') AS instype_old,
  COALESCE(pc.cardtype, '') AS instype_new,
  COALESCE(pc.cardno, '') AS insid,
  '' AS startdate,
  COALESCE(DATE_FORMAT(pc.expiredate, '%%Y%%m%%d'), '') AS expiredate,
  '' AS main,
  '' AS sub,
  DATE_FORMAT(NOW(), '%%Y%%m%%d%%H%%i%%s') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM ptcardno pc
LEFT JOIN patient pt ON pt.hn = pc.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE EXISTS (
  SELECT 1 FROM ovst o2 WHERE o2.hn = pc.hn AND o2.vstdate BETWEEN %s AND %s
    AND (%s = '' OR o2.ovstist = %s)
)
"""
