# 43 แฟ้ม: LABFU
COLUMNS = [
    'hospcode',
    'pid',
    'seq',
    'date_serv',
    'labtest',
    'labresult',
    'd_update',
    'labplace',
    'cid',
    'provider',
]

SQL = """
SELECT
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS hospcode,
  COALESCE(LPAD(CAST(ps.person_id AS CHAR), 6, '0'), o.hn, '') AS pid,
  CAST(COALESCE(q.seq_id, '') AS CHAR) AS seq,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d'), '') AS date_serv,
  COALESCE(lo.lab_items_code, '') AS labtest,
  COALESCE(lo.lab_order_result, '') AS labresult,
  COALESCE(DATE_FORMAT(o.vstdate, '%%Y%%m%%d%%H%%i%%s'), '') AS d_update,
  COALESCE((SELECT hospitalcode FROM opdconfig LIMIT 1), '') AS labplace,
  COALESCE(pt.cid, '') AS cid,
  COALESCE(o.doctor, '') AS provider
FROM lab_order lo
JOIN lab_head lh ON lh.lab_order_number = lo.lab_order_number
JOIN ovst o ON o.vn = lh.vn
LEFT JOIN ovst_seq q ON q.vn = o.vn
LEFT JOIN patient pt ON pt.hn = o.hn
LEFT JOIN person ps ON ps.cid = pt.cid AND pt.cid IS NOT NULL AND pt.cid <> ''
WHERE o.vstdate BETWEEN %s AND %s
  AND (%s = '' OR o.ovstist = %s)
"""
