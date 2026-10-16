"""Reviewer: Monte Carlo stability of the disruption threshold. The 5th-percentile threshold comes from 2000 simulated
paths drawn from one global generator, so it carries simulation noise; at quiet ports the depth statistic is also
discrete. Rerun the borderline detections (and Suva/Harold, whose threshold differed under a fresh seed) with 8 seeds."""
import sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RUN / "code"))
import recovery as R
HERE = Path(__file__).parent
calls = pickle.load(open(HERE / "cache/calls.pkl", "rb")); act = calls.mean()
ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv"); pos = ports.set_index("portid")[["lat", "lon"]]
ev = pd.read_csv(RUN / "data/processed/events_all.csv"); ev["date"] = pd.to_datetime(ev.date); cyclone = ev[ev.cat_at_closest >= 1]
rec = pd.read_csv(RUN / "results/tables/recovery_events.csv"); rec["date"] = pd.to_datetime(rec.date)
ok = rec[(rec.status == "ok") & (rec.cat_at_closest >= 3) & (rec.closest_km <= 150)].copy()
ok["margin"] = ok.depth_min_ratio - ok.depth_crit
border = pd.concat([ok[ok.margin.abs() < 0.06], ok[(ok.portname == "Suva") & (ok.storm == "HAROLD")]])
def job(args):
    portid, d0, seed = args
    idx, _ = R.reference_index(calls, act, pos, cyclone, portid, d0)
    res = R.one_event(calls[portid], idx, d0, np.random.default_rng(seed), use_index=idx is not None)
    return dict(portid=portid, d0=d0, seed=seed, crit=res["depth_crit"], disrupted=res["disrupted"], T=res["T"])
if __name__ == "__main__":
    from multiprocessing import Pool
    jobs = [(e.portid, e.date, s) for _, e in border.iterrows() for s in range(8)]
    with Pool(16) as pool: rows = pool.map(job, jobs)
    t = pd.DataFrame(rows).merge(border[["portid", "date", "portname", "storm", "depth_min_ratio", "depth_crit", "disrupted", "T", "mean_calls"]].rename(columns={"date": "d0", "disrupted": "study_disrupted", "T": "study_T", "depth_crit": "study_crit"}), on=["portid", "d0"])
    g = t.groupby(["portname", "storm"]).agg(calls=("mean_calls", "first"), dip=("depth_min_ratio", "first"), study_crit=("study_crit", "first"), crit_min=("crit", "min"), crit_max=("crit", "max"),
                                             study_disrupted=("study_disrupted", "first"), share_disrupted_8seeds=("disrupted", "mean"), T_values=("T", lambda x: sorted(set(x.round(0)))))
    pd.set_option("display.width", 200); print(g.round(3).to_string())
    t.to_csv(HERE / "borderline_seeds.csv", index=False)
