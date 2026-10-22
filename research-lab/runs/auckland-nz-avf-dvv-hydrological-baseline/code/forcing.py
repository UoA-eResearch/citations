"""Forcing (plan section 1): Open-Meteo ERA5 archive, daily precipitation sum and mean 2 m temperature at the field's
centre (36.90 S, 174.78 E), 2012-01-01 to 2026-09-30. Writes data/raw/era5_daily.csv and its sha256."""
import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
URL = ("https://archive-api.open-meteo.com/v1/archive?latitude=-36.90&longitude=174.78&start_date=2012-01-01"
       "&end_date=2026-09-30&daily=precipitation_sum,temperature_2m_mean&timezone=Pacific%2FAuckland&models=era5")


def main():
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "research-lab"}), timeout=300))
    d = pd.DataFrame({"date": r["daily"]["time"], "precip_mm": r["daily"]["precipitation_sum"],
                      "t2m_c": r["daily"]["temperature_2m_mean"]})
    p = RUN / "data" / "raw" / "era5_daily.csv"
    d.to_csv(p, index=False)
    print(len(d), "days;", int(d.precip_mm.isna().sum()), "missing precip;", hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
