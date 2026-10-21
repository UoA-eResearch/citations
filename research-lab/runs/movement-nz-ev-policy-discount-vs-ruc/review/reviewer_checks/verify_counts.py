"""Reviewer check 1: re-query NZTA's MVR_Mar26 service independently and compare with data/registrations.csv.

Queries (each a server-side aggregation, 2 s apart, cached in review/reviewer_checks/raw/):
  a. for 2023-11, 2023-12, 2024-01, 2024-04, 2026-03, 2026-09: count by MOTIVE_POWER x VEHICLE_TYPE (light universe)
  b. all MOTIVE_POWER categories 2021-2026 in the light universe (magnitudes of the ambiguous categories)
  c. GOODS VAN/TRUCK/UTILITY by GROSS_VEHICLE_MASS band (<=3500 vs >3500) by year - heavy trucks in the 'light' universe?
  d. total light registrations by month for 2026 (is September complete?)
"""
import csv, json, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
RAW = HERE / "raw"; RAW.mkdir(exist_ok=True)
SVC = "https://services.arcgis.com/CXBb7LAjgIIdcsPt/arcgis/rest/services/MVR_Mar26/FeatureServer/0/query"
UA = {"User-Agent": "UoA research-lab reviewer (aggregation queries only)"}
TYPES = "('PASSENGER CAR/VAN','GOODS VAN/TRUCK/UTILITY')"

def q(name, where, group, extra=None):
    f = RAW / f"{name}.json"
    if f.exists():
        return json.load(open(f))
    params = {"where": where, "f": "json",
              "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}]),
              "groupByFieldsForStatistics": group}
    if extra: params.update(extra)
    url = SVC + "?" + urllib.parse.urlencode(params)
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                d = json.loads(r.read())
            if "features" not in d: raise ValueError(str(d)[:200])
            json.dump(d, open(f, "w")); time.sleep(2); return d
        except Exception as e:
            print(f"  {name} attempt {k+1}: {type(e).__name__} {str(e)[:150]}", flush=True); time.sleep(5*(k+1))
    sys.exit(f"query {name} failed")

def feats(d): return [x["attributes"] for x in d["features"]]

# study's series
study = defaultdict(int)
for r in csv.DictReader(open(RUN / "data" / "registrations.csv")):
    study[(int(r["year"]), int(r["month"]), r["motive_power"], r["vehicle_type"])] += int(r["n"])

print("== a. key months, MOTIVE_POWER x VEHICLE_TYPE: reviewer vs study")
mism = 0
for y, m in [(2023, 11), (2023, 12), (2024, 1), (2024, 4), (2026, 3), (2026, 9)]:
    d = q(f"a_{y}_{m:02d}", f"FIRST_NZ_REGISTRATION_YEAR={y} AND FIRST_NZ_REGISTRATION_MONTH={m} AND VEHICLE_TYPE IN {TYPES}",
          "MOTIVE_POWER,VEHICLE_TYPE")
    mine = {((a["MOTIVE_POWER"] or "").strip(), (a["VEHICLE_TYPE"] or "").strip()): a["n"] for a in feats(d)}
    tot_me = sum(mine.values()); tot_st = sum(v for k, v in study.items() if k[0] == y and k[1] == m)
    print(f"{y}-{m:02d}: reviewer total {tot_me:,} study total {tot_st:,}")
    for (mp, vt), n in sorted(mine.items(), key=lambda kv: -kv[1]):
        s = study.get((y, m, mp, vt), 0)
        flag = "" if s == n else "  <-- MISMATCH"
        if s != n: mism += 1
        if n >= 20 or s != n: print(f"    {mp:32s} {vt:24s} reviewer {n:7,d} study {s:7,d}{flag}")
print("mismatching cells:", mism)

print("\n== b. MOTIVE_POWER categories, light universe, 2021-2026 (by year)")
d = q("b_categories", f"FIRST_NZ_REGISTRATION_YEAR>=2021 AND FIRST_NZ_REGISTRATION_YEAR<=2026 AND VEHICLE_TYPE IN {TYPES}",
      "MOTIVE_POWER,FIRST_NZ_REGISTRATION_YEAR")
cat = defaultdict(dict)
for a in feats(d): cat[(a["MOTIVE_POWER"] or "<null>").strip()][a["FIRST_NZ_REGISTRATION_YEAR"]] = a["n"]
for mp in sorted(cat, key=lambda k: -sum(cat[k].values())):
    print(f"  {mp:36s} total {sum(cat[mp].values()):9,d}  " + " ".join(f"{y}:{cat[mp].get(y,0):,}" for y in range(2021, 2027)))

