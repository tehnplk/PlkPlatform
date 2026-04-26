# 43 แฟ้ม (SQLite/F43.db): DENTAL
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'denttype',
    'servplace',
    'pteeth',
    'pcaries',
    'pfilling',
    'pextract',
    'dteeth',
    'dcaries',
    'dfilling',
    'dextract',
    'need_fluoride',
    'need_scaling',
    'need_sealant',
    'need_pfilling',
    'need_dfilling',
    'need_pextract',
    'need_dextract',
    'nprosthesis',
    'permanent_permanent',
    'permanent_prosthesis',
    'prosthesis_prosthesis',
    'gum',
    'schooltype',
    'class',
    'provider',
    'd_update',
    'cid',
]

SQL = """
SELECT "hospcode", "pid", "seq", "date_serv", "denttype", "servplace", "pteeth", "pcaries", "pfilling", "pextract", "dteeth", "dcaries", "dfilling", "dextract", "need_fluoride", "need_scaling", "need_sealant", "need_pfilling", "need_dfilling", "need_pextract", "need_dextract", "nprosthesis", "permanent_permanent", "permanent_prosthesis", "prosthesis_prosthesis", "gum", "schooltype", "class", "provider", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update", "cid" FROM "DENTAL"
WHERE "date_serv" BETWEEN ? AND ?
  AND (? = '' OR "seq" IN (SELECT "seq" FROM "SERVICE" WHERE CAST(NULLIF("typein", '') AS INTEGER) = CAST(? AS INTEGER)))
"""
