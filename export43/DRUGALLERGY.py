# 43 แฟ้ม: DRUGALLERGY
COLUMNS = [
    'hospcode',
    'pid',
    'daterecord',
    'drugallergy',
    'dname',
    'typedx',
    'alevel',
    'symptom',
    'informant',
    'informhosp',
    'd_update',
    'provider',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), oa.hn, '') AS pid,
  COALESCE(DATE_FORMAT(oa.report_date, '%%Y%%m%%d'), '') AS daterecord,
  COALESCE(oa.agent_code24, di.did, '') AS drugallergy,
  COALESCE(NULLIF(oa.agent, ''), di.name, '') AS dname,
  COALESCE(CAST(oa.allergy_type AS CHAR), '') AS typedx,
  COALESCE(CAST(oa.seriousness_id AS CHAR), '') AS alevel,
  COALESCE(oa.symptom, '') AS symptom,
  COALESCE(oa.reporter, '') AS informant,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS informhosp,
  COALESCE(DATE_FORMAT(oa.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(oa.doctor_code, '') AS provider,
  COALESCE(pt.cid, '') AS cid
FROM opd_allergy oa
LEFT JOIN drugitems di ON di.icode = oa.icode
LEFT JOIN patient pt ON pt.hn = oa.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE EXISTS (
  SELECT 1 FROM ovst o2 WHERE o2.hn = oa.hn AND o2.vstdate BETWEEN %s AND %s
    AND (%s = '' OR o2.ovstist = %s)
)
"""
