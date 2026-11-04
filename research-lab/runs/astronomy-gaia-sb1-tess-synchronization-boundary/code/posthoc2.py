"""D2 analyses after the independent review (verdict: fix first). Items 4 and 9b are preregistered secondaries that
had not been run; everything else is post hoc and labelled so in the report.

1. Chance null: P_orb permuted among detected stars within each Teff group, 1,000 times; the synchronized share
   that pure coincidence produces.
2. Credible signals: detections with semi-amplitude > 2 ppt and >= 2 detecting sectors.
3. "Inconsistent" stars rescued by a majority cluster: if more than half of a star's detecting sectors agree within
   10% (after the P/2P harmonisation of posthoc.py), only those sectors are kept and the plan's rules reapplied.
4. Preregistered secondary 2 in full: pulsators and possible-beaming stars classified by the same synchronization rule
   and added to the detections.
5. No ACF doubling: the undoubled period used throughout.
6. QLP-only stars compared with TESS-SPOC stars (Tmag, Teff, P_orb).
7. Preregistered secondary 5: states by Teff group x P_orb bin, including 10-12 d; the RUWE distribution by state.
8. H2 with a noise-aware circular criterion: e consistent with zero (e < 2 x eccentricity_error, or SB1C).

  posthoc2.py -> results/tables/posthoc2.json
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
COOL, HOT = (4000, 6200), (6500, 7500)
rng = np.random.default_rng(20261105)


def grp(d, g):
    a, b = COOL if g == "cool" else HOT
    return d[(d.period < 10) & d.teff.between(a, b, inclusive="left")]


def boot_share(y, n=2000):
    y = np.asarray(y, float)
    if not len(y):
        return [None, None]
    bs = [y[rng.integers(0, len(y), len(y))].mean() for _ in range(n)]
    return [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]


def sync_of(p, pps):
    return (np.abs(p / pps - 1) < 0.10).astype(float)


def main():
    out = {}
    st = pd.read_parquet(D / "stars.parquet")
    det = st[st.cls == "detected"].copy()
    # 1 chance null
    for g in ("cool", "hot"):
        x = grp(det, g); obs = float(x.sync.mean()); ch = []
        for _ in range(1000):
            perm = rng.permutation(len(x))
            ch.append(sync_of(x.p_rot.to_numpy(), x.p_ps.to_numpy()[perm]).mean())
        out[f"chance_{g}"] = {"n": len(x), "observed_unweighted": obs, "chance_mean": float(np.mean(ch)), "chance_q975": float(np.quantile(ch, 0.975))}
    # 2 credible signals
    cred = det[(det.amp > 2e-3) & (det.n_sectors_det >= 2)]
    for g in ("cool", "hot"):
        x = grp(cred, g); ch = [sync_of(x.p_rot.to_numpy(), x.p_ps.to_numpy()[rng.permutation(len(x))]).mean() for _ in range(1000)]
        out[f"credible_{g}"] = {"n": len(x), "share": float(x.sync.mean()) if len(x) else None, "ci": boot_share(x.sync), "chance_mean": float(np.mean(ch)) if len(x) else None}
    # 3 majority cluster
    sp = pd.read_parquet(D / "sector_periods_harmonised.parquet")
    incon = set(st.loc[st.cls == "inconsistent", "tic"].dropna().astype("int64"))
    keep = []
    for tic, g in sp[(sp.fap < 1e-5) & sp.tic.isin(incon)].groupby("tic"):
        p = g.p_ls.to_numpy(); best = None
        for c in p:
            m = np.abs(p / c - 1) < 0.10
            if best is None or m.sum() > best.sum():
                best = m
        if best.sum() > len(p) / 2:
            keep.append(g[best])
        else:
            keep.append(g)
    sp2 = pd.concat([sp[~(sp.tic.isin(incon) & (sp.fap < 1e-5))]] + keep)
    sp2.to_parquet(D / "sector_periods_majority.parquet")
    env = {**os.environ, "SECTOR_IN": "sector_periods_majority.parquet", "STARS_OUT": "stars_majority.parquet", "LC_PRODUCTS": "tess-spoc"}
    subprocess.run([PY, "-I", str(RUN / "code" / "classify.py")], env=env, check=True, capture_output=True)
    sm = pd.read_parquet(D / "stars_majority.parquet"); dm = sm[sm.cls == "detected"]
    out["majority_cluster"] = {"classes": sm.cls.value_counts().to_dict(),
                               **{g: {"n": len(grp(dm, g)), "share": float(grp(dm, g).sync.mean())} for g in ("cool", "hot")}}
    # 4 secondary 2 in full
    wide = st[st.cls.isin(["detected", "pulsator", "possible_beaming"])].copy(); wide["s2"] = sync_of(wide.p_rot, wide.p_ps)
    out["secondary2_with_pulsators_and_beaming"] = {g: {"n": len(grp(wide, g)), "share": float(grp(wide, g).s2.mean()),
                                                        "pulsators_share": float(grp(wide[wide.cls == "pulsator"], g).s2.mean())} for g in ("cool", "hot")}
    # 5 no doubling
    nd = det.copy(); nd["s"] = sync_of(nd.p_ls_med, nd.p_ps)
    out["no_doubling"] = {g: float(grp(nd, g).s.mean()) for g in ("cool", "hot")}
    out["doubled_detections_sync_before_doubling"] = int((det.doubled & (sync_of(det.p_ls_med, det.p_ps) == 1)).sum())
    # 6 QLP-only vs SPOC
    sp0 = pd.read_parquet(D / "sector_periods.parquet"); sp0 = sp0[sp0.n > 0]
    spoc = set(sp0[sp0["product"] == "tess-spoc"].tic); qlp = set(sp0.tic) - spoc
    out["qlp_only_vs_spoc"] = {nm: {"n": int(st.tic.isin(s).sum()), "Tmag_med": float(st[st.tic.isin(s)].Tmag.median()),
                                    "teff_med": float(st[st.tic.isin(s)].teff.median()), "porb_med": float(st[st.tic.isin(s)].period.median())}
                               for nm, s in (("spoc", spoc), ("qlp_only", qlp))}
    # 7 secondary 5 and RUWE
    pb = [0.5, 2, 4, 6, 8, 10, 12]
    sec5 = {}
    for g in ("cool", "hot"):
        a, b = COOL if g == "cool" else HOT
        x = det[det.teff.between(a, b, inclusive="left")]
        sec5[g] = x.groupby(pd.cut(x.period, pb), observed=True).sync_state.value_counts(normalize=True).round(3).unstack(fill_value=0).rename(index=str).to_dict("index")
    out["secondary5_states_by_porb"] = sec5
    out["ruwe_median_by_state"] = det.groupby("sync_state").ruwe.median().round(3).to_dict()
    out["panel25_check"] = st[st.tic == 117738228][["tic", "period", "eccentricity", "p_ps", "p_rot", "p_ls_med", "doubled", "cls", "sync_state"]].astype(str).to_dict("records")
    # 8 H2 with a noise-aware circular criterion
    s = pd.read_parquet(D / "sample.parquet")
    s["circ_na"] = ((s.nss_solution_type == "SB1C") | (s.eccentricity.fillna(1) < 2 * s.eccentricity_error.fillna(0))).astype(float)
    h2 = {}
    for nm, (a, b) in {"4000-5500": (4000, 5500), "5500-6200": (5500, 6200), "6200-7000": (6200, 7000)}.items():
        c = s[s.teff.between(a, b, inclusive="left") & s.period.between(0.5, 30)]
        h2[nm] = {"n": len(c), "P_circ50_noise_aware": AN.fit_mid(np.log(c.period.to_numpy()), c.circ_na.to_numpy(), np.ones(len(c))),
                  "circular_share_below_3d": float(c[c.period < 3].circ_na.mean())}
    out["h2_noise_aware_circularization"] = h2
    (T / "posthoc2.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, default=str)[:4000])


if __name__ == "__main__":
    main()
