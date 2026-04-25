"""SQL mapping จาก HOSXP source tables (hos_*) → output schema ตาม temp.tmp_exp_3090_*

แต่ละ query คืน column ลำดับเดียวกับตาราง tmp_exp_3090_<file> เพื่อให้ output .TXT
มีรูปแบบเหมือนกับที่ vendor สร้าง

อ้างอิง: docs/vendor_hos_07547_source_selects.sql (capture จาก general_log)
"""
from __future__ import annotations


# คอลัมน์ตามลำดับ schema ของ temp.tmp_exp_3090_*
PERSON_COLUMNS = [
    "hospcode", "cid", "pid", "hid", "prename", "name", "lname", "hn",
    "sex", "birth", "mstatus", "occupation_old", "occupation_new",
    "race", "nation", "religion", "education", "fstatus",
    "father", "mother", "couple", "vstatus", "movein",
    "discharge", "ddischarge", "abogroup", "rhgroup", "labor",
    "passport", "typearea", "d_update", "telephone", "mobile",
]

SERVICE_COLUMNS = [
    "hospcode", "pid", "hn", "seq", "date_serv", "time_serv",
    "location", "intime", "instype", "insid", "main", "typein",
    "referinhosp", "causein", "chiefcomp", "servplace",
    "btemp", "sbp", "dbp", "pr", "rr",
    "typeout", "referouthosp", "causeout",
    "cost", "price", "payprice", "actualpay",
    "d_update", "hsub", "cid",
]

DIAGNOSIS_OPD_COLUMNS = [
    "hospcode", "pid", "seq", "date_serv", "diagtype", "diagcode",
    "clinic", "provider", "d_update", "cid",
]


