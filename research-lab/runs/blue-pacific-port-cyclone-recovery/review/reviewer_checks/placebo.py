"""Reviewer check 4: the real pipeline's false-alarm rate. Run recovery.one_event, with the real reference index,
on the 85 computed primary-arm events at PLACEBO dates (d0 shifted by -365, +365, -200, +200 days, where history and
follow-up allow and no Cat 1+ storm passed within 250 km of the port in [placebo-30, placebo+120])."""
import sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import recovery as R
HERE = Path(__file__).parent
calls = pickle.load(open(HERE / "cache/calls.pkl", "rb"))
act = calls.mean()
ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv")
pos = ports.set_index("portid")[["lat", "lon"]]
ev = pd.read_csv(RUN / "data/processed/events_all.csv"); ev["date"] = pd.to_datetime(ev.date)
cyclone = ev[ev.cat_at_closest >= 1]
rec = pd.read_csv(RUN / "results/tables/recovery_events.csv")
ok = rec[(rec.status == "ok") & (rec.cat_at_closest >= 3) & (rec.closest_km <= 150)].copy()
ok["date"] = pd.to_datetime(ok.date)
SHIFTS = (-365, 365, -200, 200)

def job(args):
    portid, d0, shift, seed = args
    d = d0 + pd.Timedelta(days=shift)
    # any storm near this port in the placebo window?
    near = cyclone[(cyclone.portid == portid) & (cyclone.date >= d - pd.Timedelta(days=30)) & (cyclone.date <= d + pd.Timedelta(days=120))]
    if len(near): return dict(portid=portid, d0=d0, shift=shift, status="storm_in_window")
    rng = np.random.default_rng(seed)
    idx, ref = R.reference_index(calls, act, pos, cyclone, portid, d)
    res = R.one_event(calls[portid], idx, d, rng, use_index=idx is not None)
    own = R.one_event(calls[portid], None, d, rng, use_index=False)
    return dict(portid=portid, d0=d0, shift=shift, status=res.get("status"), disrupted=res.get("disrupted"), T=res.get("T"),
                depth=res.get("depth_min_ratio"), crit=res.get("depth_crit"), own_disrupted=own.get("disrupted"), own_T=own.get("T"),
                alpha=res.get("alpha"), window=res.get("window"), mean_calls=float(act[portid]), n_ref=len(ref))

if __name__ == "__main__":
    from multiprocessing import Pool
    jobs = [(e.portid, e.date, s, 1000 + i) for i, (_, e) in enumerate(ok.iterrows()) for s in SHIFTS]
    with Pool(14) as pool:
        rows = pool.map(job, jobs, chunksize=4)
    t = pd.DataFrame(rows)
    t = t.merge(ok[["portid", "date", "portname", "storm", "sids", "disrupted"]].rename(columns={"date": "d0", "disrupted": "real_disrupted"}), on=["portid", "d0"])
    t.to_csv(HERE / "placebo.csv", index=False)
    v = t[t.status == "ok"]
    print("placebo runs:", t.status.value_counts().to_dict())
    print(f"\nFALSE-ALARM RATE, reference-index pipeline: {v.disrupted.mean():.3f} ({int(v.disrupted.sum())}/{len(v)}); own-history: {v.own_disrupted.mean():.3f}")
    for s in SHIFTS:
        g = v[v["shift"] == s]; print(f"  shift {s:+d}: {g.disrupted.mean():.3f} ({int(g.disrupted.sum())}/{len(g)})")
    v = v.assign(band=pd.cut(v.mean_calls, [0, 1, 2, 5, 1000], labels=["0.5-1", "1-2", "2-5", ">5"]))
    print("\nby traffic band (index pipeline / own-history):")
    print(v.groupby("band", observed=True).agg(n=("disrupted", "size"), fa_index=("disrupted", "mean"), fa_own=("own_disrupted", "mean"), medT=("T", lambda x: float(np.median(x[x > 0])) if (x > 0).any() else None)).round(3).to_string())
    print("\nby group: SIDS vs non-SIDS ports")
    print(v.groupby("sids").agg(n=("disrupted", "size"), fa_index=("disrupted", "mean"), fa_own=("own_disrupted", "mean")).round(3).to_string())
    print("\nplacebo 'recovery times' of false alarms (index pipeline):", sorted(v[v.disrupted].T.tolist()))
    print("\nports flagged at placebo dates:", v[v.disrupted][["portname", "storm", "shift", "depth", "crit", "T", "mean_calls"]].round(2).to_string(index=False))
    # expected number of the 28 real detections that are false alarms, at the placebo rate
    fa = v.disrupted.mean()
    print(f"\nat a placebo false-alarm rate of {fa:.3f}, expected false alarms among 85 real events = {85*fa:.1f}; among 68 non-SIDS = {68*fa:.1f} (27 detected); among 17 SIDS = {17*fa:.1f} (1 detected)")
