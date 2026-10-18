"""Secondary pair (plan section 2): PERSIANN and PERSIANN-CDR daily values at every gauge's 0.25 deg cell, 2001-2020, and
the GPCC Full Data Monthly v2022 gauge count of the 2.5 deg cell containing each gauge. Both PERSIANN grids are cell-
centred at 59.875..-59.875 N, 0.125..359.875 E. A missing or unreadable file gives no row for that day, never zero rain.
Writes data/extract/persiann_daily.csv (date, station, persiann, cdr; empty where nodata) and data/labels_gpcc.csv
(station, ym, numgauge)."""
import datetime as dt
import gzip
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"


def cell(lat, lon):
    return int(np.floor((60 - lat) / 0.25)), int(np.floor((lon % 360) / 0.25))


def main():
    st = pd.read_csv(RAW / "ghcn" / "stations.csv")
    rc = [cell(a, b) for a, b in zip(st.lat, st.lon)]
    rows_i, cols_i = np.array([r for r, _ in rc]), np.array([c for _, c in rc])
    cdr = {p.name.split("_")[2]: p for p in (RAW / "persiann_cdr").glob("PERSIANN-CDR_v01r01_*.nc")}
    out, miss = [], {"persiann": 0, "cdr": 0}
    d = dt.date(2001, 1, 1)
    while d <= dt.date(2020, 12, 31):
        doy = d.timetuple().tm_yday
        pv = cv = None
        f = RAW / "persiann" / f"ms6s4_d{d.year % 100:02d}{doy:03d}.bin.gz"
        try:
            a = np.frombuffer(gzip.open(f).read(), dtype=">f4").reshape(480, 1440)
            pv = a[rows_i, cols_i].astype(float); pv[pv < 0] = np.nan
        except Exception:  # noqa: BLE001
            miss["persiann"] += 1
        g = cdr.get(d.strftime("%Y%m%d"))
        try:
            with netCDF4.Dataset(g) as nc:
                v = nc.variables["precipitation"]; v.set_auto_mask(False)
                lat, lon = nc.variables["lat"][:], nc.variables["lon"][:]
                assert abs(lat[0] - 59.875) < 1e-6 and abs(lon[0] - 0.125) < 1e-6 and v.dimensions == ("time", "lon", "lat")
                b = v[0][:, :]
                cv = b[cols_i, rows_i].astype(float); cv[cv < 0] = np.nan
        except Exception:  # noqa: BLE001
            miss["cdr"] += 1
        if pv is not None or cv is not None:
            for k, s in enumerate(st.id):
                out.append((d.isoformat(), s, None if pv is None or np.isnan(pv[k]) else round(pv[k], 3),
                            None if cv is None or np.isnan(cv[k]) else round(cv[k], 3)))
        d += dt.timedelta(1)
    pd.DataFrame(out, columns=["date", "station", "persiann", "cdr"]).to_csv(RUN / "data" / "extract" / "persiann_daily.csv", index=False)
    lab = []
    for a, b in ((2001, 2010), (2011, 2020)):
        nc = netCDF4.Dataset("gpcc", memory=gzip.open(RAW / "gpcc" / f"full_data_monthly_v2022_{a}_{b}_25.nc.gz").read())
        lat, lon = nc.variables["lat"][:], nc.variables["lon"][:]
        ng = nc.variables["numgauge"][:]
        t0 = dt.datetime(a, 1, 1)
        times = [t0 + dt.timedelta(hours=float(h)) for h in nc.variables["time"][:]]
        for s in st.itertuples():
            i = int(np.argmin(np.abs(lat - s.lat))); lo = ((s.lon + 180) % 360) - 180; j = int(np.argmin(np.abs(lon - lo)))
            assert abs(lat[i] - s.lat) <= 1.25 + 1e-9 and abs(lon[j] - lo) <= 1.25 + 1e-9
            for t, tm in enumerate(times):
                lab.append((s.id, tm.strftime("%Y-%m"), int(ng[t, i, j]) if np.ma.is_masked(ng[t, i, j]) is False else None))
    pd.DataFrame(lab, columns=["station", "ym", "numgauge"]).to_csv(RUN / "data" / "labels_gpcc.csv", index=False)
    print(len(out), "station-days;", miss, "missing days;", len(lab), "GPCC station-months")


if __name__ == "__main__":
    main()
