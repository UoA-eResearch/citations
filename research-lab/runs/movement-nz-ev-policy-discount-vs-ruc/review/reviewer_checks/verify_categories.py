"""Reviewer check 1b: what are the ambiguous motive-power categories, and the DIESEL HYBRID surge in the control?
  a. DIESEL HYBRID by month 2023-10 .. 2024-12 (light universe) and by vehicle type / import status
  b. PETROL ELECTRIC HYBRID: top MAKE/MODEL and import status 2023-2024
  c. ELECTRIC [PETROL EXTENDED]: top MAKE/MODEL 2025-2026
"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path
HERE = Path(__file__).resolve().parent; RAW = HERE / "raw"; RAW.mkdir(exist_ok=True)
SVC = "https://services.arcgis.com/CXBb7LAjgIIdcsPt/arcgis/rest/services/MVR_Mar26/FeatureServer/0/query"
UA = {"User-Agent": "UoA research-lab reviewer (aggregation queries only)"}
TYPES = "('PASSENGER CAR/VAN','GOODS VAN/TRUCK/UTILITY')"
def q(name, where, group):
    f = RAW / f"{name}.json"
    if f.exists(): return json.load(open(f))
    params = {"where": where, "f": "json", "groupByFieldsForStatistics": group,
              "outStatistics": json.dumps([{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"}])}
    url = SVC + "?" + urllib.parse.urlencode(params)
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r: d = json.loads(r.read())
            if "features" not in d: raise ValueError(str(d)[:200])
            json.dump(d, open(f, "w")); time.sleep(2); return d
        except Exception as e:
            print(f"  {name} attempt {k+1}: {type(e).__name__} {str(e)[:150]}", flush=True); time.sleep(5*(k+1))
    sys.exit(f"query {name} failed")
F = lambda d: [x["attributes"] for x in d["features"]]

print("== a. DIESEL HYBRID by month (light universe), 2023-10 .. 2024-12, with vehicle type")
d = q("dh_months", f"((FIRST_NZ_REGISTRATION_YEAR=2023 AND FIRST_NZ_REGISTRATION_MONTH>=10) OR FIRST_NZ_REGISTRATION_YEAR=2024) AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER='DIESEL HYBRID'",
      "FIRST_NZ_REGISTRATION_YEAR,FIRST_NZ_REGISTRATION_MONTH,VEHICLE_TYPE,IMPORT_STATUS")
rows = sorted(F(d), key=lambda a: (a["FIRST_NZ_REGISTRATION_YEAR"], a["FIRST_NZ_REGISTRATION_MONTH"]))
for a in rows: print(f"  {a['FIRST_NZ_REGISTRATION_YEAR']}-{a['FIRST_NZ_REGISTRATION_MONTH']:02d} {a['VEHICLE_TYPE']:24s} {a['IMPORT_STATUS']:12s} {a['n']:,}")
d = q("dh_models", f"FIRST_NZ_REGISTRATION_YEAR>=2024 AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER='DIESEL HYBRID'", "MAKE,MODEL")
print("  top DIESEL HYBRID make/model 2024-26:", sorted(((a['n'], a['MAKE'], a['MODEL']) for a in F(d)), reverse=True)[:8])

print("\n== b. PETROL ELECTRIC HYBRID 2023-2024: top make/model, import status")
d = q("peh_models", f"FIRST_NZ_REGISTRATION_YEAR IN (2023,2024) AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER='PETROL ELECTRIC HYBRID'", "MAKE,MODEL,IMPORT_STATUS")
for n, mk, md, st in sorted(((a['n'], a['MAKE'], a['MODEL'], a['IMPORT_STATUS']) for a in F(d)), reverse=True)[:12]: print(f"  {n:6,d} {mk} {md} [{st}]")
d = q("ph_models", f"FIRST_NZ_REGISTRATION_YEAR IN (2023,2024) AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER='PETROL HYBRID'", "MAKE,MODEL,IMPORT_STATUS")
print("  (for contrast) top PETROL HYBRID:", [(a['n'], a['MAKE'], a['MODEL'], a['IMPORT_STATUS']) for a in sorted(F(d), key=lambda a: -a['n'])[:6]])

print("\n== c. ELECTRIC [PETROL EXTENDED] 2025-2026: top make/model")
d = q("epe_models", f"FIRST_NZ_REGISTRATION_YEAR IN (2025,2026) AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER='ELECTRIC [PETROL EXTENDED]'", "MAKE,MODEL")
print("  ", sorted(((a['n'], a['MAKE'], a['MODEL']) for a in F(d)), reverse=True)[:8])

print("\n== d. plug-in by vehicle type and month around April 2024 (GOODS plug-ins; heavy EV exemption from RUC)")
d = q("plug_goods", f"FIRST_NZ_REGISTRATION_YEAR=2024 AND VEHICLE_TYPE IN {TYPES} AND MOTIVE_POWER IN ('ELECTRIC','PLUGIN PETROL HYBRID') AND GROSS_VEHICLE_MASS>3500", "FIRST_NZ_REGISTRATION_MONTH")
print("  2024 plug-ins >3500 kg by month:", {a['FIRST_NZ_REGISTRATION_MONTH']: a['n'] for a in sorted(F(d), key=lambda a: a['FIRST_NZ_REGISTRATION_MONTH'])})
