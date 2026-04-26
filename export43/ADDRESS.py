# 43 แฟ้ม: ADDRESS
COLUMNS = [
    'hospcode',
    'pid',
    'addresstype',
    'house_id',
    'housetype',
    'roomno',
    'condo',
    'houseno',
    'soisub',
    'soimain',
    'road',
    'villaname',
    'village',
    'tambon',
    'ampur',
    'changwat',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  LPAD(CAST(p.person_id AS CHAR), 6, '0') AS pid,
  '1' AS addresstype,
  COALESCE(CAST(p.house_id AS CHAR), '') AS house_id,
  COALESCE(CAST(p.house_regist_type_id AS CHAR), '') AS housetype,
  '' AS roomno,
  '' AS condo,
  '' AS houseno, '' AS soisub, '' AS soimain, '' AS road, '' AS villaname,
  COALESCE(LPAD(p.village_id, 2, '0'), '') AS village,
  '' AS tambon, '' AS ampur, '' AS changwat,
  COALESCE(DATE_FORMAT(p.last_update, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(p.cid, '') AS cid
FROM person p
WHERE EXISTS (
  SELECT 1 FROM ovst o2 LEFT JOIN patient pt2 ON pt2.hn=o2.hn
  WHERE pt2.cid = p.cid AND o2.vstdate BETWEEN %s AND %s
    AND (%s = '' OR o2.ovstist = %s)
)
"""
