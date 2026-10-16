"""Reviewer check 2: recompute closest approach and category for selected events straight from IBTrACS with an
independent method (10-minute interpolation on 3-D unit vectors, so the antimeridian needs no unwrapping), and
compute an exposure measure the study does not use: was the port inside the USA 64-kt (hurricane-force) and 50-kt
wind radii at closest approach? Also Port Vila's activity and the SIDS list."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from events import cat_from_wind, haversine  # noqa
import recovery as R

RAD = ["USA_R34_NE", "USA_R34_SE", "USA_R34_SW", "USA_R34_NW", "USA_R50_NE", "USA_R50_SE", "USA_R50_SW", "USA_R50_NW",
       "USA_R64_NE", "USA_R64_SE", "USA_R64_SW", "USA_R64_NW", "USA_RMW"]
t = pd.read_csv(RUN / "data/raw/ibtracs/ibtracs.since1980.csv", skiprows=[1], low_memory=False,
                usecols=["SID", "NAME", "BASIN", "ISO_TIME", "LAT", "LON", "USA_SSHS", "USA_WIND", "USA_AGENCY", "USA_STATUS",
                         "TRACK_TYPE", "WMO_WIND", "WMO_AGENCY"] + RAD, keep_default_na=False, na_values=["", " "])
t["ISO_TIME"] = pd.to_datetime(t.ISO_TIME)
t = t[t.ISO_TIME >= "2019-01-01"].copy()
for c in ["LAT", "LON", "USA_SSHS", "USA_WIND", "WMO_WIND"] + RAD:
    t[c] = pd.to_numeric(t[c], errors="coerce")
print("TRACK_TYPE values:", t.TRACK_TYPE.value_counts().to_dict())
print("USA_AGENCY values (2019+):", t.USA_AGENCY.value_counts().head(8).to_dict())
print("share of 2019+ fixes with USA_SSHS missing but USA_WIND present:", ((t.USA_SSHS.isna()) & t.USA_WIND.notna()).mean().round(4),
      "; both missing:", (t.USA_SSHS.isna() & t.USA_WIND.isna()).mean().round(4))
t = t.dropna(subset=["LAT", "LON"])

def unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)

def closest(track, plat, plon, step_min=10):
    tr = track.sort_values("ISO_TIME")
    ts = tr.ISO_TIME.astype("int64").to_numpy() / 6e10  # minutes
    v = unit(tr.LAT.to_numpy(), tr.LON.to_numpy())
    grid = np.arange(ts[0], ts[-1] + 1e-9, step_min)
    vi = np.stack([np.interp(grid, ts, v[:, j]) for j in range(3)], -1)
    vi /= np.linalg.norm(vi, axis=1, keepdims=True)
    p = unit(plat, plon)
    d = 6371.0088 * np.arccos(np.clip(vi @ p, -1, 1))
    i = int(np.argmin(d))
    near = int(np.abs(ts - grid[i]).argmin())
    row = tr.iloc[near]
    cat = row.USA_SSHS if np.isfinite(row.USA_SSHS) else cat_from_wind(row.USA_WIND)
    # bearing from storm centre to port, for the wind-radius quadrant
    la1, lo1, la2, lo2 = map(np.radians, (np.degrees(np.arcsin(vi[i, 2])), np.degrees(np.arctan2(vi[i, 1], vi[i, 0])), plat, plon))
    br = np.degrees(np.arctan2(np.sin(lo2 - lo1) * np.cos(la2), np.cos(la1) * np.sin(la2) - np.sin(la1) * np.cos(la2) * np.cos(lo2 - lo1))) % 360
    q = ["NE", "SE", "SW", "NW"][int(br // 90)]
    r64, r50, r34 = row[f"USA_R64_{q}"], row[f"USA_R50_{q}"], row[f"USA_R34_{q}"]
    km = 1.852
    return dict(closest_km=float(d[i]), time=pd.Timestamp(grid[i] * 6e10), cat=float(cat), usa_wind=row.USA_WIND, wmo_wind=row.WMO_WIND,
                usa_status=row.USA_STATUS, quadrant=q, r64_km=r64 * km if np.isfinite(r64) else np.nan,
                r50_km=r50 * km if np.isfinite(r50) else np.nan, r34_km=r34 * km if np.isfinite(r34) else np.nan,
                rmw_km=row.USA_RMW * km if np.isfinite(row.USA_RMW) else np.nan, max_cat=float(np.nanmax(np.where(tr.USA_SSHS.notna(), tr.USA_SSHS, tr.USA_WIND.map(cat_from_wind)))))

ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv").set_index("portid")
ev = pd.read_csv(RUN / "results/tables/recovery_events.csv")
ok = ev[(ev.status == "ok") & (ev.cat_at_closest >= 3) & (ev.closest_km <= 150)].copy()
spot = ["Suva|HAROLD", "Lautoka|HAROLD", "Nuku'alofa|HAROLD", "Luganville|HAROLD", "Noumea|NIRAN", "Apra Harbor|MAWAR",
        "Kingston|MELISSA", "Montego Bay|MELISSA", "Santiago De Cuba|MELISSA", "Kingston|BERYL", "Cebu|RAI", "Lake Charles|LAURA",
        "Saint George's|BERYL", "Freeport|DORIAN", "Mariel|RAFAEL", "Providenciales|FIONA"]
rows = []
for s in spot:
    pn, st = s.split("|")
    e = ev[(ev.portname == pn) & (ev.storm == st)]
    if not len(e): print("not found", s); continue
    e = e.iloc[0]
    c = closest(t[t.SID == e.sid], ports.loc[e.portid, "lat"], ports.loc[e.portid, "lon"])
    rows.append(dict(port=pn, storm=st, study_km=round(e.closest_km, 1), review_km=round(c["closest_km"], 1), study_cat=e.cat_at_closest,
                     review_cat=c["cat"], usa_wind_kt=c["usa_wind"], wmo_wind_kt=c["wmo_wind"], status=c["usa_status"],
                     study_date=e.date, review_time=c["time"], quadrant=c["quadrant"], r64_km=c["r64_km"], r50_km=c["r50_km"], rmw_km=c["rmw_km"],
                     in_r64=c["closest_km"] <= c["r64_km"] if np.isfinite(c["r64_km"]) else None, max_cat=c["max_cat"]))
spot_df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("\n=== spot checks ===")
print(spot_df.to_string(index=False))

# exposure for every computed primary-arm event
exp_rows = []
for _, e in ok.iterrows():
    c = closest(t[t.SID == e.sid], ports.loc[e.portid, "lat"], ports.loc[e.portid, "lon"], step_min=30)
    exp_rows.append(dict(portname=e.portname, storm=e.storm, sids=e.sids, disrupted=e.disrupted, closest_km=e.closest_km, cat=e.cat_at_closest,
                         r64_km=c["r64_km"], r50_km=c["r50_km"], r34_km=c["r34_km"], in_r64=(c["closest_km"] <= c["r64_km"]) if np.isfinite(c["r64_km"]) else np.nan,
                         in_r50=(c["closest_km"] <= c["r50_km"]) if np.isfinite(c["r50_km"]) else np.nan, status=c["usa_status"]))
x = pd.DataFrame(exp_rows)
x.to_csv(Path(__file__).parent / "exposure_primary_ok.csv", index=False)
print("\n=== exposure (port inside the storm's 64-kt / 50-kt wind radius at closest approach) ===")
for name, g in (("SIDS", x[x.sids]), ("non-SIDS", x[~x.sids])):
    print(f"{name}: n={len(g)}  in R64: {g.in_r64.sum()} ({g.in_r64.mean():.2f})  in R50: {g.in_r50.sum()} ({g.in_r50.mean():.2f})  R64 missing: {g.in_r64.isna().sum()}")
print("disrupted by exposure (all):")
print(x.groupby(["in_r64"]).agg(n=("disrupted", "size"), disrupted=("disrupted", "sum")).to_string())
print(x.groupby(["sids", "in_r64"]).agg(n=("disrupted", "size"), disrupted=("disrupted", "sum")).to_string())
print("\nSIDS events with exposure:")
print(x[x.sids][["portname", "storm", "closest_km", "cat", "r64_km", "r50_km", "in_r64", "in_r50", "disrupted"]].round(0).to_string(index=False))
print("\nnon-SIDS DISRUPTED events outside R64:")
print(x[~x.sids & x.disrupted & (x.in_r64 == False)][["portname", "storm", "closest_km", "cat", "r64_km", "r50_km"]].round(0).to_string(index=False))
print("\nnon-SIDS NOT disrupted inside R64:")
print(x[~x.sids & ~x.disrupted & (x.in_r64 == True)][["portname", "storm", "closest_km", "cat", "r64_km"]].round(0).to_string(index=False))

# Port Vila and Judy/Kevin
a = pd.read_csv(RUN / "data/raw/portwatch/daily.csv", usecols=["portid", "portcalls"]).groupby("portid").portcalls.mean()
print("\nPort Vila mean calls/day:", round(a.get("port980", np.nan), 3), " Luganville:", round(a.get("port1324", np.nan), 3))
print("Pacific ports (PICT) >= 0.5:", int((a[ports.index[ports.ISO3.isin(R.PICT)].intersection(a.index)] >= 0.5).sum()), "of", ports.ISO3.isin(R.PICT).sum(),
      "; >= 1:", int((a[ports.index[ports.ISO3.isin(R.PICT)].intersection(a.index)] >= 1).sum()), "; >= 2:", int((a[ports.index[ports.ISO3.isin(R.PICT)].intersection(a.index)] >= 2).sum()))
print("SIDS list length:", len(R.SIDS), "; SIDS ports in database:", ports.ISO3.isin(R.SIDS).sum(), "; SGP/BHR/PRI/GUM/MNP ports:",
      ports[ports.ISO3.isin(["SGP", "BHR", "PRI", "GUM", "MNP"])].groupby("ISO3").size().to_dict())
e2 = ev[ev.ISO3.isin(["SGP", "BHR", "PRI", "VIR"]) & (ev.cat_at_closest >= 1) & (ev.closest_km <= 150)]
print("Cat1+ <=150 km events at SGP/BHR/PRI/VIR ports:", len(e2), e2[["portname", "storm", "cat_at_closest", "closest_km", "status"]].to_string(index=False) if len(e2) else "")
