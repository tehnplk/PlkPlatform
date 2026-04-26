# 43 แฟ้ม: EPI
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'vaccinetype',
    'vaccineplace',
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
  COALESCE(pv.export_vaccine_code, pv.vaccine_code, '') AS vaccinetype,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS vaccineplace,
  COALESCE(ov.doctor_code, o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(ov.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM ovst_vaccine ov
JOIN ovst o ON o.vn = ov.vn
LEFT JOIN person_vaccine pv ON pv.person_vaccine_id = ov.person_vaccine_id
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
"""
