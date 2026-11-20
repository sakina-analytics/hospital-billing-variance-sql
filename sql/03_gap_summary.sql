-- Rolls the patient-level gaps up by cost head and status. Reads the temp view built by run_analysis.py.
SELECT cost_head, status,
       COUNT(*)        AS lines,
       SUM(amount_gap) AS net_gap_tzs
FROM patient_gaps
WHERE status <> 'Match'
GROUP BY cost_head, status
ORDER BY cost_head, status;
