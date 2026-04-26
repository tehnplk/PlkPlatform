# 43 แฟ้ม: REFER_HISTORY
COLUMNS = [
    'hospcode',
    'referid',
    'referid_province',
    'pid',
    'seq',
    'an',
    'referid_origin',
    'hospcode_origin',
    'datetime_serv',
    'datetime_admit',
    'datetime_refer',
    'clinic_refer',
    'hosp_destination',
    'chiefcomp',
    'physicalexam',
    'diagfirst',
    'diaglast',
    'pstatus',
    'ptype',
    'emergency',
    'ptypedis',
    'causeout',
    'request',
    'provider',
    'd_update',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(ro.refer_number, '') AS referid,
  '' AS referid_province,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  '' AS an,
  '' AS referid_origin,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode_origin,
  COALESCE(CONCAT(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), DATE_FORMAT(o.vsttime, '%%H%%i%%s')), '') AS datetime_serv,
  '' AS datetime_admit,
  COALESCE(CONCAT(DATE_FORMAT(ro.refer_date, '%%Y%%m%%d'), DATE_FORMAT(ro.refer_time, '%%H%%i%%s')), '') AS datetime_refer,
  COALESCE(sp.provis_code, '') AS clinic_refer,
  COALESCE(ro.refer_hospcode, '') AS hosp_destination,
  '' AS chiefcomp,
  '' AS physicalexam,
  COALESCE(ro.pdx, ro.pre_diagnosis, '') AS diagfirst,
  COALESCE(ro.pdx, '') AS diaglast,
  COALESCE(LEFT(ro.ptstatus_text, 250), '') AS pstatus,
  '' AS ptype, '' AS emergency, '' AS ptypedis, '' AS causeout,
  COALESCE(LEFT(ro.request_text, 250), '') AS request,
  COALESCE(ro.doctor, o.doctor, '') AS provider,
  COALESCE(DATE_FORMAT(ro.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update
FROM referout ro
LEFT JOIN ovst o ON o.vn = ro.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp ON sp.spclty = o.spclty
WHERE ro.refer_date BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