# ----------------------------------------------------------------- PERSON
# ดึงประชากรที่ลงทะเบียนกับ รพสต./รพ. (ตาราง person) JOIN patient เพื่อดึง hn
# date filter ใช้ p.last_update (กรองเฉพาะที่อัปเดตในช่วงนั้น) — ถ้าต้องการครบทั้งหมดใช้ '00000000'-'99999999'
PERSON_SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(p.cid, '')                                          AS cid,
  CAST(p.person_id AS CHAR)                                    AS pid,
  CAST(COALESCE(p.house_id, '') AS CHAR)                       AS hid,
  COALESCE(pn.provis_code, '')                                 AS prename,
  COALESCE(p.fname, '')                                        AS name,
  COALESCE(p.lname, '')                                        AS lname,
  COALESCE(pt.hn, '')                                          AS hn,
  COALESCE(p.sex, '')                                          AS sex,
  COALESCE(DATE_FORMAT(p.birthdate, '%%Y%%m%%d'), '')          AS birth,
  COALESCE(p.marrystatus, '')                                  AS mstatus,
  COALESCE(oc.nhso_code, '')                                   AS occupation_old,
  COALESCE(oc.nhso_code, '')                                   AS occupation_new,
  COALESCE(nt.nhso_code, '')                                   AS race,
  COALESCE(nt2.nhso_code, '')                                  AS nation,
  COALESCE(rl.nhso_code, '')                                   AS religion,
  COALESCE(ed.provis_code, '')                                 AS education,
  COALESCE(CAST(p.person_house_position_id AS CHAR), '')       AS fstatus,
  COALESCE(p.father_cid, '')                                   AS father,
  COALESCE(p.mother_cid, '')                                   AS mother,
  COALESCE(p.sps_cid, '')                                      AS couple,
  COALESCE(hr.export_code, '')                                 AS vstatus,
  COALESCE(DATE_FORMAT(p.movein_date, '%%Y%%m%%d'), '')        AS movein,
  COALESCE(CAST(p.person_discharge_id AS CHAR), '9')           AS discharge,
  COALESCE(DATE_FORMAT(p.discharge_date, '%%Y%%m%%d'), '')     AS ddischarge,
  COALESCE(pb.code, '')                                        AS abogroup,
  ''                                                           AS rhgroup,
  COALESCE(pl.nhso_code, '')                                   AS labor,
  ''                                                           AS passport,
  COALESCE(CAST(p.house_regist_type_id AS CHAR), '')           AS typearea,
  COALESCE(DATE_FORMAT(p.last_update, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(p.hometel, '')                                      AS telephone,
  COALESCE(p.mobile_phone, '')                                 AS mobile
FROM person p
LEFT JOIN patient pt ON pt.cid = p.cid
  AND p.cid IS NOT NULL AND p.cid <> '' AND p.cid NOT LIKE '%%00000000%%'
LEFT JOIN occupation oc ON oc.occupation = p.occupation
LEFT JOIN nationality nt ON nt.nationality = p.nationality
LEFT JOIN nationality nt2 ON nt2.nationality = p.citizenship
LEFT JOIN religion rl ON rl.religion = p.religion
LEFT JOIN education ed ON ed.education = p.education
LEFT JOIN provis_bgroup pb ON pb.name = p.blood_group
LEFT JOIN house_regist_type hr ON hr.house_regist_type_id = p.house_regist_type_id
LEFT JOIN pname pn ON pn.name = p.pname
LEFT JOIN person_labor_type pl ON pl.person_labor_type_id = p.person_labor_type_id
WHERE p.cid IS NOT NULL
  AND p.cid <> ''
  AND DATE(p.last_update) BETWEEN %s AND %s
ORDER BY p.person_id
"""


# ----------------------------------------------------------------- SERVICE
# ตามคิวรี่ของ vendor (line 270 ของ vendor_hos_07547_source_selects.sql)
# กรองด้วย vstdate range + spclty.no_export_43 + anonymous_visit
SERVICE_SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '')   AS hospcode,
  CAST(COALESCE(ps.person_id, '') AS CHAR)                     AS pid,
  COALESCE(o.hn, '')                                           AS hn,
  CAST(COALESCE(q.seq_id, '') AS CHAR)                         AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '')            AS date_serv,
  COALESCE(DATE_FORMAT(o.vsttime, '%%H%%i%%s'), '')            AS time_serv,
  COALESCE(CAST(o.visit_type AS CHAR), '')                     AS location,
  ''                                                           AS intime,
  COALESCE(pts.code, y.nhso_code, '')                          AS instype,
  COALESCE(o.pttypeno, '')                                     AS insid,
  COALESCE(o.hospmain, '')                                     AS main,
  COALESCE(oi.export_code, '')                                 AS typein,
  COALESCE(rf.refer_hospcode, '')                              AS referinhosp,
  ''                                                           AS causein,
  COALESCE(s.cc, '')                                           AS chiefcomp,
  ''                                                           AS servplace,
  COALESCE(CAST(s.temperature AS CHAR), '')                    AS btemp,
  COALESCE(CAST(s.bps AS CHAR), '')                            AS sbp,
  COALESCE(CAST(s.bpd AS CHAR), '')                            AS dbp,
  COALESCE(CAST(s.pulse AS CHAR), '')                          AS pr,
  COALESCE(CAST(s.rr AS CHAR), '')                             AS rr,
  COALESCE(oo.export_code, '')                                 AS typeout,
  COALESCE(ro.refer_hospcode, '')                              AS referouthosp,
  COALESCE(rc1.export_code, '')                                AS causeout,
  COALESCE(CAST(v.income AS CHAR), '')                         AS cost,
  COALESCE(CAST(v.income AS CHAR), '')                         AS price,
  COALESCE(CAST(v.rcpt_money AS CHAR), '')                     AS payprice,
  COALESCE(CAST(v.rcpt_money AS CHAR), '')                     AS actualpay,
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
ORDER BY o.vn
"""


# ----------------------------------------------------------------- DIAGNOSIS_OPD
# ตามคิวรี่ของ vendor (line 279)
DIAGNOSIS_OPD_SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '')   AS hospcode,
  CAST(COALESCE(ps.person_id, '') AS CHAR)                     AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR)                         AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '')            AS date_serv,
  COALESCE(d.diagtype, '')                                     AS diagtype,
  COALESCE(d.icd10, '')                                        AS diagcode,
  COALESCE(sp.provis_code, '')                                 AS clinic,
  COALESCE(d.doctor, '')                                       AS provider,
  COALESCE(DATE_FORMAT(d.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE(pt.cid, '')                                         AS cid
FROM ovstdiag d
JOIN ovst o          ON o.vn = d.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps  ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN spclty sp  ON sp.spclty = o.spclty
WHERE o.vstdate BETWEEN %s AND %s
ORDER BY o.vn, d.diagtype
"""


# ลงทะเบียน mapping: file_name (uppercase) → (columns, sql)
QUERIES: dict[str, tuple[list[str], str]] = {
    "PERSON":         (PERSON_COLUMNS,        PERSON_SQL),
    "SERVICE":        (SERVICE_COLUMNS,       SERVICE_SQL),
    "DIAGNOSIS_OPD":  (DIAGNOSIS_OPD_COLUMNS, DIAGNOSIS_OPD_SQL),
}
