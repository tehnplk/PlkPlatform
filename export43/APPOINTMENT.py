# 43 แฟ้ม: APPOINTMENT
COLUMNS = [
    'hospcode',
    'pid',
    'an',
    'seq',
    'date_serv',
    'clinic',
    'apdate',
    'aptype',
    'apdiag',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), oa.hn, '') AS pid,
  '' AS an,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  COALESCE(sp.provis_code, '') AS clinic,
  COALESCE(DATE_FORMAT(oa.nextdate, '%%Y%%m%%d'), '') AS apdate,
  '' AS aptype,
  '' AS apdiag,
  COALESCE(oa.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(oa.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '') AS cid
FROM oapp oa
LEFT JOIN ovst o ON o.vn = oa.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = oa.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp ON sp.spclty = oa.spclty
WHERE oa.vstdate BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
