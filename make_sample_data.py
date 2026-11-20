"""Creates made-up manual bill and hospital system (HIS) data.

Run:  python make_sample_data.py
Writes data/manual_bills.csv and data/his_charges.csv. Same result every time (fixed seed).
The hospital, patients and every number are fictional.
"""
import csv, os, random

random.seed(2026)
MONTHS = ["2026-07", "2026-08", "2026-09", "2026-10"]
PATIENTS_PER_MONTH = 320

# unit rates (made up, in TZS)
IPD_RATE, DIALYSIS_RATE, ICU_RATE, HDU_RATE = 20_000, 180_000, 400_000, 150_000
SURGERIES = [("Caesarean section", 650_000, 40), ("Appendectomy", 500_000, 25),
             ("Hernia repair", 450_000, 20), ("Hip replacement", 3_500_000, 5),
             ("Hysterectomy", 900_000, 10)]          # (name, rate, weight)


def surgery_rate():
    names, rates, weights = zip(*SURGERIES)
    i = random.choices(range(len(SURGERIES)), weights=weights)[0]
    return rates[i]


manual, his = [], []
pid = 10000
for month in MONTHS:
    for _ in range(PATIENTS_PER_MONTH):
        pid += 1
        p = f"P{pid}"
        lines = []                                   # (head, units, rate)
        if random.random() < 0.45:
            lines.append(("IPD", random.randint(1, 8), IPD_RATE))
        if random.random() < 0.09:
            lines.append(("SURGERY", 1, surgery_rate()))
        if random.random() < 0.05:
            lines.append(("DIALYSIS", random.randint(4, 12), DIALYSIS_RATE))
        if random.random() < 0.04:
            lines.append(("ICU", random.randint(1, 5), ICU_RATE))
        if random.random() < 0.03:
            lines.append(("HDU", random.randint(1, 4), HDU_RATE))
        if random.random() < 0.70:
            lines.append(("PHARMACY", None, None))
        if random.random() < 0.90:
            lines.append(("CONSULTATION", None, None))

        for head, units, rate in lines:
            if head == "PHARMACY":
                amount = round(random.lognormvariate(11.2, 0.7), -2)      # about 70,000 typical
            elif head == "CONSULTATION":
                amount = random.choice([10_000, 15_000, 20_000, 30_000])
            else:
                amount = units * rate
            manual.append([p, month, head, units, rate, amount])

            # ---- what the hospital system recorded for the same line ----
            if random.random() < 0.06:               # line never entered in the system
                continue
            h_units, h_rate, h_amount = units, rate, amount
            if head == "IPD" and random.random() < 0.30:
                h_units = units + 1                  # system charges the night of admission too
                h_amount = h_units * rate
            elif head == "SURGERY" and random.random() < 0.18:
                h_rate = round(rate * random.choice([0.85, 0.9, 1.1]), -3)   # package price differs
                h_amount = units * h_rate
            elif head == "DIALYSIS" and random.random() < 0.20:
                h_units = max(1, units - random.randint(1, 2))               # sessions not entered
                h_amount = h_units * rate
            elif head == "ICU" and random.random() < 0.45:
                h_rate = IPD_RATE * 4                # charged at a lower room rate
                h_amount = units * h_rate
            elif head == "HDU" and random.random() < 0.30:
                h_units = max(1, units - 1)
                h_amount = h_units * rate
            elif head == "PHARMACY" and random.random() < 0.35:
                h_amount = round(amount * random.uniform(0.97, 1.04), -2)
            elif head == "CONSULTATION" and random.random() < 0.10:
                h_amount = amount + random.choice([5_000, 10_000])
            his.append([p, month, head, h_units, h_rate, h_amount])

        # lines that exist only in the hospital system
        if random.random() < 0.04:
            n = random.randint(1, 3)
            his.append([p, month, "IPD", n, IPD_RATE, n * IPD_RATE])

os.makedirs("data", exist_ok=True)
for name, rows in (("manual_bills", manual), ("his_charges", his)):
    with open(f"data/{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["patient_id", "month", "cost_head", "units", "rate", "amount"])
        for r in rows:
            w.writerow(["" if v is None else (int(v) if isinstance(v, float) and v == int(v) else v) for v in r])
print(f"manual_bills.csv: {len(manual)} lines | his_charges.csv: {len(his)} lines")
