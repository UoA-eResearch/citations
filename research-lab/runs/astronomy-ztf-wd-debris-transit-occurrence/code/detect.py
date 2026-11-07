"""Detection, injection-recovery and occurrence (plan section 0). Run only after results/tables/known_systems.csv
(the positive controls) was committed.

  detect.py detect      the two preregistered rules on every sample star -> results/tables/detect.parquet
  detect.py inject      5,000 random eligible stars x 3 classes x 10 injections -> results/tables/inject.parquet
  detect.py occurrence  known-system recovery, candidates, completeness tables and rates -> results/tables/primary.json

Light curves (data/lc/) hold good epochs only (catflags = 0, magerr < 0.25), one ZTF object per filter (the one with
the most good epochs within 2 arcsec of the epoch-2019.0 position).
Rules (plan section 0):
  short: per filter, robust sigma = 1.4826 MAD about the median; faint = epochs > median + 3 sigma, bright = epochs
         < median - 3 sigma, pooled over filters. Flag if faint - bright >= 5, the one-sided binomial P(X >= faint |
         faint + bright, 1/2) < 1e-6, and the faint epochs fall on >= 3 nights (floor of MJD).
  long:  flux relative to each filter's median, pooled; 30-day bins with >= 5 epochs; a bin is low if its median is
         below the global median by > 5 standard errors (std / sqrt(n)) and by >= 5% of flux. Flag if >= 2 low bins.
Injection details not fixed by the plan (decided here, before any detection was run): box-shaped dips applied as
flux multipliers; magnitude errors scaled by (flux ratio)^-1/2; injected epochs fainter than 21.0 mag are dropped
as non-detections; seasons are runs of epochs separated by gaps > 60 days; stars flagged before injection are not
used for injection.
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import binom

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
T.mkdir(parents=True, exist_ok=True)
MIN_EPOCHS, SEED, LIMIT_MAG = 100, 20261107, 21.0


def short_rule(filt, mag, mjd, k=3.0):
    faint = np.zeros(len(mag), bool)
    bright = np.zeros(len(mag), bool)
    for f in np.unique(filt):
        m = filt == f
        if m.sum() < 5:
            continue
        med = np.median(mag[m])
        sig = 1.4826 * np.median(np.abs(mag[m] - med))
        if sig <= 0:
            continue
        faint[m] = mag[m] > med + k * sig
        bright[m] = mag[m] < med - k * sig
    nf, nb = int(faint.sum()), int(bright.sum())
    p = float(binom.sf(nf - 1, nf + nb, 0.5)) if nf + nb > 0 else 1.0
    nights = int(len(np.unique(np.floor(mjd[faint])))) if nf else 0
    return {"faint": nf, "bright": nb, "excess": nf - nb, "p_binom": p, "faint_nights": nights,
            "short": bool(nf - nb >= 5 and p < 1e-6 and nights >= 3)}


def long_rule(filt, mag, mjd, k=5.0):
    rel = np.empty(len(mag))
    for f in np.unique(filt):
        m = filt == f
        rel[m] = 10 ** (-0.4 * (mag[m] - np.median(mag[m])))
    gmed = np.median(rel)
    b = np.floor((mjd - mjd.min()) / 30.0).astype(int)
    low = 0
    for v in np.unique(b):
        x = rel[b == v]
        if len(x) < 5:
            continue
        se = x.std(ddof=1) / np.sqrt(len(x))
        med = np.median(x)
        if (gmed - med) > k * se and (gmed - med) >= 0.05:
            low += 1
    return {"low_bins": low, "long": bool(low >= 2)}


def rules(filt, mag, mjd, ks=3.0, kl=5.0):
    return {**short_rule(filt, mag, mjd, ks), **long_rule(filt, mag, mjd, kl)}


def load_shard(path):
    t = pq.read_table(path, columns=["source_id", "filt", "mjd", "mag", "magerr"]).to_pandas()
    return {sid: g for sid, g in t.groupby("source_id")}


def detect_shard(path):
    rows = []
    for sid, g in load_shard(path).items():
        n = len(g)
        row = {"source_id": int(sid), "n_epochs": n, "n_g": int((g.filt == "zg").sum()), "n_r": int((g.filt == "zr").sum())}
        if n >= MIN_EPOCHS:
            f, m, t = g.filt.to_numpy(), g.mag.to_numpy(), g.mjd.to_numpy()
            row.update(rules(f, m, t))
            for ks in (2.5, 3.5):
                row[f"short_{ks}"] = short_rule(f, m, t, ks)["short"]
            for kl in (3.0, 7.0):
                row[f"long_{kl:g}"] = long_rule(f, m, t, kl)["long"]
        rows.append(row)
    return rows


def detect():
    files = sorted((D / "lc_v2").glob("shard_*.parquet"))   # D1: true Gaia IDs
    rows = []
    with ProcessPoolExecutor(16) as ex:
        for r in ex.map(detect_shard, files):
            rows += r
    d = pd.DataFrame(rows)
    d.to_parquet(T / "detect.parquet", index=False)
    e = d[d.n_epochs >= MIN_EPOCHS]
    print("stars with light curves", len(d), "eligible", len(e), "short", int(e.short.sum()), "long", int(e.long.sum()),
          "either", int((e.short | e.long).sum()))


def seasons(mjd):
    o = np.argsort(mjd)
    s = np.zeros(len(mjd), int)
    s[o] = np.cumsum(np.r_[0, np.diff(mjd[o]) > 60])
    return s


def inject_one(filt, mag, err, mjd, cls, rng):
    flux = np.ones(len(mag))
    if cls == "wd1145":
        P = rng.uniform(3, 12) / 24
        duty, depth = rng.uniform(0.05, 0.30), rng.uniform(0.10, 0.60)
        s = seasons(mjd)
        us = np.unique(s)
        act = rng.choice(us, max(1, int(np.ceil(rng.uniform(0.5, 1.0) * len(us)))), replace=False)
        ph = ((mjd / P) + rng.random()) % 1.0
        dim = (ph < duty) & np.isin(s, act)
    elif cls == "j0139":
        P = np.exp(rng.uniform(np.log(10 / 24), np.log(120)))
        dur = np.exp(rng.uniform(np.log(0.02 * P), np.log(max(0.02 * P * 1.0001, min(25.0, 0.5 * P)))))
        depth = rng.uniform(0.10, 0.50)
        ph = ((mjd / P) + rng.random()) % 1.0
        dim = ph < dur / P
    else:
        dur, depth = rng.uniform(30, 400), rng.uniform(0.25, 1.0)
        t0 = rng.uniform(mjd.min() - dur, mjd.max())
        dim = (mjd >= t0) & (mjd < t0 + dur)
    flux[dim] = 1 - depth
    keep = flux > 0
    m2 = np.where(keep, mag - 2.5 * np.log10(np.where(keep, flux, 1)), np.inf)
    e2 = err / np.sqrt(np.where(keep, flux, 1))
    keep &= m2 <= LIMIT_MAG
    return filt[keep], m2[keep], e2[keep], mjd[keep]


def inject_shard(args):
    path, items = args
    lcs = load_shard(path)
    out = []
    for sid, seed in items:
        g = lcs[sid]
        f, m, e, t = g.filt.to_numpy(), g.mag.to_numpy(), g.magerr.to_numpy(), g.mjd.to_numpy()
        rng = np.random.default_rng([SEED, seed])
        for cls in ("wd1145", "j0139", "oneoff"):
            for i in range(10):
                f2, m2, e2, t2 = inject_one(f, m, e, t, cls, rng)
                r = rules(f2, m2, t2) if len(m2) >= 10 else {"short": False, "long": False}
                out.append({"source_id": int(sid), "cls": cls, "i": i, "rec": bool(r["short"] or r["long"]),
                            "rec_short": bool(r["short"]), "rec_long": bool(r["long"])})
    return out


def inject():
    d = pd.read_parquet(T / "detect.parquet")
    e = d[(d.n_epochs >= MIN_EPOCHS) & ~(d.short.fillna(False) | d.long.fillna(False))]
    pick = e.sample(5000, random_state=SEED).source_id.astype(int).tolist()
    seed_of = {s: k for k, s in enumerate(pick)}
    jobs = []
    for p in sorted((D / "lc_v2").glob("shard_*.parquet")):
        ids = set(pq.read_table(p, columns=["source_id"]).column(0).unique().to_pylist()) & set(pick)
        if ids:
            jobs.append((p, [(s, seed_of[s]) for s in sorted(ids)]))
    rows = []
    with ProcessPoolExecutor(16) as ex:
        for r in ex.map(inject_shard, jobs):
            rows += r
    pd.DataFrame(rows).to_parquet(T / "inject.parquet", index=False)
    print("injections", len(rows))


def poisson_ci(n, a=0.05):
    from scipy.stats import chi2
    lo = 0.0 if n == 0 else chi2.ppf(a / 2, 2 * n) / 2
    hi = chi2.ppf(1 - a / 2, 2 * (n + 1)) / 2
    return lo, hi


CLASS_OF_DIP = {"short": "wd1145", "long": "j0139", "one-off": "oneoff"}


def dip_class(text):
    t = str(text).lower()
    if t.startswith("one-off") or "one-off" in t[:30]:
        return "oneoff"
    if t.startswith("long"):
        return "j0139"
    return "wd1145"


def occurrence():
    d = pd.read_parquet(T / "detect.parquet")
    s = pd.read_parquet(D / "sample.parquet")[["source_id", "phot_g_mean_mag", "parallax", "bp_rp"]]
    e = d[d.n_epochs >= MIN_EPOCHS].merge(s, on="source_id")
    e["flag"] = e.short.fillna(False) | e.long.fillna(False)
    k = pd.read_csv(T / "known_systems.csv")
    k = k[k.in_sample]
    k["cls"] = k.dip_type.map(dip_class)
    kid = set(k.gaia_dr3_source_id_in_sample.astype(int))
    v = pd.read_csv(T / "flagged_gaia_vari.csv")
    var = set(v[v.best_class_name.isin(["ECL", "CV", "RS", "SOLAR_LIKE"])].source_id.astype(int))
    e["known"] = e.source_id.isin(kid)
    e["gaia_variable"] = e.source_id.isin(var)
    rec_known = e[e.known & e.flag]
    cand = e[e.flag & ~e.known & ~e.gaia_variable]
    cand[["source_id", "phot_g_mean_mag", "parallax", "bp_rp", "n_epochs", "excess", "p_binom", "faint_nights", "low_bins", "short", "long"]] \
        .to_csv(T / "candidates.csv", index=False)
    # completeness by class, G bin and epoch bin, from the injections
    inj = pd.read_parquet(T / "inject.parquet").merge(e[["source_id", "phot_g_mean_mag", "n_epochs"]], on="source_id")
    gb, nb = [0, 17, 18, 19, 19.5, 21], [100, 400, 700, 1000, 1500, 10**6]
    for x in (inj, e):
        x["gbin"] = pd.cut(x.phot_g_mean_mag, gb, labels=False, include_lowest=True)
        x["nbin"] = pd.cut(x.n_epochs, nb, labels=False, include_lowest=True)
    C = inj.groupby(["cls", "gbin", "nbin"]).rec.mean().rename("C").reset_index()
    ctab = {c: C[C.cls == c].pivot(index="gbin", columns="nbin", values="C").round(3).to_dict() for c in ("wd1145", "j0139", "oneoff")}
    for c in ("wd1145", "j0139", "oneoff"):
        e = e.merge(C[C.cls == c][["gbin", "nbin", "C"]].rename(columns={"C": f"C_{c}"}), on=["gbin", "nbin"], how="left")
        e[f"C_{c}"] = e[f"C_{c}"].fillna(inj[inj.cls == c].rec.mean())
    e["C_best"] = e[["C_wd1145", "C_j0139", "C_oneoff"]].max(axis=1)
    out = {"eligible_stars": int(len(e)), "flagged": int(e.flag.sum()), "flagged_short": int(e.short.fillna(False).sum()),
           "flagged_long": int(e.long.fillna(False).sum()), "known_in_sample": int(len(k)), "known_eligible": int(e.known.sum()),
           "known_recovered": int(len(rec_known)), "known_missed": sorted(k[~k.gaia_dr3_source_id_in_sample.astype(int).isin(set(rec_known.source_id))].name.tolist()),
           "gaia_variables_removed": int((e.flag & e.gaia_variable).sum()), "candidates": int(len(cand)),
           "injection_recovery_by_class": inj.groupby("cls").rec.mean().round(4).to_dict(), "completeness_tables": ctab}
    rates = {}
    for name, col in (("wd1145", "C_wd1145"), ("j0139", "C_j0139"), ("oneoff", "C_oneoff"), ("combined", "C_best")):
        S = float(e[col].sum())
        nk = int(len(rec_known)) if name == "combined" else int(((k.cls == name) & k.gaia_dr3_source_id_in_sample.astype(int).isin(set(rec_known.source_id))).sum())
        nu = nk + int(len(cand))
        lo, hi = [x / S for x in poisson_ci(nk)], [x / S for x in poisson_ci(nu)]
        rates[name] = {"sum_completeness": round(S, 1), "N_lower": nk, "rate_lower": nk / S, "rate_lower_ci": lo,
                       "N_upper": nu, "rate_upper": nu / S, "rate_upper_ci": hi}
    out["rates"] = rates
    c = rates["combined"]
    out["H1"] = "Supported" if c["rate_upper_ci"][1] < 5e-4 else "Refuted" if c["rate_lower_ci"][0] > 5e-4 else "Inconclusive"
    out["geometric_times_duty_if_polluted_25_50pct"] = [c["rate_lower"] / 0.5, c["rate_lower"] / 0.25]
    # secondary: thresholds, G and distance bins (lower rate)
    out["threshold_variants_flagged"] = {k_: int(e[k_].fillna(False).sum()) for k_ in ("short_2.5", "short_3.5", "long_3", "long_7")}
    e["dist_pc"] = 1000 / e.parallax
    e["dbin"] = pd.cut(e.dist_pc, [0, 100, 200, 500], labels=["<=100", "100-200", "200-500"])
    e["rec_known"] = e.source_id.isin(set(rec_known.source_id))
    out["by_distance"] = {str(b): {"stars": int(len(g)), "known_recovered": int(g.rec_known.sum()), "candidates": int((g.flag & ~g.known & ~g.gaia_variable).sum()),
                                   "sum_C_best": round(float(g.C_best.sum()), 1)} for b, g in e.groupby("dbin", observed=True)}
    out["by_gbin"] = {str(b): {"stars": int(len(g)), "known_recovered": int(g.rec_known.sum()), "candidates": int((g.flag & ~g.known & ~g.gaia_variable).sum()),
                               "sum_C_best": round(float(g.C_best.sum()), 1)} for b, g in e.groupby("gbin")}
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps({k_: out[k_] for k_ in out if k_ not in ("completeness_tables",)}, indent=1, default=float))


def test():
    rng = np.random.default_rng(1)
    t = np.sort(rng.uniform(58200, 60600, 600)); f = np.where(rng.random(600) < 0.5, "zg", "zr")
    m = 18 + rng.normal(0, 0.05, 600)
    r0 = rules(f, m, t)
    assert not r0["short"] and not r0["long"], r0
    m1 = m.copy(); dip = rng.choice(600, 30, replace=False); m1[dip] += 0.5          # 30 deep faint epochs
    assert rules(f, m1, t)["short"]
    m2 = m.copy(); m2[(t > 59000) & (t < 59120)] += 0.2                               # a 120-day 17% dimming
    assert rules(f, m2, t)["long"]
    f3, m3, e3, t3 = inject_one(f, m, np.full(600, 0.05), t, "oneoff", np.random.default_rng(3))
    assert len(m3) <= 600
    print("detect tests pass")


if __name__ == "__main__":
    {"detect": detect, "inject": inject, "occurrence": occurrence, "test": test}[sys.argv[1]]()
