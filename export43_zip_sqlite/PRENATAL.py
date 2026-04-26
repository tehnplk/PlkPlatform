# 43 แฟ้ม (SQLite/F43.db): PRENATAL
COLUMNS = [
    'hospcode',
    'pid',
    'gravida',
    'lmp',
    'edc',
    'vdrl_result',
    'hb_result',
    'hiv_result',
    'date_hct',
    'hct_result',
    'thalassemia',
    'd_update',
    'provider',
    'cid',
    'height',
]

SQL = """
SELECT "hospcode", "pid", "gravida", "lmp", "edc", "vdrl_result", "hb_result", "hiv_result", "date_hct", "hct_result", "thalassemia", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "provider", "cid", "height" FROM "PRENATAL"
WHERE "lmp" BETWEEN ? AND ?
  AND (? = '' OR "pid" IN (SELECT DISTINCT "pid" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
