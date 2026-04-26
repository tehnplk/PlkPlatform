# 43 แฟ้ม: PROVIDER
COLUMNS = [
    'hospcode',
    'provider',
    'registerno',
    'council',
    'cid',
    'prename',
    'name',
    'lname',
    'sex',
    'birth',
    'providertype',
    'startdate',
    'outdate',
    'movefrom',
    'moveto',
    'd_update',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(d.code, '') AS provider,
  COALESCE(d.licenseno, '') AS registerno,
  COALESCE(d.council_code, '') AS council,
  COALESCE(d.cid, '') AS cid,
  COALESCE(d.pname, '') AS prename,
  COALESCE(d.fname, d.name, '') AS name,
  COALESCE(d.lname, d.shortname, '') AS lname,
  COALESCE(d.sex, '') AS sex,
  COALESCE(DATE_FORMAT(d.birth_date, '%%Y%%m%%d'), '') AS birth,
  COALESCE(d.provider_type_code, '') AS providertype,
  COALESCE(DATE_FORMAT(d.start_date, '%%Y%%m%%d'), '') AS startdate,
  COALESCE(DATE_FORMAT(d.finish_date, '%%Y%%m%%d'), '') AS outdate,
  COALESCE(d.move_from_hospcode, '') AS movefrom,
  COALESCE(d.move_to_hospcode, '') AS moveto,
  COALESCE(DATE_FORMAT(d.update_datetime, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update
FROM doctor d
WHERE d.code IS NOT NULL AND %s <= %s AND %s = %s
"""
