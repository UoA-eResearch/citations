"""Secondary check of the strain proxy (plan section 5).

40 broadband stations with LHZ data, drawn with seed 20261026 from stations in the primary population, one per 2-degree
cell first; for every population trigger at those stations, peak vertical velocity bandpassed 15-60 s within the
surface-wave window (origin + D/4.5 km/s - 5 min to origin + D/2.5 km/s + 5 min), instrument response removed, from
EarthScope FDSN. Spearman correlation with the estimated PGV, and quintile agreement.
-> results/tables/strain_check.csv, results/tables/strain_check.json
"""
import json
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
from windows import strain  # noqa: E402

SEED, NSTA = 20261026, 40


def pick_stations(pop):
    from obspy.clients.fdsn import Client
    c = Client("https://service.iris.edu", timeout=120)
    st = pd.read_parquet(D / "raw" / "stations.parquet", columns=["id", "latitude", "longitude"]).groupby("id").median()
    st = st.loc[st.index.intersection(pop.tid.unique())].copy()
    st["cell"] = (np.floor(st.latitude / 2)).astype(int).astype(str) + "_" + (np.floor(st.longitude / 2)).astype(int).astype(str)
    rng = np.random.default_rng(SEED)
    order = []
    cells = list(st.groupby("cell"))
    rng.shuffle(cells)
    for _, g in cells:                                                   # one per cell first, then the rest
        order.append(g.index[int(rng.integers(len(g)))])
    rest = [t for t in st.index if t not in set(order)]
    rng.shuffle(rest)
    chosen = []
    for tid in order + rest:
        net, sta = tid.split(".")[:2]
        try:
            inv = c.get_stations(network=net, station=sta, channel="LHZ", level="channel")
            if len(inv.get_contents()["channels"]):
                chosen.append(tid)
        except Exception:
            pass
        if len(chosen) == NSTA:
            break
    return chosen


def one(args):
    from obspy import UTCDateTime
    from obspy.clients.fdsn import Client
    tid, trig, o_ms, dist = args
    net, sta = tid.split(".")[:2]
    t0 = UTCDateTime(o_ms / 1000 + dist / 4.5 - 300)
    t1 = UTCDateTime(o_ms / 1000 + dist / 2.5 + 300)
    try:
        c = Client("https://service.iris.edu", timeout=120)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = c.get_waveforms(net, sta, "*", "LHZ", t0 - 600, t1 + 600, attach_response=True)
            s.merge(fill_value=0)
            tr = s[0]
            tr.detrend("linear"); tr.taper(0.05)
            tr.remove_response(output="VEL", pre_filt=(0.01, 0.0167, 0.0667, 0.1))
            tr.filter("bandpass", freqmin=1 / 60, freqmax=1 / 15, corners=4, zerophase=True)
            tr.trim(t0, t1)
            return {"tid": tid, "trigger": trig, "pgv_measured": float(np.abs(tr.data).max())}
    except Exception as e:
        return {"tid": tid, "trigger": trig, "pgv_measured": np.nan, "error": type(e).__name__}


def main():
    pr = pd.read_parquet(T / "pairs_primary.parquet")
    pop = pr[pr.in_population]
    chosen = pick_stations(pop)
    tr = pd.read_csv(D / "cat" / "triggers_m7.csv", parse_dates=["time"]).set_index("id")
    jobs = [(r.tid, r.trigger, int(tr.loc[r.trigger, "time"].value // 10**6), r.dist_km)
            for r in pop[pop.tid.isin(chosen)].itertuples()]
    with ThreadPoolExecutor(8) as ex:
        res = pd.DataFrame(list(ex.map(one, jobs)))
    d = pop[pop.tid.isin(chosen)][["tid", "trigger", "mag", "dist_km", "strain"]].merge(res, on=["tid", "trigger"])
    d["pgv_estimated"] = d.strain * 3500.0
    d.to_csv(T / "strain_check.csv", index=False)
    ok = d.dropna(subset=["pgv_measured"])
    ok = ok[ok.pgv_measured > 0]
    qe = pd.qcut(ok.pgv_estimated.rank(method="first"), 5, labels=False)
    qm = pd.qcut(ok.pgv_measured.rank(method="first"), 5, labels=False)
    out = {"stations": len(chosen), "pairs": int(len(d)), "measured": int(len(ok)),
           "spearman": round(float(ok.pgv_estimated.corr(ok.pgv_measured, method="spearman")), 4),
           "same_quintile": round(float((qe == qm).mean()), 4), "within_one_quintile": round(float((abs(qe - qm) <= 1).mean()), 4),
           "median_ratio_measured_to_estimated": round(float((ok.pgv_measured / ok.pgv_estimated).median()), 4)}
    (T / "strain_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
