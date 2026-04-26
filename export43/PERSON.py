# 43 แฟ้ม: PERSON
COLUMNS = [
    'hospcode',
    'cid',
    'pid',
    'hid',
    'prename',
    'name',
    'lname',
    'hn',
    'sex',
    'birth',
    'mstatus',
    'occupation_old',
    'occupation_new',
    'race',
    'nation',
    'religion',
    'education',
    'fstatus',
    'father',
    'mother',
    'couple',
    'vstatus',
    'movein',
    'discharge',
    'ddischarge',
    'abogroup',
    'rhgroup',
    'labor',
    'passport',
    'typearea',
    'd_update',
    'telephone',
    'mobile',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(p.cid, '')                                          AS cid,
  LPAD(CAST(p.person_id AS CHAR), 6, '0')                      AS pid,
  CAST(COALESCE(p.house_id, '') AS CHAR)                       AS hid,
  COALESCE(pn.provis_code, '')                                 AS prename,
  COALESCE(p.fname, '')                                        AS name,
  COALESCE(p.lname, '')                                        AS lname,
  COALESCE(pt.hn, '')                                          AS hn,
  COALESCE(p.sex, '')                                          AS sex,
  COALESCE(DATE_FORMAT(p.birthdate, '%%Y%%m%%d'), '')          AS birth,
  COALESCE(p.marrystatus, '')                                  AS mstatus,
  COALESCE(oc.occupation, '')                                  AS occupation_old,
  COALESCE(oc.nhso_code, '')                                   AS occupation_new,
  COALESCE(nt.nhso_code, '')                                   AS race,
  COALESCE(nt2.nhso_code, '')                                  AS nation,
  COALESCE(rl.nhso_code, '')                                   AS religion,
  COALESCE(LPAD(ed.provis_code, 2, '0'), '')                   AS education,
  COALESCE(CAST(p.person_house_position_id AS CHAR), '')       AS fstatus,
  COALESCE(p.father_cid, '')                                   AS father,
  COALESCE(p.mother_cid, '')                                   AS mother,
  COALESCE(p.sps_cid, '')                                      AS couple,
  CASE
    WHEN EXISTS (
      SELECT 1
      FROM village_organization_member vom
      JOIN village_organization vo
        ON vo.village_organization_id = vom.village_organization_id
      WHERE vom.person_id = p.person_id
        AND (
          vo.village_organization_type_id = 1
          OR vom.village_org_member_type_id = 1
        )
    ) THEN '2'
    WHEN EXISTS (
      SELECT 1
      FROM village_organization_member vom
      JOIN village_organization vo
        ON vo.village_organization_id = vom.village_organization_id
      WHERE vom.person_id = p.person_id
        AND vo.village_organization_type_id = 4
    ) THEN '4'
    ELSE '5'
  END                                                          AS vstatus,
  COALESCE(DATE_FORMAT(p.movein_date, '%%Y%%m%%d'), '')        AS movein,
  CASE
    WHEN p.person_discharge_id IN (1, 2, 3, 9)
      THEN CAST(p.person_discharge_id AS CHAR)
    ELSE '9'
  END                                                          AS discharge,
  COALESCE(DATE_FORMAT(p.discharge_date, '%%Y%%m%%d'), '')     AS ddischarge,
  CASE
    WHEN p.blood_group IS NULL OR p.blood_group = '' THEN ''
    WHEN p.blood_group LIKE 'A%%'  AND p.blood_group NOT LIKE 'AB%%' THEN '1'
    WHEN p.blood_group LIKE 'B%%'  THEN '2'
    WHEN p.blood_group LIKE 'AB%%' THEN '3'
    WHEN p.blood_group LIKE 'O%%'  THEN '4'
    ELSE '9'
  END                                                          AS abogroup,
  CASE
    WHEN p.bloodgroup_rh LIKE '%%+%%' THEN '1'
    WHEN p.bloodgroup_rh LIKE '%%-%%' THEN '2'
    ELSE ''
  END                                                          AS rhgroup,
  COALESCE(pl.nhso_code, '')                                   AS labor,
  COALESCE(pt.passport_no, '')                                 AS passport,
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
LEFT JOIN pname pn ON pn.name = p.pname
LEFT JOIN person_labor_type pl ON pl.person_labor_type_id = p.person_labor_type_id
WHERE EXISTS (
    SELECT 1
    FROM ovst o2
    JOIN patient pt2 ON pt2.hn = o2.hn
    LEFT JOIN spclty sp2 ON sp2.spclty = o2.spclty
    WHERE pt2.cid = p.cid
      AND o2.vstdate BETWEEN %s AND %s
      AND (sp2.no_export_43 = 'N' OR sp2.no_export_43 IS NULL)
      AND (o2.anonymous_visit = 'N' OR o2.anonymous_visit IS NULL)
      AND (%s = '' OR o2.ovstist = %s)
  )
UNION ALL
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(pt.cid, '')                                       AS cid,
  COALESCE(pt.hn, '')                                        AS pid,
  '000000'                                                   AS hid,
  COALESCE(pn.provis_code, '')                               AS prename,
  COALESCE(pt.fname, '')                                     AS name,
  COALESCE(pt.lname, '')                                     AS lname,
  COALESCE(pt.hn, '')                                        AS hn,
  COALESCE(pt.sex, '')                                       AS sex,
  COALESCE(DATE_FORMAT(pt.birthday, '%%Y%%m%%d'), '')        AS birth,
  COALESCE(pt.marrystatus, '')                               AS mstatus,
  COALESCE(oc.occupation, '')                                AS occupation_old,
  COALESCE(oc.nhso_code, '')                                 AS occupation_new,
  COALESCE(nt.nhso_code, '')                                 AS race,
  COALESCE(nt2.nhso_code, '')                                AS nation,
  COALESCE(rl.nhso_code, '')                                 AS religion,
  COALESCE(LPAD(ed.provis_code, 2, '0'), '')                 AS education,
  '2'                                                        AS fstatus,
  COALESCE(pt.father_cid, '')                                AS father,
  COALESCE(pt.mother_cid, '')                                AS mother,
  COALESCE(pt.couple_cid, '')                                AS couple,
  '5'                                                        AS vstatus,
  ''                                                         AS movein,
  CASE WHEN pt.deathday IS NOT NULL THEN '1' ELSE '9' END    AS discharge,
  COALESCE(DATE_FORMAT(pt.deathday, '%%Y%%m%%d'), '')        AS ddischarge,
  CASE
    WHEN pt.bloodgrp IS NULL OR pt.bloodgrp = '' THEN ''
    WHEN pt.bloodgrp LIKE 'A%%'  AND pt.bloodgrp NOT LIKE 'AB%%' THEN '1'
    WHEN pt.bloodgrp LIKE 'B%%'  THEN '2'
    WHEN pt.bloodgrp LIKE 'AB%%' THEN '3'
    WHEN pt.bloodgrp LIKE 'O%%'  THEN '4'
    ELSE '9'
  END                                                        AS abogroup,
  ''                                                         AS rhgroup,
  COALESCE(pl.nhso_code, '')                                 AS labor,
  COALESCE(pt.passport_no, '')                               AS passport,
  COALESCE(pt.type_area, '')                                 AS typearea,
  COALESCE(DATE_FORMAT(pt.last_update, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  ''                                                         AS telephone,
  ''                                                         AS mobile
FROM patient pt
LEFT JOIN person p ON p.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
LEFT JOIN occupation oc ON oc.occupation = pt.occupation
LEFT JOIN nationality nt ON nt.nationality = pt.nationality
LEFT JOIN nationality nt2 ON nt2.nationality = pt.citizenship
LEFT JOIN religion rl ON rl.religion = pt.religion
LEFT JOIN education ed ON ed.education = pt.educate
LEFT JOIN pname pn ON pn.name = pt.pname
LEFT JOIN person_labor_type pl ON pl.person_labor_type_id = pt.person_labor_type_id
WHERE p.person_id IS NULL
  AND EXISTS (
    SELECT 1
    FROM ovst o2
    LEFT JOIN spclty sp2 ON sp2.spclty = o2.spclty
    WHERE o2.hn = pt.hn
      AND o2.vstdate BETWEEN %s AND %s
      AND (sp2.no_export_43 = 'N' OR sp2.no_export_43 IS NULL)
      AND (o2.anonymous_visit = 'N' OR o2.anonymous_visit IS NULL)
      AND (%s = '' OR o2.ovstist = %s)
  )
ORDER BY pid
"""
