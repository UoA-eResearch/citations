"""Post hoc analyses (labelled as such in the report), run after the primary results were seen.

1. Harmonised periods: 7,267 stars were "inconsistent", mostly because the periodogram picked P in some sectors and
   P/2 in others (median span 2.06). Each detecting sector's period is mapped to whichever of p, 2p and p/2 is
   closest to the best sector's period; the plan's rules are then applied unchanged.
2. QLP detrended (the sensitivity promised in D1): TESS-SPOC sectors plus QLP sectors detrended per segment.
3. Why H2 is not estimable: the synchronized and circular shares by orbital period.
4. Crowding: the synchronized share by TESS magnitude tercile and by number of detecting sectors.
5. The Teff transition: the profile log-likelihood over the midpoint T0.
6. Synchronization against P_orb directly: Gaia eccentricities of near-circular orbits are biased upward by noise,
   and the plan's Hut pseudo-synchronous period then moves the target away from P_orb (G3 trace 2).

  posthoc.py -> results/tables/posthoc.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as AN  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
PY = str(RUN / "venv" / "bin" / "python")


def shares(stars_file):
    st = pd.read_parquet(D / stars_file)
    det = st[st.cls == "detected"].copy(); det["C"] = AN.weights(det); det = det[det.C >= 0.1]; det["w"] = 1 / det.C
    det["y"] = det.sync.astype(float); h = det[det.period < 10]
    c, ht = h.teff.between(4000, 6200, inclusive="left"), h.teff.between(6500, 7500, inclusive="left")
    return {"classes": st.cls.value_counts().to_dict(), "n_cool": int(c.sum()), "n_hot": int(ht.sum()),
            "f_cool": AN.wshare(h.y[c], h.w[c]), "f_hot": AN.wshare(h.y[ht], h.w[ht])}


def classify(sector_in, stars_out, products):
    env = {**os.environ, "SECTOR_IN": sector_in, "STARS_OUT": stars_out, "LC_PRODUCTS": products}
    subprocess.run([PY, "-I", str(RUN / "code" / "classify.py")], env=env, check=True, capture_output=True)


def main():
    out = {}
    sp = pd.read_parquet(D / "sector_periods.parquet"); sp = sp[sp["product"] == "tess-spoc"].copy()
    det = sp.fap < 1e-5
    best = sp[det].sort_values("power", ascending=False).drop_duplicates("tic").set_index("tic").p_ls
    b = sp.loc[det, "tic"].map(best).to_numpy(); p = sp.loc[det, "p_ls"].to_numpy()
    cand = np.vstack([p, 2 * p, p / 2]); k = np.argmin(np.abs(np.log(cand / b)), axis=0)
    sp.loc[det, "p_ls"] = cand[k, np.arange(len(p))]
    sp.to_parquet(D / "sector_periods_harmonised.parquet")
    classify("sector_periods_harmonised.parquet", "stars_harmonised.parquet", "tess-spoc")
    out["harmonised"] = shares("stars_harmonised.parquet")
    if (D / "sector_periods_qlpd.parquet").exists():
        both = pd.concat([pd.read_parquet(D / "sector_periods.parquet").query("product == 'tess-spoc'"), pd.read_parquet(D / "sector_periods_qlpd.parquet")])
        both.to_parquet(D / "sector_periods_spoc_qlpd.parquet")
        classify("sector_periods_spoc_qlpd.parquet", "stars_qlpd.parquet", "tess-spoc,qlp")
        q = pd.read_parquet(D / "sector_periods_qlpd.parquet")
        out["qlp_detrended"] = {**shares("stars_qlpd.parquet"), "qlp_sector_detection_rate": float((q.fap < 1e-5).mean()),
                                "qlp_share_9_13d": float(((q.fap < 1e-5) & (q.p_ls > 9)).sum() / max((q.fap < 1e-5).sum(), 1))}
    st = pd.read_parquet(D / "stars.parquet")
    d = st[st.cls == "detected"]
    allst = pd.read_parquet(D / "sample.parquet")
    allst["circ"] = (allst.nss_solution_type == "SB1C") | (allst.eccentricity.fillna(1) < 0.05)
    pb = [0.5, 1, 2, 3, 5, 7, 10, 12, 20, 30]
    out["sync_share_by_porb"] = d.groupby(pd.cut(d.period, pb), observed=True).sync.agg(["mean", "size"]).round(3).rename(index=str).astype(str).to_dict("index")
    out["circular_share_by_porb"] = allst.groupby(pd.cut(allst.period, pb), observed=True).circ.agg(["mean", "size"]).round(3).rename(index=str).astype(str).to_dict("index")
    out["eccentricity_median_by_porb"] = allst.groupby(pd.cut(allst.period, pb), observed=True).eccentricity.median().round(3).rename(index=str).astype(str).to_dict()
    porb_sync = (np.abs(d.p_rot / d.period - 1) < 0.10)
    dd = d.copy(); dd["C"] = AN.weights(dd); dd = dd[(dd.C >= 0.1) & (dd.period < 10)]; dd["w"] = 1 / dd.C
    yy = (np.abs(dd.p_rot / dd.period - 1) < 0.10).astype(float)
    cc, hh = dd.teff.between(4000, 6200, inclusive="left"), dd.teff.between(6500, 7500, inclusive="left")
    out["sync_vs_porb"] = {"f_cool": AN.wshare(yy[cc], dd.w[cc]), "f_hot": AN.wshare(yy[hh], dd.w[hh]),
                           "detected_sync_to_porb_not_pps": int((porb_sync & ~d.sync.astype(bool)).sum()),
                           "detected_sync_to_pps_not_porb": int((~porb_sync & d.sync.astype(bool)).sum())}
    d = d.assign(tq=pd.qcut(d.Tmag, 3, labels=["bright", "middle", "faint"]))
    out["sync_share_by_tmag"] = {str(k): v for k, v in d.groupby("tq", observed=True).sync.mean().round(3).to_dict().items()}
    out["sync_share_by_n_sectors"] = {str(k): v for k, v in d.groupby(np.minimum(d.n_sectors_det, 4)).sync.mean().round(3).to_dict().items()}
    # profile likelihood over T0 (H1's logistic, weights as in the primary)
    det2 = d.copy(); det2["C"] = AN.weights(det2); det2 = det2[det2.C >= 0.1]; det2["w"] = 1 / det2.C
    h = det2[(det2.period < 10) & det2.teff.between(4000, 7500)]
    y, w, Tf = h.sync.astype(float).to_numpy(), h.w.to_numpy(), h.teff.to_numpy()
    from scipy.optimize import minimize
    prof = {}
    for T0 in range(5400, 7201, 100):
        def nll(th):
            lo, hi, lw = th
            pr = np.clip(lo + (hi - lo) / (1 + np.exp((Tf - T0) / np.exp(lw))), 1e-6, 1 - 1e-6)
            return -np.sum(w * (y * np.log(pr) + (1 - y) * np.log(1 - pr)))
        r = minimize(nll, [0.1, 0.25, np.log(150)], method="L-BFGS-B", bounds=[(0, 1), (0, 1), (np.log(10), np.log(3000))])
        prof[T0] = round(float(r.fun), 2)
    m = min(prof.values()); out["T0_profile_delta_nll"] = {k: round(v - m, 2) for k, v in prof.items()}
    (T / "posthoc.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("T0_profile_delta_nll",)}, default=str)[:3000])
    print("T0 profile", out["T0_profile_delta_nll"])


if __name__ == "__main__":
    main()
