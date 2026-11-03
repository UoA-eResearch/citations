"""G4 geocoding audit with a denominator (D4, review finding 5): a random 100 panel places are reverse-geocoded
with OpenStreetMap Nominatim (1 request per 1.5 s, identifying User-Agent, per its usage policy) and the OSM
region and territorial authority are compared with the place's region (its TLA's modal council) and FENZ TLA.

  g4_osm.py -> results/tables/g4_osm.csv, results/tables/g4_osm.json
"""
import json
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
UA = "research-lab-fenz-audit/1.0 (University of Auckland eResearch; one-off audit of 100 points)"


def norm(x):
    x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().lower()
    x = re.sub(r"\b(region|district|city|council|of|the|territorial authority)\b", " ", x)
    return re.sub(r"[^a-z0-9]+", " ", x).strip()


def main():
    P = pd.read_parquet(D / "panel.parquet", columns=["suburb", "tla", "region"]).drop_duplicates()
    S = pd.read_parquet(D / "suburbs.parquet")[["suburb", "tla", "lat", "lon"]].drop_duplicates(["suburb", "tla"])
    u = P.merge(S, on=["suburb", "tla"]).sample(100, random_state=20261103)
    rows = []
    for r in u.itertuples():
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={r.lat:.6f}&lon={r.lon:.6f}&zoom=10&addressdetails=1"
        a = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()).get("address", {})
        osm_region = a.get("state") or a.get("region") or ""
        osm_tla = a.get("county") or a.get("city") or a.get("municipality") or a.get("town") or ""
        rows.append((r.suburb, r.tla, r.region, osm_region, osm_tla,
                     norm(osm_region) == norm(r.region), norm(osm_tla) == norm(r.tla) or norm(r.tla) in norm(osm_tla) or norm(osm_tla) in norm(r.tla)))
        time.sleep(1.5)
    d = pd.DataFrame(rows, columns=["suburb", "tla", "region", "osm_region", "osm_tla", "region_match", "tla_match"])
    d.to_csv(T / "g4_osm.csv", index=False)
    out = {"audited": len(d), "region_match": int(d.region_match.sum()), "tla_match": int(d.tla_match.sum()),
           "both_mismatch": int((~d.region_match & ~d.tla_match).sum())}
    (T / "g4_osm.json").write_text(json.dumps(out, indent=1) + "\n"); print(out)


if __name__ == "__main__":
    main()
