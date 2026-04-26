# 43 แฟ้ม (SQLite/F43.db): VILLAGE
COLUMNS = [
    'hospcode',
    'vid',
    'ntraditional',
    'nmonk',
    'nreligionleader',
    'nbroadcast',
    'nradio',
    'npchc',
    'nclinic',
    'ndrugstore',
    'nchildcenter',
    'npschool',
    'nsschool',
    'ntemple',
    'nreligiousplace',
    'nmarket',
    'nshop',
    'nfoodshop',
    'nstall',
    'nraintank',
    'nchickenfarm',
    'npigfarm',
    'wastewater',
    'garbage',
    'nfactory',
    'latitude',
    'longitude',
    'outdate',
    'numactually',
    'risktype',
    'numstateless',
    'nexerciseclub',
    'nolderlyclub',
    'ndisableclub',
    'nnumberoneclub',
    'd_update',
]

SQL = """
SELECT "hospcode", "vid", "ntraditional", "nmonk", "nreligionleader", "nbroadcast", "nradio", "npchc", "nclinic", "ndrugstore", "nchildcenter", "npschool", "nsschool", "ntemple", "nreligiousplace", "nmarket", "nshop", "nfoodshop", "nstall", "nraintank", "nchickenfarm", "npigfarm", "wastewater", "garbage", "nfactory", "latitude", "longitude", "outdate", "numactually", "risktype", "numstateless", "nexerciseclub", "nolderlyclub", "ndisableclub", "nnumberoneclub", COALESCE(NULLIF("d_update", ''), strftime('%Y%m%d%H%M%S', 'now', 'localtime')) AS "d_update" FROM "VILLAGE"
WHERE ? = ? OR ? = ?  -- no real filter
"""
