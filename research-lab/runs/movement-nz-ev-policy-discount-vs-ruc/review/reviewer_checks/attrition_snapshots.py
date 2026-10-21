"""Reviewer check 2: snapshot attrition. Compare the MVR snapshot 'MVR_May23' (ArcGIS Online item
aa8a8f187daf491d93d18483a8853562, 'MVR snapshot of data until 30 April' 2023, downloaded 2026-10-21) with the
study's series from MVR_Mar26 (loaded 2026-10-06) for first registrations Jan 2021 - Apr 2023, same universe.
Usage: python -I attrition_snapshots.py <path to MVR_May23_1.csv>
"""
import csv, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent; RUN = HERE.parents[1]
TYPES = {"PASSENGER CAR/VAN", "GOODS VAN/TRUCK/UTILITY"}
BEV = {"ELECTRIC", "ELECTRIC [PETROL EXTENDED]", "ELECTRIC [DIESEL EXTENDED]", "ELECTRIC FUEL CELL OTHER", "ELECTRIC FUEL CELL HYDROGEN"}
PHEV = {"PLUGIN PETROL HYBRID", "PLUGIN DIESEL HYBRID", "PLUG IN FUEL CELL HYDROGEN HYBRID", "PLUG IN FUEL CELL OTHER HYBRID"}
HEV = {"PETROL HYBRID", "DIESEL HYBRID", "PETROL ELECTRIC HYBRID", "DIESEL ELECTRIC HYBRID"}
def grp(mp): return "PLUG" if mp in BEV | PHEV else "HEV" if mp in HEV else "ICE"
old = defaultdict(int); n_rows = 0
with open(sys.argv[1], encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        n_rows += 1
        if r["VEHICLE_TYPE"] not in TYPES: continue
        try: y, m = int(r["FIRST_NZ_REGISTRATION_YEAR"]), int(r["FIRST_NZ_REGISTRATION_MONTH"])
        except ValueError: continue
        if 2021 <= y <= 2023:
            used = "used" if "USED" in r["IMPORT_STATUS"].upper() else "new"
            old[(y, m, grp(r["MOTIVE_POWER"].strip()), used)] += 1
print(f"May-2023 snapshot: {n_rows:,} rows read")
new = defaultdict(int)
for r in csv.DictReader(open(RUN / "data" / "registrations.csv")):
    y, m = int(r["year"]), int(r["month"])
    if y <= 2023:
        used = "used" if "USED" in r["import_status"].upper() else "new"
        new[(y, m, grp(r["motive_power"]), used)] += int(r["n"])
print("\nmonth     | all: May23  Oct26  ratio | plug-in: May23 Oct26 ratio | HEV ratio | ICE ratio | new ratio | used ratio")
tot = defaultdict(lambda: [0, 0])
for y in (2021, 2022, 2023):
    for m in range(1, 13):
        if (y, m) > (2023, 4): break
        def s(g=None, u=None, d=None):
            return sum(v for (yy, mm, gg, uu), v in d.items() if (yy, mm) == (y, m) and (g is None or gg == g) and (u is None or uu == u))
        a_o, a_n = s(d=old), s(d=new); p_o, p_n = s("PLUG", d=old), s("PLUG", d=new)
        rat = lambda g=None, u=None: s(g, u, new) / max(1, s(g, u, old))
        print(f"{y}-{m:02d}   | {a_o:7,d} {a_n:7,d} {a_n/max(1,a_o):.3f} | {p_o:6,d} {p_n:6,d} {p_n/max(1,p_o):.3f} | {rat('HEV'):.3f} | {rat('ICE'):.3f} | {rat(u='new'):.3f} | {rat(u='used'):.3f}")
        tot[y][0] += a_o; tot[y][1] += a_n
for y in tot: print(f"{y} (to Apr 2023 for 2023): May23 {tot[y][0]:,} -> Oct26 {tot[y][1]:,}, surviving share {tot[y][1]/max(1,tot[y][0]):.4f}")
