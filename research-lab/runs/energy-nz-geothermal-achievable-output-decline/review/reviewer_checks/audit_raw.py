"""Audit the raw EMI Generation_MD files: fuel codes, geothermal gen codes (incl. plausibly mis-coded), TP counts
per day, duplicate plant-days, date formats. Read-only on data; writes nothing."""
import glob, os, sys, re
from collections import Counter, defaultdict
import pandas as pd, numpy as np
RAW = sys.argv[1]
TP = [f"TP{i}" for i in range(1, 51)]
fuel = Counter(); geo_keys = defaultdict(lambda: [None, None, 0])  # (poc,gen,fuel,tech) -> first,last,count
namehits = defaultdict(lambda: [None, None, 0])
GEONAMES = re.compile(r"ohaaki|wairakei|mokai|rotokawa|^nap$|ngatamariki|te_?mihi|poihipi|kawerau|ngawha|te_?huka|tauhara|ahi|maui|taom|geo|norske|topp|tasman|kgl|mercury|contact|bay_of_plenty", re.I)
tpcount = Counter(); dup = []; datefmt = Counter(); nrows_geo = {}
for f in sorted(glob.glob(os.path.join(RAW, "*.csv"))):
    ym = os.path.basename(f)[:6]
    d = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
    d.columns = [c.strip() for c in d.columns]
    dcol = [c for c in d.columns if c.lower() == "trading_date"][0]
    for c in TP:
        if c not in d: d[c] = np.nan
    fuel.update(d.Fuel_Code.str.strip().value_counts().to_dict())
    s = d[dcol].str.strip()
    datefmt.update(("iso" if bool(re.match(r"^\d{4}-\d{2}-\d{2}", v)) else "other") for v in s.head(3))
    isgeo = d.Fuel_Code.str.strip().str.lower().str.startswith("geo", na=False)
    g = d[isgeo]
    nrows_geo[ym] = len(g)
    for (poc, gen, fu, te), n in g.groupby([g.POC_Code.str.strip(), g.Gen_Code.str.strip(), g.Fuel_Code.str.strip(), g.Tech_Code.str.strip()]).size().items():
        k = (poc, gen, fu, te); v = geo_keys[k]
        v[0] = v[0] or ym; v[1] = ym; v[2] += n
    # names that look geothermal but are not fuel-coded Geo
    ng = d[~isgeo & d.Gen_Code.str.strip().str.contains(GEONAMES, na=False)]
    for (poc, gen, fu, te), n in ng.groupby([ng.POC_Code.str.strip(), ng.Gen_Code.str.strip(), ng.Fuel_Code.str.strip(), ng.Tech_Code.str.strip()]).size().items():
        k = (poc, gen, fu, te); v = namehits[k]; v[0] = v[0] or ym; v[1] = ym; v[2] += n
    # TP counts per geothermal plant-day
    vals = g[TP].apply(pd.to_numeric, errors="coerce")
    cnt = vals.notna().sum(axis=1)
    tpcount.update(cnt.value_counts().to_dict())
    # duplicates
    dd = g.groupby([g.POC_Code.str.strip(), g.Gen_Code.str.strip().str.lower(), s[isgeo]]).size()
    for k, n in dd[dd > 1].items():
        dup.append((ym,) + k + (n,))
    # also duplicates by (POC, Gen_Code, Nwk_Code, date) within geo
    print(ym, len(g), file=sys.stderr, end="\r")
print("\nFUEL CODES:", dict(fuel))
print("\nDATE FORMATS (first 3 rows each file):", dict(datefmt))
print("\nGEOTHERMAL (POC, Gen_Code, Fuel, Tech) -> first, last, nrows:")
for k, v in sorted(geo_keys.items(), key=lambda kv: (kv[0][0], kv[1][0])):
    print("  ", k, v)
print("\nNON-GEO-CODED ROWS WHOSE NAME LOOKS GEOTHERMAL (POC, Gen_Code, Fuel, Tech) -> first, last, nrows:")
for k, v in sorted(namehits.items(), key=lambda kv: (kv[0][0], kv[1][0])):
    print("  ", k, v)
print("\nTP non-null counts per geothermal plant-day:", dict(sorted(tpcount.items())))
print("\nDUPLICATE geothermal plant-days (ym, poc, gen, date, n):", len(dup))
for x in dup[:40]: print("  ", x)
