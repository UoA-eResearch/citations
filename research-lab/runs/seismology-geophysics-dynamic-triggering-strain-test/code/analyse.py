"""H1 and H2 (plan section 0) and the secondary summaries (section 6). Written before any window count was computed.

Excess per station x trigger = I(beta >= 2) - p0 of the station. Quintiles of estimated strain over all population
pairs. Two-way bootstrap: triggers and stations resampled independently with replacement (2,000, seed 20261026);
a pair's weight is the product of its trigger's and station's multiplicities.
  H1 Supported if E5 lower95 > 0, (E5 - 3 E1) lower95 > 0 and E1's 90% interval includes 0;
     Refuted if (E5 - 3 E1) upper95 < 0 or E5 upper95 <= 0; Inconclusive otherwise.
  H2 Supported if the overall mean excess lower95 > 0; Refuted if upper95 < 0.005; Inconclusive otherwise.
usage: analyse.py [VARIANT ...]  -> results/tables/primary.json (and robustness entries)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEED, B = 20261026, 2000
GEOTHERMAL = {"The Geysers": (38.79, -122.76), "Coso": (36.03, -117.80), "Salton Sea": (33.17, -115.60),
              "Long Valley": (37.65, -118.90), "Yellowstone": (44.60, -110.50)}


def stats_for(d, w=None):
    w = np.ones(len(d)) if w is None else w
    out = {}
    for q in range(1, 6):
        m = d.q.to_numpy() == q
        out[q] = float(np.sum(w[m] * d.excess.to_numpy()[m]) / np.sum(w[m])) if np.sum(w[m]) else np.nan
    out["all"] = float(np.sum(w * d.excess.to_numpy()) / np.sum(w))
    return out


def summarise(d, rng):
    d = d.copy()
    d["q"] = pd.qcut(d.strain.rank(method="first"), 5, labels=False) + 1
    est = stats_for(d)
    trig, stas = d.trigger.unique(), d.tid.unique()
    ti = {t: i for i, t in enumerate(trig)}
    si = {s: i for i, s in enumerate(stas)}
    tix, six = d.trigger.map(ti).to_numpy(), d.tid.map(si).to_numpy()
    bs = []
    for _ in range(B):
        wt = np.bincount(rng.integers(len(trig), size=len(trig)), minlength=len(trig))
        ws = np.bincount(rng.integers(len(stas), size=len(stas)), minlength=len(stas))
        w = (wt[tix] * ws[six]).astype(float)
        if w.sum() == 0:
            continue
        bs.append(stats_for(d, w))
    bs = pd.DataFrame(bs)
    ci = lambda x, a=95: [round(float(np.nanpercentile(x, (100 - a) / 2)), 5), round(float(np.nanpercentile(x, 100 - (100 - a) / 2)), 5)]
    diff = bs[5] - 3 * bs[1]
    e5, e1 = ci(bs[5]), ci(bs[1], 90)
    d53 = ci(diff)
    h1 = ("Supported" if (e5[0] > 0 and d53[0] > 0 and e1[0] <= 0 <= e1[1])
          else "Refuted" if (d53[1] < 0 or e5[1] <= 0) else "Inconclusive")
    allci = ci(bs["all"])
    h2 = "Supported" if allci[0] > 0 else "Refuted" if allci[1] < 0.005 else "Inconclusive"
    qs = d.groupby("q").agg(pairs=("excess", "size"), strain_lo=("strain", "min"), strain_hi=("strain", "max"),
                            observed_sig=("sig", "mean"), mean_p0=("p0", "mean"))
    return {"pairs": int(len(d)), "triggers": int(len(trig)), "stations": int(len(stas)),
            "E": {str(k): round(v, 5) for k, v in est.items()},
            "E_ci95": {str(q): ci(bs[q]) for q in (1, 2, 3, 4, 5, "all")}, "E1_ci90": e1, "E5_minus_3E1": round(est[5] - 3 * est[1], 5),
            "E5_minus_3E1_ci95": d53, "H1": h1, "H2": h2,
            "quintiles": {str(k): {kk: (float(vv) if isinstance(vv, (float, np.floating)) else int(vv)) for kk, vv in r.items()} for k, r in qs.iterrows()},
            "expected_false_positives": round(float(d.p0.sum()), 1), "observed_significant": int(d.sig.sum())}


def main():
    variants = sys.argv[1:] or ["primary"]
    rng = np.random.default_rng(SEED)
    out = json.loads((T / "primary.json").read_text()) if (T / "primary.json").exists() else {}
    for v in variants:
        pr = pd.read_parquet(T / f"pairs_{v}.parquet")
        d = pr[pr.in_population].copy()
        out[v] = summarise(d, rng)
        if v == "primary":
            st = pd.read_parquet(RUN / "data" / "raw" / "stations.parquet", columns=["id", "latitude", "longitude"]).groupby("id").median()
            ll = st.reindex(d.tid)
            geo = np.zeros(len(d), bool)
            for la, lo in GEOTHERMAL.values():
                geo |= ((ll.latitude.to_numpy() - la).__abs__() <= 0.3) & ((ll.longitude.to_numpy() - lo).__abs__() <= 0.3)
            out["no_geothermal"] = summarise(d[~geo], rng)
            out["no_m8"] = summarise(d[d.mag <= 8.0], rng)
            dd = d.copy()
            dd["decile"] = pd.qcut(dd.strain.rank(method="first"), 10, labels=False) + 1
            out["deciles"] = dd.groupby("decile").agg(pairs=("excess", "size"), strain_median=("strain", "median"),
                                                      excess=("excess", "mean")).round(6).reset_index().to_dict("records")
            out["by_trigger_top"] = (d.groupby("trigger").agg(pairs=("excess", "size"), mag=("mag", "first"),
                                                             observed=("sig", "sum"), expected=("p0", "sum"))
                                     .assign(excess=lambda x: x.observed - x.expected).sort_values("excess", ascending=False)
                                     .head(15).round(2).reset_index().to_dict("records"))
        print(v, json.dumps({k: out[v][k] for k in ("pairs", "E", "H1", "H2")}), flush=True)
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
