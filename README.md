# Hospital billing variance: manual bills vs hospital system (SQL + Python)

A small project that compares what was written on **paper (manual) bills** with what the **hospital information system (HIS)** recorded, and shows where the revenue gap comes from.

> **All data here is made up.** The hospital, the patients (IDs like P10001) and every number are fictional and created by `make_sample_data.py`. No real hospital or patient data is in this repository.

## What it produces

A summary table in the reporting layout hospital finance teams use, for all months and for each month, plus a patient-by-patient trace of the gap.

**All months (Jul to Oct 2026), TZS**

| Name | Manual Units | Manual Rev | HIS Units | HIS Rev | Unit Var | Rate Var |
|---|---:|---:|---:|---:|---:|---:|
| IPD NIGHTS TOTAL COST | 2,679 | 53,580,000 | 2,759 | 55,180,000 | 3% | 3% |
| SURGERIES COST | 127 | 105,650,000 | 122 | 100,913,000 | -4% | -4% |
| DIALYSIS COST | 524 | 94,320,000 | 503 | 90,540,000 | -4% | -4% |
| ICU COST | 166 | 66,400,000 | 154 | 36,960,000 | -7% | -44% |
| HDU COST | 97 | 14,550,000 | 79 | 11,850,000 | -19% | -19% |
| PHARMACY |  | 85,028,100 |  | 79,864,900 |  | -6% |
| CONSULTATION |  | 21,735,000 |  | 21,335,000 |  | -2% |
| **Total** |  | 441,263,100 |  | 396,642,900 |  | -10% |

Pharmacy and consultation are amounts only, so their unit columns are blank.

**Where the gap comes from (all months)**

| Cost head | What happened | Lines | Net gap (TZS) |
|---|---|---:|---:|
| CONSULTATION | Missing in HIS | 72 | -1,240,000 |
| CONSULTATION | Rate or amount differs | 106 | 840,000 |
| DIALYSIS | Missing in HIS | 1 | -1,260,000 |
| DIALYSIS | Units differ | 8 | -2,520,000 |
| HDU | Missing in HIS | 4 | -1,500,000 |
| HDU | Units differ | 8 | -1,200,000 |
| ICU | Missing in HIS | 5 | -4,800,000 |
| ICU | Rate or amount differs | 24 | -24,640,000 |
| IPD | Missing in HIS | 38 | -3,460,000 |
| IPD | Only in HIS | 28 | 1,140,000 |
| IPD | Units differ | 168 | 3,920,000 |
| PHARMACY | Missing in HIS | 59 | -5,303,300 |
| PHARMACY | Rate or amount differs | 299 | 140,100 |
| SURGERY | Missing in HIS | 5 | -2,900,000 |
| SURGERY | Rate or amount differs | 27 | -1,837,000 |

In this made-up data the biggest single gap is ICU lines charged at a lower room rate in the HIS. Lines missing from the HIS account for most of the rest, while extra IPD nights charged in the HIS push the gap the other way.

## How the variances are calculated

- **Unit Var** = (HIS Units - Manual Units) / Manual Units
- **Rate Var** = (HIS Rev - Manual Rev) / Manual Rev. This is a revenue variance, kept under the "Rate Var" heading to match the reporting layout. It moves with both units and rate.
- **Total** adds up the revenue columns only.

## Run it

```
pip install -r requirements.txt
python make_sample_data.py     # creates data/manual_bills.csv and data/his_charges.csv
python run_analysis.py         # loads SQLite, runs the SQL, writes outputs/
```

`run_analysis.py` also checks that the revenue gap in the summary equals the sum of the patient-level gaps, and stops with an error if it does not.

## Files

| Path | What it is |
|---|---|
| `sql/00_schema.sql` | Tables and the list of cost heads |
| `sql/01_variance_summary.sql` | The summary table. Takes `:month` as `'ALL'` or `'2026-09'` |
| `sql/02_patient_gaps.sql` | Compares each patient, month and cost head, and labels it Match, Missing in HIS, Only in HIS, Units differ, or Rate or amount differs |
| `sql/03_gap_summary.sql` | Rolls the gaps up by cost head and status |
| `run_analysis.py` | Loads the CSVs into SQLite, runs the queries, writes CSV and Excel |
| `make_sample_data.py` | Creates the made-up data (fixed seed, same result every run) |
| `outputs/variance_summary.xlsx` | One sheet per month, plus All months and the gap roll-up. Variances are live formulas |
| `outputs/*.csv` | The same results as CSV, plus `patient_gaps.csv` listing every line that does not match |

## SQL used

CTEs, `LEFT JOIN`, `UNION` / `UNION ALL`, conditional aggregation with `CASE`, named parameters, and a patient-level full comparison built from a union of keys.
