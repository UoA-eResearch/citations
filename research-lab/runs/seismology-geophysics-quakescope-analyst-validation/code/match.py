"""Match reference (analyst-reviewed) picks to QuakeScope picks (plan section 5). Writes data/matched.parquet.

A reference pick is matched at tolerance tol if the catalogue has a pick of the same phase at the same network and
station code (any location or band) with |peak - t_ref| <= tol; one-to-one, greedy closest-first within each
(station, phase). Tolerances 0.2, 0.5 (primary) and 1.0 s. Denominator (plan section 3): the station-day is `loaded`
in QuakeScope's availability table (any location code) and the station is in western/stations.parquet."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
TOLS = (0.2, 0.5, 1.0)


def greedy_match(ref_t, pk_t, tol):
    """ref_t, pk_t: sorted int64 ns arrays. Returns, for each reference pick, the index of its matched catalogue pick
    (or -1), assigning pairs in order of increasing |dt| so that each catalogue pick is used at most once."""
    tol_ns = int(round(tol * 1e9))
    lo = np.searchsorted(pk_t, ref_t - tol_ns, side="left")
    hi = np.searchsorted(pk_t, ref_t + tol_ns, side="right")
    cand = [(abs(int(pk_t[j]) - int(ref_t[i])), i, j) for i in range(len(ref_t)) for j in range(lo[i], hi[i])]
    cand.sort()
    out = np.full(len(ref_t), -1)
    used = set()
    for _, i, j in cand:
        if out[i] < 0 and j not in used:
            out[i] = j
            used.add(j)
    return out


def load_picks(net, y, m):
    files = sorted((RAW / "western" / "picks" / f"network={net}" / f"year={y}" / f"month={m:02d}").glob("*.parquet"))
    if not files:
        return pd.DataFrame(columns=["tid", "cha", "pha", "peak", "conf"])
    p = pd.concat([pd.read_parquet(f, columns=["tid", "cha", "pha", "peak", "conf"]) for f in files], ignore_index=True)
    p["netsta"] = p.tid.str.rsplit(".", n=1).str[0]
    return p


def availability(nets):
    a = pd.concat([pd.read_parquet(RAW / "availability" / f"{n}.parquet", columns=["tid", "date", "status", "cha"]) for n in nets])
    a = a[a.status == "loaded"].copy()
    a["netsta"] = a.tid.str.rsplit(".", n=1).str[0]
    a["date"] = pd.to_datetime(a.date)
    return a.groupby(["netsta", "date"]).cha.agg(lambda s: ",".join(sorted(set(s.dropna())))).rename("read_band")


def match_frame(ref, picks):
    """ref: reference picks of one (network, month); picks: catalogue picks of the same partition."""
    ref = ref.copy()
    for tol in TOLS:
        ref[f"matched_{tol}"] = False
    ref["resid_0.5"] = np.nan
    ref["conf_0.5"] = np.nan
    ref["cha_qs_0.5"] = None
    if picks.empty:
        return ref
    pk = picks.sort_values("peak")
    groups = dict(tuple(pk.groupby(["netsta", "pha"])))
    for (ns, ph), r in ref.groupby(["netsta", "phase"]):
        g = groups.get((ns, ph))
        if g is None:
            continue
        r = r.sort_values("t_ref")
        rt = r.t_ref.values.astype("datetime64[ns]").astype(np.int64)
        pt = g.peak.values.astype("datetime64[ns]").astype(np.int64)
        for tol in TOLS:
            j = greedy_match(rt, pt, tol)
            ref.loc[r.index, f"matched_{tol}"] = j >= 0
            if tol == 0.5:
                ok = j >= 0
                ref.loc[r.index[ok], "resid_0.5"] = (pt[j[ok]] - rt[ok]) / 1e9
                ref.loc[r.index[ok], "conf_0.5"] = g.conf.values[j[ok]]
                ref.loc[r.index[ok], "cha_qs_0.5"] = g.cha.values[j[ok]]
    return ref


def main():
    ms = json.load(open(RUN / "data" / "months.json"))
    ref = pd.read_parquet(RUN / "data" / "reference_picks.parquet")
    ref["netsta"] = ref.net + "." + ref.sta
    ref["date"] = ref.t_ref.dt.floor("D")
    st = pd.read_parquet(RAW / "stations.parquet")
    st_ids = set(st.network_code + "." + st.station_code)
    av = availability(["CI", "NC", "BK"])
    ref = ref.join(av, on=["netsta", "date"])
    ref["in_stations"] = ref.netsta.isin(st_ids)
    ref["loaded"] = ref.read_band.notna()
    out = []
    for net in ["CI", "NC", "BK"]:
        for y, m in ms:
            r = ref[(ref.net == net) & (ref.t_ref.dt.year == y) & (ref.t_ref.dt.month == m)]
            if r.empty:
                continue
            out.append(match_frame(r, load_picks(net, y, m)))
            print(net, y, m, len(r), flush=True)
    d = pd.concat(out)
    d.to_parquet(RUN / "data" / "matched.parquet", index=False)
    print("matched table:", len(d), "reference picks;", int((d.loaded & d.in_stations).sum()), "in the denominator")


if __name__ == "__main__":
    main()
