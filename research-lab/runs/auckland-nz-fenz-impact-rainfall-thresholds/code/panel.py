"""Suburb-day panel (plan sections 0-2): geocoded suburbs with a gauge within 10 km; each day takes the nearest gauge
that is usable that day (known6 >= 0.9 and the gauge-year's median wet interval <= 15 min). Variants: Q (2xx excluded),
5 km, and an inverse-distance mean of up to three usable gauges within 10 km.

  panel.py -> data/panel.parquet, results/tables/panel_coverage.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
HL = RUN.parent / "auckland-nz-hirds-out-of-sample-exceedance-audit"
D, T = RUN / "data", RUN / "results" / "tables"
TRAIN_END = pd.Timestamp("2024-06-30")


def km(lat1, lon1, lat2, lon2):
    return np.hypot((lon2 - lon1) * 111.32 * np.cos(np.radians((lat1 + lat2) / 2)), (lat2 - lat1) * 110.57)


def main():
    S = pd.read_parquet(D / "suburbs.parquet")
    S = S[S.match.isin(["unique", "tla_centroid"])].reset_index(drop=True)
    H = pd.read_parquet(HL / "data" / "hirds_depths.parquet")
    G = H.groupby("file")[["lat", "lon"]].first()
    idx = lambda d, a: H[(H.table == "historical") & (H.duration_h == d) & np.isclose(H.ari, a)].set_index("file").mm
    M6, M1, M24 = idx(6, 2.0), idx(1, 2.0), idx(24, 2.0)
    R = pd.read_parquet(D / "rain_daily.parquet")
    R["wy"] = np.where(R.day.dt.month >= 7, R.day.dt.year, R.day.dt.year - 1)
    mx = pd.read_parquet(HL / "data" / "maxima.parquet")
    res = mx[(mx.d == 6) & (mx.variant == "S3")].set_index(["file", "wy"]).wet_median_min
    R["resolved"] = pd.MultiIndex.from_arrays([R.file, R.wy]).map(res).to_numpy() <= 15
    R = R[R.file.isin(G.index) & R.file.isin(M6.index)]
    days = np.sort(R.day.unique())
    files = sorted(R.file.unique()); fi = {f: i for i, f in enumerate(files)}
    nd, nf = len(days), len(files)
    di = np.searchsorted(days, R.day.to_numpy())
    A = {}
    for col in ("d1", "d6", "d24", "ante72", "d6_q"):
        a = np.full((nf, nd), np.nan); a[R.file.map(fi).to_numpy(), di] = R[col].to_numpy(); A[col] = a
    m6v = np.array([M6[f] for f in files])
    A["r6"] = A["d6"] / m6v[:, None]
    use = np.zeros((nf, nd), bool); use[R.file.map(fi).to_numpy(), di] = ((R.known6 >= 0.9) & R.resolved).to_numpy()
    use_q = np.zeros((nf, nd), bool); use_q[R.file.map(fi).to_numpy(), di] = ((R.known6_q >= 0.9) & R.resolved).to_numpy()
    glat, glon = G.loc[files, "lat"].to_numpy(), G.loc[files, "lon"].to_numpy()
    F = pd.read_parquet(D / "fenz_daily.parquet")
    F = F.groupby(["suburb", "tla", "region", "day"])[["flood", "v1", "v2", "nonflood"]].sum()
    train_days = int((days <= np.datetime64(TRAIN_END)).sum())
    out, cov = [], {"geocoded_suburbs": len(S), "with_gauge_within_10km": 0, "suburb_days_possible": 0, "suburb_days_no_usable_gauge": 0}
    for s in S.itertuples():
        dist = km(s.lat, s.lon, glat, glon)
        order = np.argsort(dist); order = order[dist[order] <= 10]
        if not len(order):
            continue
        cov["with_gauge_within_10km"] += 1; cov["suburb_days_possible"] += nd
        U = use[order]; first = np.where(U.any(0), U.argmax(0), -1)
        ok = first >= 0
        cov["suburb_days_no_usable_gauge"] += int((~ok).sum())
        g = np.where(ok, order[np.maximum(first, 0)], -1)
        Uq = use_q[order]; fq = np.where(Uq.any(0), Uq.argmax(0), -1); gq = np.where(fq >= 0, order[np.maximum(fq, 0)], -1)
        # inverse-distance mean of up to three usable gauges
        w = np.where(U, 1.0 / np.maximum(dist[order], 0.5)[:, None], 0.0)
        rank = np.cumsum(U, axis=0); w = np.where(rank <= 3, w, 0.0)
        wsum = np.where(w.sum(0) > 0, w.sum(0), np.nan)
        d6_idw = np.nansum(np.nan_to_num(A["d6"][order]) * w, 0) / wsum
        r6_idw = np.nansum(np.nan_to_num(A["r6"][order]) * w, 0) / wsum
        cols = np.arange(nd)
        rec = pd.DataFrame({"suburb": s.suburb, "tla": s.tla, "region": s.region, "day": days, "gauge": np.array(files, dtype=object)[np.maximum(g, 0)],
                            "gauge_km": np.where(ok, dist[np.maximum(g, 0)], np.nan)})
        for col in ("d1", "d6", "d24", "ante72"):
            rec[col] = np.where(ok, A[col][np.maximum(g, 0), cols], np.nan)
        rec["d6_q"] = np.where(gq >= 0, A["d6_q"][np.maximum(gq, 0), cols], np.nan)
        rec["gauge_q"] = np.where(gq >= 0, np.array(files, dtype=object)[np.maximum(gq, 0)], None)
        rec["d6_idw"], rec["r6_idw"] = d6_idw, r6_idw
        rec = rec[ok]
        out.append(rec)
    P = pd.concat(out, ignore_index=True)
    P["M6"], P["M1"], P["M24"] = P.gauge.map(M6), P.gauge.map(M1), P.gauge.map(M24)
    P["M6_q"] = P.gauge_q.map(M6)
    key = pd.MultiIndex.from_frame(P[["suburb", "tla", "region", "day"]])
    for c in ("flood", "v1", "v2", "nonflood"):
        P[c] = F[c].reindex(key).fillna(0).to_numpy().astype(np.int32)
    tr = P.day <= TRAIN_END
    act = P[tr].groupby(["suburb", "tla", "region"]).nonflood.sum() / train_days
    P["activity"] = np.log(pd.MultiIndex.from_frame(P[["suburb", "tla", "region"]]).map(act).to_numpy() + 0.01)
    P["test"] = ~tr
    P.to_parquet(D / "panel.parquet")
    cov.update({"panel_suburb_days": len(P), "panel_suburbs": int(P[["suburb", "tla", "region"]].drop_duplicates().shape[0]),
                "gauges_used": int(P.gauge.nunique()), "test_suburb_days": int(P.test.sum())})
    (T / "panel_coverage.json").write_text(json.dumps(cov, indent=1) + "\n")
    print(json.dumps(cov, indent=1))


if __name__ == "__main__":
    main()
