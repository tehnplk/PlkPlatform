# 43 แฟ้ม: DEATH
COLUMNS = [
    'hospcode',
    'pid',
    'hospdeath',
    'an',
    'seq',
    'ddeath',
    'cdeath_a',
    'cdeath_b',
    'cdeath_c',
    'cdeath_d',
    'odisease',
    'cdeath',
    'pregdeath',
    'pdeath',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), pt.hn, '') AS pid,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospdeath,
  COALESCE(d.an, '') AS an,
  '' AS seq,
  COALESCE(DATE_FORMAT(d.death_date, '%%Y%%m%%d'), DATE_FORMAT(pt.deathday, '%%Y%%m%%d'), '') AS ddeath,
  COALESCE(d.death_diag_1, '') AS cdeath_a,
  COALESCE(d.death_diag_2, '') AS cdeath_b,
  COALESCE(d.death_diag_3, '') AS cdeath_c,
  COALESCE(d.death_diag_4, '') AS cdeath_d,
  COALESCE(d.odisease, '') AS odisease,
  COALESCE(d.death_cause, d.death_diag_icd10, '') AS cdeath,
  '' AS pregdeath, '' AS pdeath,
  COALESCE(d.death_cert_doctor, '') AS provider,
  COALESCE(DATE_FORMAT(d.last_update, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM patient pt
LEFT JOIN death d ON d.hn = pt.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE pt.deathday IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM ovst o2 WHERE o2.hn = pt.hn
      AND o2.vstdate BETWEEN %s AND %s
      AND (%s = '' OR o2.ovstist = %s)
  )
"""
