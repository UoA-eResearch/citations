"""USGS ComCat catalogues (plan section 1). No pick is read here.

  catalogs.py fetch      -> data/cat/{triggers_m7, global_m45, region_m35}.csv
  catalogs.py validation -> data/cat/validation_days.csv (100 quiet days, seed 20261026) and region_m1_validation.csv
"""
import io
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
C = RUN / "data" / "cat"
C.mkdir(parents=True, exist_ok=True)
URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
REGION = dict(minlatitude=25, maxlatitude=55, minlongitude=-135, maxlongitude=-100)
SEED = 20261026


def query(**kw):
    q = dict(format="csv", orderby="time-asc", limit=20000, **kw)
    for k in range(6):
        try:
            s = urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=300).read().decode()
            d = pd.read_csv(io.StringIO(s)) if s.strip() else pd.DataFrame()
            assert len(d) < 20000, f"query hit the limit: {kw}"
            return d
        except AssertionError:
            raise
        except Exception:
            time.sleep(10 * (k + 1))
    raise IOError(f"query failed: {kw}")


def by_year(lo, hi, **kw):
    return pd.concat([query(starttime=f"{y}-01-01", endtime=f"{y + 1}-01-01", **kw) for y in range(lo, hi + 1)],
                     ignore_index=True)


def fetch():
    query(starttime="2002-01-01", endtime="2026-01-01", minmagnitude=7.0).to_csv(C / "triggers_m7.csv", index=False)
    by_year(2001, 2025, minmagnitude=4.5).to_csv(C / "global_m45.csv", index=False)
    by_year(2001, 2025, minmagnitude=3.5, **REGION).to_csv(C / "region_m35.csv", index=False)
    for f in ("triggers_m7", "global_m45", "region_m35"):
        print(f, len(pd.read_csv(C / f"{f}.csv")), flush=True)


def validation():
    """100 quiet days: no regional M >= 4.5 that day or the day before, and no global M >= 6.5 that day."""
    g = pd.read_csv(C / "global_m45.csv", parse_dates=["time"])
    r = pd.read_csv(C / "region_m35.csv", parse_dates=["time"])
    days = pd.date_range("2005-01-01", "2025-12-31", freq="D", tz="UTC")
    bad = set(g[g.mag >= 6.5].time.dt.floor("D"))
    rr = r[r.mag >= 4.5].time.dt.floor("D")
    bad |= set(rr) | set(rr + pd.Timedelta(days=1))
    ok = [d for d in days if d not in bad]
    pick = sorted(np.random.default_rng(SEED).choice(len(ok), 100, replace=False))
    vd = pd.DataFrame({"day": [ok[i] for i in pick]})
    vd.to_csv(C / "validation_days.csv", index=False)
    ev = [query(starttime=str(d.date()), endtime=str((d + pd.Timedelta(days=1)).date()), minmagnitude=1.0, **REGION)
          for d in vd.day]
    pd.concat(ev, ignore_index=True).to_csv(C / "region_m1_validation.csv", index=False)
    print(len(vd), "days;", sum(len(e) for e in ev), "M>=1 events", flush=True)


if __name__ == "__main__":
    {"fetch": fetch, "validation": validation}[sys.argv[1]]()
