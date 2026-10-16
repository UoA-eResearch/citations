"""Independent recomputation of field-month P95 straight from the raw CSVs (no code shared with build_series)."""
import sys, csv, math
import numpy as np, pandas as pd
RAW = sys.argv[1]; FM = pd.read_csv(sys.argv[2])
cases = {  # (field, month): list of (POC, gen_code lower)
    ("Wairakei", "2000-01"): [("WRK2201", "wairakei"), ("PPI2201", "poihipi")],
    ("Wairakei", "2016-06"): [("WRK2201", "wairakei"), ("PPI2201", "poihipi"), ("THI2201", "te_mihi")],
    ("Ohaaki", "2008-07"): [("OKI2201", "ohaaki")],
    ("Mokai", "2020-03"): [("WKM2201", "mokai")],
    ("Kawerau", "2023-05"): [("KAW1101", "kawerau_new"), ("KAW0111", "kawerau"), ("KAW0112", "norskeskog")],
    ("Rotokawa", "2012-04"): [("WRK0331", "rotokawa"), ("NAP2201", "nap")],
    ("Ngawha", "2015-09"): [("KOE1101", "ngawha")],
    ("Ngatamariki", "2019-01"): [("NAP2202", "ngatamariki")],
}
print(f"{'field':12s} {'month':8s} {'hand P95':>9s} {'file P95':>9s} {'diff':>8s} {'hand n':>7s} {'file n':>7s}  {'P95 lower':>9s} {'P95 nearest':>11s}  hours>=P95")
for (field, month), plants in cases.items():
    ym = month.replace("-", "")
    rows = list(csv.DictReader(open(f"{RAW}/{ym}.csv", encoding="utf-8-sig")))
    rows = [{k.strip(): v for k, v in r.items()} for r in rows]
    dcol = [k for k in rows[0] if k.lower() == "trading_date"][0]
    # per plant: date -> 50-slot array of MW (kWh*2/1000)
    per = {}
    for r in rows:
        key = (r["POC_Code"].strip(), r["Gen_Code"].strip().lower())
        if key not in plants: continue
        arr = per.setdefault(key, {}).setdefault(r[dcol].strip(), np.full(50, np.nan))
        for i in range(50):
            v = r.get(f"TP{i+1}", "")
            v = v.strip() if v else ""
            if v != "":
                try: x = float(v) * 2 / 1000
                except ValueError: continue
                arr[i] = x if math.isnan(arr[i]) else arr[i] + x   # duplicate plant-day rows summed (as build_series does)
    dates = sorted(set().union(*[set(p) for p in per.values()]))
    tot = []
    for dte in dates:
        stack = np.array([per[k].get(dte, np.full(50, np.nan)) for k in plants])
        allnan = np.isnan(stack).all(axis=0); anynan = np.isnan(stack).any(axis=0)
        s = stack.sum(axis=0)
        s[anynan] = np.nan
        tot.extend(s[~allnan].tolist())
    v = np.array([x for x in tot if not math.isnan(x)])
    p95 = float(np.percentile(v, 95)); lo = float(np.percentile(v, 95, method="lower")); ne = float(np.percentile(v, 95, method="nearest"))
    fr = FM[(FM.field == field) & (FM.month == month)].iloc[0]
    print(f"{field:12s} {month:8s} {p95:9.3f} {fr.p95:9.3f} {p95-fr.p95:8.4f} {len(v):7d} {int(fr.n):7d}  {lo:9.3f} {ne:11.3f}  {(v>=p95).sum()/2:.1f}")
