# 43 แฟ้ม (SQLite/F43.db): PERSON
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
SELECT "hospcode", "cid", "pid", "hid", "prename", "name", "lname", "hn", "sex", "birth", "mstatus", "occupation_old", "occupation_new", "race", "nation", "religion", "education", "fstatus", "father", "mother", "couple", "vstatus", "movein", "discharge", "ddischarge", "abogroup", "rhgroup", "labor", "passport", "typearea", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "telephone", "mobile" FROM "PERSON"
WHERE "pid" IN (
  SELECT DISTINCT "pid" FROM "SERVICE"
  WHERE "date_serv" BETWEEN ? AND ?
    AND (? = '' OR CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER))
)
"""
