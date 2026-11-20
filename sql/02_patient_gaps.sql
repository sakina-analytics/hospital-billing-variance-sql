-- Compares the two systems patient by patient, month by month and cost head by cost head.
-- Every pair gets one status, so the gap in the summary can be traced to specific patients.
WITH m AS (
    SELECT patient_id, month, cost_head,
           SUM(units) AS units, SUM(amount) AS amount,
           CASE WHEN SUM(units) > 0 THEN SUM(amount) / SUM(units) END AS rate
    FROM manual_bills GROUP BY patient_id, month, cost_head
),
h AS (
    SELECT patient_id, month, cost_head,
           SUM(units) AS units, SUM(amount) AS amount,
           CASE WHEN SUM(units) > 0 THEN SUM(amount) / SUM(units) END AS rate
    FROM his_charges GROUP BY patient_id, month, cost_head
),
keys AS (
    SELECT patient_id, month, cost_head FROM m
    UNION
    SELECT patient_id, month, cost_head FROM h
)
SELECT k.patient_id, k.month, k.cost_head,
       m.units  AS manual_units, ROUND(m.rate) AS manual_rate, m.amount AS manual_amount,
       h.units  AS his_units,    ROUND(h.rate) AS his_rate,    h.amount AS his_amount,
       COALESCE(h.amount, 0) - COALESCE(m.amount, 0) AS amount_gap,
       CASE
           WHEN m.amount IS NULL THEN 'Only in HIS'
           WHEN h.amount IS NULL THEN 'Missing in HIS'
           WHEN COALESCE(m.units, 0) <> COALESCE(h.units, 0) THEN 'Units differ'
           WHEN ABS(m.amount - h.amount) > 0.5 THEN 'Rate or amount differs'
           ELSE 'Match'
       END AS status
FROM keys k
LEFT JOIN m ON m.patient_id = k.patient_id AND m.month = k.month AND m.cost_head = k.cost_head
LEFT JOIN h ON h.patient_id = k.patient_id AND h.month = k.month AND h.cost_head = k.cost_head
ORDER BY k.month, k.cost_head, k.patient_id;
