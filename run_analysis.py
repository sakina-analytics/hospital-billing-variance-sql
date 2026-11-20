"""Loads the made-up CSVs into SQLite, runs the SQL files and writes the results to outputs/.

Run:
    python make_sample_data.py     # only needed once
    python run_analysis.py
"""
import csv
import os
import sqlite3

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

DB = "data/hospital_billing.db"
OUT = "outputs"
HEADERS = ["Name", "Manual Units", "Manual Rev", "HIS Units", "HIS Rev", "Unit Var", "Rate Var"]


def read_sql(name):
    with open(os.path.join("sql", name)) as f:
        return f.read()


def load_csv(con, table, path):
    with open(path, newline="") as f:
        rows = [[None if v == "" else v for v in r] for r in list(csv.reader(f))[1:]]
    con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?,?)", rows)


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(read_sql("00_schema.sql"))
    load_csv(con, "manual_bills", "data/manual_bills.csv")
    load_csv(con, "his_charges", "data/his_charges.csv")
    con.commit()

    months = [r[0] for r in con.execute("SELECT DISTINCT month FROM manual_bills ORDER BY month")]
    summary_sql = read_sql("01_variance_summary.sql")
    results = {}
    for scope in ["ALL"] + months:
        rows = con.execute(summary_sql, {"month": scope}).fetchall()
        results[scope] = rows
        label = "all_months" if scope == "ALL" else scope
        write_csv(f"{OUT}/variance_summary_{label}.csv", ["head_order"] + [h.lower().replace(" ", "_") for h in HEADERS], rows)

    # patient-level gaps, kept in a temp table so the roll-up query can read it
    cur = con.execute(read_sql("02_patient_gaps.sql"))
    gap_header = [d[0] for d in cur.description]
    gaps = cur.fetchall()
    con.execute("CREATE TEMP TABLE patient_gaps (%s)" % ", ".join(gap_header))
    con.executemany("INSERT INTO patient_gaps VALUES (%s)" % ",".join("?" * len(gap_header)), gaps)
    write_csv(f"{OUT}/patient_gaps.csv", gap_header, [g for g in gaps if g[-1] != "Match"])
    gap_summary = con.execute(read_sql("03_gap_summary.sql")).fetchall()
    write_csv(f"{OUT}/gap_summary.csv", ["cost_head", "status", "lines", "net_gap_tzs"], gap_summary)

    # check: the revenue gap in the summary must equal the sum of the patient-level gaps
    total_row = [r for r in results["ALL"] if r[1] == "Total"][0]
    summary_gap = total_row[5] - total_row[3]
    patient_gap = sum(g[-2] for g in gaps)
    assert abs(summary_gap - patient_gap) < 0.5, (summary_gap, patient_gap)
    print(f"Check passed: summary gap {summary_gap:,.0f} TZS = sum of patient-level gaps {patient_gap:,.0f} TZS")

    write_workbook(results, gap_summary)
    print(f"Wrote {OUT}/variance_summary.xlsx and CSV files")
    con.close()


def write_workbook(results, gap_summary):
    font = lambda **k: Font(name="Arial", **k)
    head_fill = PatternFill("solid", fgColor="1F3A5F")
    total_fill = PatternFill("solid", fgColor="E8EDF3")
    thin = Side(style="thin", color="C9D1DA")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    wb = Workbook()
    wb.remove(wb.active)
    for scope, rows in results.items():
        ws = wb.create_sheet("All months" if scope == "ALL" else scope)
        ws.sheet_view.showGridLines = False
        ws["A1"] = "HIS to Manual Revenue Variance - " + ("All months" if scope == "ALL" else scope)
        ws["A1"].font = font(size=14, bold=True, color="1F3A5F")
        ws["A2"] = "Made-up data. TZS. Unit Var = (HIS Units - Manual Units) / Manual Units. Rate Var = (HIS Rev - Manual Rev) / Manual Rev."
        ws["A2"].font = font(size=9, italic=True, color="5C6B7A")
        for i, h in enumerate(HEADERS, 1):
            c = ws.cell(4, i, h)
            c.font = font(bold=True, color="FFFFFF"); c.fill = head_fill; c.border = box
            c.alignment = Alignment(horizontal="left" if i == 1 else "center")
        first = 5
        for n, r in enumerate(rows):
            row = first + n
            is_total = r[1] == "Total"
            ws.cell(row, 1, r[1])
            for col, val in ((2, r[2]), (3, r[3]), (4, r[4]), (5, r[5])):
                ws.cell(row, col, val)
            if not is_total:
                ws.cell(row, 6, f'=IF(N(B{row})=0,"",(D{row}-B{row})/B{row})')
                ws.cell(row, 7, f'=IF(N(C{row})=0,"",(E{row}-C{row})/C{row})')
            else:
                last = row - 1
                ws.cell(row, 3, f"=SUM(C{first}:C{last})")
                ws.cell(row, 5, f"=SUM(E{first}:E{last})")
                ws.cell(row, 7, f'=IF(C{row}=0,"",(E{row}-C{row})/C{row})')
            for col in range(1, 8):
                c = ws.cell(row, col)
                c.font = font(bold=is_total); c.border = box
                if is_total: c.fill = total_fill
                if col > 1: c.alignment = Alignment(horizontal="right")
                if col in (2, 4): c.number_format = "#,##0"
                if col in (3, 5): c.number_format = "#,##0"
                if col in (6, 7): c.number_format = "0%;[Red]-0%;0%"
        for col, w in zip("ABCDEFG", (26, 14, 18, 14, 18, 11, 11)):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "B5"
    ws = wb.create_sheet("Where the gap comes from")
    ws.sheet_view.showGridLines = False
    ws["A1"] = "Patient-level gaps by cost head and status (all months, made-up data)"
    ws["A1"].font = font(size=14, bold=True, color="1F3A5F")
    for i, h in enumerate(["Cost head", "Status", "Lines", "Net gap (HIS - Manual, TZS)"], 1):
        c = ws.cell(3, i, h); c.font = font(bold=True, color="FFFFFF"); c.fill = head_fill; c.border = box
    for n, r in enumerate(gap_summary):
        for i, v in enumerate(r, 1):
            c = ws.cell(4 + n, i, v); c.font = font(); c.border = box
            if i >= 3: c.number_format = "#,##0;[Red]-#,##0"
    for col, w in zip("ABCD", (16, 26, 10, 28)):
        ws.column_dimensions[col].width = w
    wb.save(f"{OUT}/variance_summary.xlsx")


if __name__ == "__main__":
    main()
