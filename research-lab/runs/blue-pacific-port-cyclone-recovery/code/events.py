"""The event table: every tropical cyclone that passed close to a PortWatch port, 2019 onward.

Uses only IBTrACS best tracks and port coordinates - no port-call outcome - so it is built before plan.md is
committed, and the number of Pacific island events it yields is what the plan's power section rests on.

A track is interpolated to hourly positions (linearly, unwrapping longitude across the antimeridian, which
matters for Fiji, Tonga, Samoa and Tuvalu). For each port and storm, the closest approach is the minimum
great-circle distance over those positions; the storm's Saffir-Simpson category at that hour comes from the
nearest best-track fix (USA_SSHS, the JTWC/NHC category; where it is missing, USA_WIND is converted with the
standard thresholds). An event is a (port, storm) pair within DIST_KM of a category >= CAT storm.

Arms: primary Cat 3+ within 150 km; Cat 1+ within 150 km; Cat 3+ within 100 and 250 km.

Writes data/processed/events_all.csv (every port-storm pair within 250 km of a Cat 1+ storm) and
results/tables/event_counts.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "tables"
PICT = ["ASM", "COK", "FSM", "FJI", "PYF", "GUM", "KIR", "MHL", "NRU", "NCL", "NIU", "MNP", "PLW", "PNG",
        "PCN", "WSM", "SLB", "TKL", "TON", "TUV", "VUT", "WLF"]       # SPC's 22 Pacific Island Countries and Territories
START = "2019-01-01"
MAX_KM = 250.0
R = 6371.0088


def cat_from_wind(kt):
    """Saffir-Simpson category from 1-minute sustained wind (kt); 0 for tropical storm, -1 below that."""
    if not np.isfinite(kt):
        return np.nan
    for c, lo in ((5, 137), (4, 113), (3, 96), (2, 83), (1, 64), (0, 34)):
        if kt >= lo:
            return c
    return -1


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def load_tracks():
    t = pd.read_csv(RAW / "ibtracs" / "ibtracs.since1980.csv", skiprows=[1], low_memory=False,
                    usecols=["SID", "NAME", "BASIN", "ISO_TIME", "LAT", "LON", "USA_SSHS", "USA_WIND"],
                    keep_default_na=False, na_values=["", " "])
    t["ISO_TIME"] = pd.to_datetime(t.ISO_TIME)
    t = t[t.ISO_TIME >= START].copy()
    for c in ("LAT", "LON", "USA_SSHS", "USA_WIND"):
        t[c] = pd.to_numeric(t[c], errors="coerce")
    # category: USA_SSHS where present, else converted from USA_WIND
    t["cat"] = t.USA_SSHS.where(t.USA_SSHS.notna(), t.USA_WIND.map(cat_from_wind))
    return t.dropna(subset=["LAT", "LON"])


def hourly(track):
    """Hourly positions with the category of the nearest fix, longitude unwrapped across 180."""
    track = track.sort_values("ISO_TIME")
    lon = np.degrees(np.unwrap(np.radians(track.LON.to_numpy())))
    ts = track.ISO_TIME.astype("int64").to_numpy() / 3.6e12           # hours
    grid = np.arange(ts[0], ts[-1] + 1e-9, 1.0)
    lat_h = np.interp(grid, ts, track.LAT.to_numpy())
    lon_h = np.interp(grid, ts, lon)
    near = np.abs(ts[None, :] - grid[:, None]).argmin(axis=1)
    cat_h = track["cat"].to_numpy()[near]
    return pd.to_datetime(grid * 3.6e12), lat_h, ((lon_h + 180) % 360) - 180, cat_h


def main():
    ports = pd.read_csv(RAW / "portwatch" / "ports.csv")
    ports["pict"] = ports.ISO3.isin(PICT)
    tracks = load_tracks()
    rows = []
    for sid, tr in tracks.groupby("SID"):
        if tr["cat"].max() < 1 or len(tr) < 2:
            continue
        times, la, lo, cat = hourly(tr)
        # coarse filter: ports within ~3 degrees of the track's bounding box
        box = ports[(ports.lat.between(la.min() - 3, la.max() + 3))]
        for _, p in box.iterrows():
            d = haversine(p.lat, p.lon, la, lo)
            i = int(np.argmin(d))
            if d[i] <= MAX_KM:
                rows.append(dict(portid=p.portid, portname=p.portname, ISO3=p.ISO3, pict=bool(p.pict),
                                 sid=sid, storm=tr.NAME.iloc[0], basin=tr.BASIN.iloc[0],
                                 closest_km=float(d[i]), cat_at_closest=float(cat[i]),
                                 date=times[i].date().isoformat(), max_cat_storm=float(tr["cat"].max())))
    ev = pd.DataFrame(rows)
    PROC.mkdir(parents=True, exist_ok=True)
    ev.to_csv(PROC / "events_all.csv", index=False)

    def count(cat, km):
        e = ev[(ev.cat_at_closest >= cat) & (ev.closest_km <= km)]
        return dict(events=int(len(e)), pict_events=int(e.pict.sum()), pict_ports=int(e[e.pict].portid.nunique()),
                    pict_storms=int(e[e.pict].sid.nunique()), other_events=int((~e.pict).sum()),
                    other_ports=int(e[~e.pict].portid.nunique()))
    arms = {"cat3_150km (primary)": count(3, 150), "cat1_150km": count(1, 150),
            "cat3_100km": count(3, 100), "cat3_250km": count(3, 250)}
    out = dict(start=START, track_end=str(tracks.ISO_TIME.max()), arms=arms)
    json.dump(out, open(TAB / "event_counts.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    prim = ev[(ev.cat_at_closest >= 3) & (ev.closest_km <= 150) & ev.pict].sort_values("date")
    print("\nPICT events in the primary arm:")
    print(prim[["date", "storm", "portname", "ISO3", "closest_km", "cat_at_closest"]].to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
