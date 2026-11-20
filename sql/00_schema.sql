-- Tables for the manual bill vs hospital system (HIS) comparison.
-- All data in this project is made up.

DROP TABLE IF EXISTS cost_heads;
DROP TABLE IF EXISTS manual_bills;
DROP TABLE IF EXISTS his_charges;

-- The rows of the summary table, in the order they are shown.
CREATE TABLE cost_heads (
    head_order INTEGER PRIMARY KEY,
    cost_head  TEXT NOT NULL UNIQUE,   -- e.g. 'ICU'
    label      TEXT NOT NULL,          -- e.g. 'ICU COST'
    has_units  INTEGER NOT NULL        -- 1 = counted in days/sessions/cases, 0 = amount only
);

-- One row per line on the paper (manual) bill.
CREATE TABLE manual_bills (
    patient_id TEXT NOT NULL,          -- patient ID only, no names
    month      TEXT NOT NULL,          -- 'YYYY-MM'
    cost_head  TEXT NOT NULL REFERENCES cost_heads(cost_head),
    units      REAL,                   -- NULL for pharmacy and consultation
    rate       REAL,                   -- NULL for pharmacy and consultation
    amount     REAL NOT NULL
);

-- One row per charge in the hospital system.
CREATE TABLE his_charges (
    patient_id TEXT NOT NULL,
    month      TEXT NOT NULL,
    cost_head  TEXT NOT NULL REFERENCES cost_heads(cost_head),
    units      REAL,
    rate       REAL,
    amount     REAL NOT NULL
);

CREATE INDEX idx_manual ON manual_bills (month, cost_head, patient_id);
CREATE INDEX idx_his    ON his_charges  (month, cost_head, patient_id);

INSERT INTO cost_heads (head_order, cost_head, label, has_units) VALUES
    (1, 'IPD',          'IPD NIGHTS TOTAL COST', 1),
    (2, 'SURGERY',      'SURGERIES COST',        1),
    (3, 'DIALYSIS',     'DIALYSIS COST',         1),
    (4, 'ICU',          'ICU COST',              1),
    (5, 'HDU',          'HDU COST',              1),
    (6, 'PHARMACY',     'PHARMACY',              0),
    (7, 'CONSULTATION', 'CONSULTATION',          0);
