# 43 แฟ้ม: SERVICE
COLUMNS = [
    'hospcode',
    'pid',
    'hn',
    'seq',
    'date_serv',
    'time_serv',
    'location',
    'intime',
    'instype',
    'insid',
    'main',
    'typein',
    'referinhosp',
    'causein',
    'chiefcomp',
    'servplace',
    'btemp',
    'sbp',
    'dbp',
    'pr',
    'rr',
    'typeout',
    'referouthosp',
    'causeout',
    'cost',
    'price',
    'payprice',
    'actualpay',
    'd_update',
    'hsub',
    'cid',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '')   AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  COALESCE(o.hn, '')                                           AS hn,
  CAST(COALESCE(q.seq_id, '') AS CHAR)                         AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '')            AS date_serv,
  COALESCE(DATE_FORMAT(o.vsttime, '%%H%%i%%s'), '')            AS time_serv,
  CASE
    WHEN ps.house_regist_type_id = 4 THEN '2'
    WHEN ps.house_regist_type_id IN (1, 2, 3, 5) THEN '1'
    WHEN v.pttype_in_region = 'Y' THEN '1'
    ELSE '2'
  END                                                          AS location,
  CASE
    WHEN DAYOFWEEK(o.vstdate) IN (1, 7) THEN '2'
    WHEN o.vsttime IS NULL THEN '1'
    WHEN TIME(o.vsttime) BETWEEN '08:30:00' AND '16:30:00' THEN '1'
    ELSE '2'
  END                                                          AS intime,
  COALESCE(pts.pttype_std_code, y.nhso_code, '')               AS instype,
  COALESCE(o.pttypeno, '')                                     AS insid,
  COALESCE(o.hospmain, '')                                     AS main,
  COALESCE(oi.export_code, '')                                 AS typein,
  COALESCE(rf.refer_hospcode, '')                              AS referinhosp,
  COALESCE(rf.f43_causein_id, '')                             AS causein,
  COALESCE(s.cc, '')                                           AS chiefcomp,
  CASE
    WHEN oi.export_code = '5' THEN '2'
    WHEN o.visit_type = 'O' THEN '2'
    WHEN o.visit_type = 'I' THEN '1'
    ELSE '1'
  END                                                          AS servplace,
  CASE WHEN s.temperature IS NULL THEN '' ELSE CAST(ROUND(s.temperature, 1) AS CHAR) END AS btemp,
  CAST(CAST(COALESCE(s.bps, 0) AS UNSIGNED) AS CHAR)           AS sbp,
  CAST(CAST(COALESCE(s.bpd, 0) AS UNSIGNED) AS CHAR)           AS dbp,
  CAST(CAST(COALESCE(s.pulse, 0) AS UNSIGNED) AS CHAR)         AS pr,
  CAST(CAST(COALESCE(s.rr, 0) AS UNSIGNED) AS CHAR)            AS rr,
  COALESCE(oo.export_code, '1')                                AS typeout,
  COALESCE(ro.refer_hospcode, '')                              AS referouthosp,
  COALESCE(rc1.export_code, '')                                AS causeout,
  CASE WHEN v.income IS NULL THEN '0.00' ELSE CAST(CAST(v.income AS DECIMAL(10,2)) AS CHAR) END AS cost,
  CASE WHEN v.income IS NULL THEN '' ELSE CAST(CAST(v.income AS DECIMAL(10,2)) AS CHAR) END AS price,
  CASE WHEN v.rcpt_money IS NULL THEN '0.00' ELSE CAST(CAST(v.rcpt_money AS DECIMAL(10,2)) AS CHAR) END AS payprice,
  CASE WHEN v.rcpt_money IS NULL THEN '0.00' ELSE CAST(CAST(v.rcpt_money AS DECIMAL(10,2)) AS CHAR) END AS actualpay,
  COALESCE(DATE_FORMAT(q.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(o.hospsub, '')                                      AS hsub,
  COALESCE(pt.cid, '')                                         AS cid
FROM ovst o
LEFT JOIN spclty sp     ON sp.spclty = o.spclty
LEFT JOIN vn_stat v     ON v.vn = o.vn
LEFT JOIN opdscreen s   ON s.vn = o.vn
LEFT JOIN ovst_seq q    ON q.vn = o.vn
LEFT JOIN patient pt    ON pt.hn = o.hn
LEFT JOIN person ps     ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN ovstist oi    ON oi.ovstist = o.ovstist
LEFT JOIN ovstost oo    ON oo.ovstost = o.ovstost
LEFT JOIN pttype y      ON y.pttype = o.pttype
LEFT JOIN provis_instype pts ON pts.code = y.nhso_code
LEFT JOIN referin rf    ON rf.vn = o.vn
LEFT JOIN referout ro   ON ro.vn = o.vn
LEFT JOIN rfrcs rc1     ON rc1.rfrcs = ro.rfrcs
WHERE o.vstdate BETWEEN %s AND %s
  AND (sp.no_export_43 = 'N' OR sp.no_export_43 IS NULL)
  AND (o.anonymous_visit = 'N' OR o.anonymous_visit IS NULL)
  AND (%s = '' OR o.ovstist = %s)
ORDER BY o.vn
"""
