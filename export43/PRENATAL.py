# 43 แฟ้ม: PRENATAL
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
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), ah.hn, '') AS pid,
  COALESCE(CAST(ah.preg_no AS CHAR), '') AS gravida,
  COALESCE(DATE_FORMAT(ah.last_menses_date, '%%Y%%m%%d'), '') AS lmp,
  COALESCE(DATE_FORMAT(ah.estimate_delivery_date, '%%Y%%m%%d'), '') AS edc,
  '' AS vdrl_result, '' AS hb_result, '' AS hiv_result,
  '' AS date_hct, '' AS hct_result, '' AS thalassemia,
  '' AS d_update,
  '' AS provider,
  COALESCE(pt.cid, '') AS cid,
  '' AS height
FROM anc_head ah
LEFT JOIN patient pt ON pt.hn = ah.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE ah.last_menses_date BETWEEN %s AND %s
  AND (%s = '' OR %s = '')
"""
