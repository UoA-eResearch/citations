"""Plant coordinates (NZTM2000 from EMI's Network Supply Points table, converted to WGS84) and Open-Meteo ERA5
hourly 100 m wind speed and shortwave radiation at each wind or solar POC, for the plausibility check of plan
section 4 (correlation of the potential forecast with weather on unconstrained trading periods).
"""
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
WX = RUN / "data" / "weather"
NSP = Path("/mnt/data/edb-solar/raw/emi/20261020_NetworkSupplyPointsTable.csv")


def nztm_to_wgs84(e, n):
    """Inverse transverse Mercator for NZTM2000 (GRS80; central meridian 173E; k0 0.9996; FE 1,600,000;
    FN 10,000,000), after Snyder (1987)."""
    a, f = 6378137.0, 1 / 298.257222101
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0, lon0, fe, fn = 0.9996, math.radians(173.0), 1600000.0, 10000000.0
    x, y = e - fe, n - fn
    mu = (y / k0) / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    p1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32)
          * math.sin(4 * mu) + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    c1, t1 = ep2 * math.cos(p1) ** 2, math.tan(p1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(p1) ** 2)
    r1 = a * (1 - e2) / (1 - e2 * math.sin(p1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = p1 - (n1 * math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                           + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2)
                                           * d ** 6 / 720)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2)
                  * d ** 5 / 120) / math.cos(p1)
    return math.degrees(lat), math.degrees(lon)


def coordinates(pocs):
    t = pd.read_csv(NSP, dtype=str)
    t = t[t["POC code"].isin(pocs)].dropna(subset=["NZTM easting", "NZTM northing"])
    t = t.drop_duplicates("POC code")
    return {r["POC code"]: nztm_to_wgs84(float(r["NZTM easting"]), float(r["NZTM northing"])) for _, r in t.iterrows()}


def fetch(pocs, start="2020-01-01", end="2026-06-30"):
    WX.mkdir(parents=True, exist_ok=True)
    for poc, (lat, lon) in coordinates(pocs).items():
        out = WX / f"{poc}.json"
        if out.exists() and out.stat().st_size > 10000:
            continue
        q = dict(latitude=round(lat, 4), longitude=round(lon, 4), start_date=start, end_date=end,
                 hourly="wind_speed_100m,shortwave_radiation", timezone="Pacific/Auckland")
        url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=300) as r:
            out.write_bytes(r.read())
        time.sleep(2)


def hourly(poc):
    h = json.load(open(WX / f"{poc}.json"))["hourly"]
    return pd.DataFrame({"time": pd.to_datetime(h["time"]), "wind100": h["wind_speed_100m"],
                         "swr": h["shortwave_radiation"]})


if __name__ == "__main__":
    print(nztm_to_wgs84(1748735.5, 5428421.0))     # Wellington, about (-41.29, 174.78)
