-- HIS to Manual Revenue Variance: one row per cost head, plus a Total row.
-- Parameter :month is 'ALL' or a month such as '2026-09'.
--   Unit Var = (HIS Units - Manual Units) / Manual Units
--   Rate Var = (HIS Rev   - Manual Rev)   / Manual Rev      (revenue variance, as in the reporting layout)
WITH m AS (
    SELECT cost_head, SUM(units) AS units, SUM(amount) AS rev
    FROM manual_bills
    WHERE :month = 'ALL' OR month = :month
    GROUP BY cost_head
),
h AS (
    SELECT cost_head, SUM(units) AS units, SUM(amount) AS rev
    FROM his_charges
    WHERE :month = 'ALL' OR month = :month
    GROUP BY cost_head
),
lines AS (
    SELECT c.head_order,
           c.label                                   AS name,
           CASE WHEN c.has_units = 1 THEN COALESCE(m.units, 0) END AS manual_units,
           COALESCE(m.rev, 0)                        AS manual_rev,
           CASE WHEN c.has_units = 1 THEN COALESCE(h.units, 0) END AS his_units,
           COALESCE(h.rev, 0)                        AS his_rev
    FROM cost_heads c
    LEFT JOIN m ON m.cost_head = c.cost_head
    LEFT JOIN h ON h.cost_head = c.cost_head
)
SELECT head_order, name, manual_units, manual_rev, his_units, his_rev,
       CASE WHEN manual_units > 0 THEN ROUND(1.0 * (his_units - manual_units) / manual_units, 4) END AS unit_var,
       CASE WHEN manual_rev   > 0 THEN ROUND(1.0 * (his_rev   - manual_rev)   / manual_rev,   4) END AS rate_var
FROM lines
UNION ALL
SELECT 99, 'Total', NULL, SUM(manual_rev), NULL, SUM(his_rev), NULL,
       ROUND(1.0 * (SUM(his_rev) - SUM(manual_rev)) / SUM(manual_rev), 4)
FROM lines
ORDER BY head_order;