print("\n== c. GOODS VAN/TRUCK/UTILITY by gross-mass band and year (DIESEL only), and all motive powers")
d = q("c_gvm_diesel", "FIRST_NZ_REGISTRATION_YEAR>=2021 AND FIRST_NZ_REGISTRATION_YEAR<=2026 AND VEHICLE_TYPE='GOODS VAN/TRUCK/UTILITY' AND MOTIVE_POWER='DIESEL' AND GROSS_VEHICLE_MASS>3500",
      "FIRST_NZ_REGISTRATION_YEAR")
heavy = {a["FIRST_NZ_REGISTRATION_YEAR"]: a["n"] for a in feats(d)}
d = q("c_gvm_diesel_light", "FIRST_NZ_REGISTRATION_YEAR>=2021 AND FIRST_NZ_REGISTRATION_YEAR<=2026 AND VEHICLE_TYPE='GOODS VAN/TRUCK/UTILITY' AND MOTIVE_POWER='DIESEL' AND GROSS_VEHICLE_MASS<=3500",
      "FIRST_NZ_REGISTRATION_YEAR")
light = {a["FIRST_NZ_REGISTRATION_YEAR"]: a["n"] for a in feats(d)}
d = q("c_gvm_diesel_null", "FIRST_NZ_REGISTRATION_YEAR>=2021 AND FIRST_NZ_REGISTRATION_YEAR<=2026 AND VEHICLE_TYPE='GOODS VAN/TRUCK/UTILITY' AND MOTIVE_POWER='DIESEL' AND GROSS_VEHICLE_MASS IS NULL",
      "FIRST_NZ_REGISTRATION_YEAR")
nul = {a["FIRST_NZ_REGISTRATION_YEAR"]: a["n"] for a in feats(d)}
for y in range(2021, 2027):
    print(f"  {y}: diesel goods GVM<=3500 {light.get(y,0):,}  GVM>3500 {heavy.get(y,0):,}  GVM null {nul.get(y,0):,}  heavy share {100*heavy.get(y,0)/max(1,light.get(y,0)+heavy.get(y,0)+nul.get(y,0)):.1f}%")
d = q("c_gvm_all_heavy", f"FIRST_NZ_REGISTRATION_YEAR>=2021 AND FIRST_NZ_REGISTRATION_YEAR<=2026 AND VEHICLE_TYPE IN {TYPES} AND GROSS_VEHICLE_MASS>3500",
      "MOTIVE_POWER")
print("  all >3500 kg GVM in the study universe 2021-2026 by motive power:", {(a['MOTIVE_POWER'] or '').strip(): a['n'] for a in feats(d)})

print("\n== c2. diesel GOODS VAN/TRUCK/UTILITY <=3500 kg by month, Oct 2023 - Mar 2024 (is the ute trough/spike in light vehicles?)")
d = q("c2_light_ute_months", "((FIRST_NZ_REGISTRATION_YEAR=2023 AND FIRST_NZ_REGISTRATION_MONTH>=10) OR (FIRST_NZ_REGISTRATION_YEAR=2024 AND FIRST_NZ_REGISTRATION_MONTH<=3)) AND VEHICLE_TYPE='GOODS VAN/TRUCK/UTILITY' AND MOTIVE_POWER='DIESEL' AND GROSS_VEHICLE_MASS<=3500",
      "FIRST_NZ_REGISTRATION_YEAR,FIRST_NZ_REGISTRATION_MONTH")
for a in sorted(feats(d), key=lambda a: (a["FIRST_NZ_REGISTRATION_YEAR"], a["FIRST_NZ_REGISTRATION_MONTH"])):
    print(f"  {a['FIRST_NZ_REGISTRATION_YEAR']}-{a['FIRST_NZ_REGISTRATION_MONTH']:02d}: {a['n']:,}")

print("\n== d. 2026 light registrations by month (completeness of September)")
d = q("d_2026_months", f"FIRST_NZ_REGISTRATION_YEAR=2026 AND VEHICLE_TYPE IN {TYPES}", "FIRST_NZ_REGISTRATION_MONTH")
for a in sorted(feats(d), key=lambda a: a["FIRST_NZ_REGISTRATION_MONTH"] or 0): print(f"  2026-{a['FIRST_NZ_REGISTRATION_MONTH']}: {a['n']:,}")
d = q("d_null_month", f"FIRST_NZ_REGISTRATION_YEAR>=2021 AND VEHICLE_TYPE IN {TYPES} AND FIRST_NZ_REGISTRATION_MONTH IS NULL", "FIRST_NZ_REGISTRATION_YEAR")
print("  rows with null month by year:", {a['FIRST_NZ_REGISTRATION_YEAR']: a['n'] for a in feats(d)})
