"""Primary and secondary analyses, as preregistered in plan.md. Reads data/aligned/ (pipeline.py) and the
alignment-validation adjudication (results/tables/alignment_validation.csv).

  population  pairs whose preprint full text is version 1 (Europe PMC's article-version, or the version a DOI encodes);
              all pairs, including unknown versions, are a sensitivity.
  primary     Among aligned statistic pairs whose significance at 0.05 is determined in both versions and differs
              (crossing_up: non-significant in the preprint, significant in the published version; crossing_down:
              the reverse), the share crossing up. Null 0.5; the lead's claim >= 0.67 (a 2:1 ratchet).
              Interval: 2,000 bootstrap resamples of PAPERS (pairs of versions), each keeping all its statistics.
              Supported if the point estimate >= 0.67 and the interval's lower end > 0.50; Refuted if the interval's
              upper end < 0.67; Inconclusive otherwise.
  abort rule  If hand-checked alignment precision among crossings (plan section 6) is < 0.90, the primary test is
              not run on all crossings; it is reported for exact tuple matches only, labelled.
  secondary   S1 dropped vs added: share significant among preprint statistics with no counterpart (dropped) vs
              among published statistics with no counterpart (added).
              S2 statcheck-style consistency: for tuples, recompute p from the test statistic and df; an
              inconsistency is a reported p outside the range implied by the statistic's rounding; a decision
              inconsistency is one that flips significance. Repair rate = share of preprint inconsistencies whose
              aligned published tuple is consistent.
              S3 the primary estimate restricted to exact tuple matches, and by server (bioRxiv, medRxiv, other).
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

RUN = Path(__file__).resolve().parents[1]
AL, TAB = RUN / "data" / "aligned", RUN / "results" / "tables"
NBOOT, SEED = 2000, 20261017


def load():
    rows = [json.loads(l) for l in gzip.open(AL / "statistics.jsonl.gz", "rt")]
    pairs = pd.DataFrame([json.loads(l) for l in open(AL / "pairs.jsonl")])
    return rows, pairs


def crossings(rows, how=None):
    c = [r for r in rows if r["status"] == "aligned" and r["cls"] in ("crossing_up", "crossing_down")
         and (how is None or r["how"] == how)]
    return pd.DataFrame(dict(pair=[r["pair"] for r in c], up=[r["cls"] == "crossing_up" for r in c]))


def boot_share(df, nboot=NBOOT, seed=SEED):
    if df.empty:
        return None, None, None
    g = df.groupby("pair").up.agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(nboot, len(g)))
    vals = s[idx].sum(1) / n[idx].sum(1)
    return float(s.sum() / n.sum()), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def verdict(est, lo, hi):
    if est is None:
        return "not estimable"
    if est >= 0.67 and lo > 0.50:
        return "Supported"
    return "Refuted" if hi < 0.67 else "Inconclusive"


def recompute_p(test, df, stat):
    try:
        if test == "t":
            return float(2 * st.t.sf(abs(stat), float(df)))
        if test == "f":
            d1, d2 = (float(x) for x in df.split(","))
            return float(st.f.sf(stat, d1, d2))
        if test == "r":
            d = float(df); t = stat * np.sqrt(d / max(1e-12, 1 - stat ** 2))
            return float(2 * st.t.sf(abs(t), d))
        if test in ("χ2", "chi2", "chi-square", "chi-squared", "chisquare"):
            return float(st.chi2.sf(stat, float(df)))
        if test == "z":
            return float(2 * st.norm.sf(abs(stat)))
    except Exception:
        return None
    return None


def consistent(x):
    """Is the reported p consistent with the reported statistic, allowing for the statistic's rounding?"""
    if x.get("kind") != "tuple" or x.get("stat") is None:
        return None
    dec = len(str(x["stat"]).split(".")[1]) if "." in str(x["stat"]) else 0
    h = 0.5 * 10 ** (-dec)
    ps = [recompute_p(x["test"], x["df"], v) for v in (abs(x["stat"]) - h, abs(x["stat"]) + h)]
    if any(p is None for p in ps):
        return None
    lo, hi = min(ps), max(ps)
    p, c = x["p"], x["cmp"]
    if c == "=":
        return lo - 0.005 <= p <= hi + 0.005 if p >= 0.01 else lo - 0.0005 <= p <= hi + 0.0005
    if c in ("<", "<="):
        return lo <= p
    if c in (">", ">="):
        return hi >= p
    return None


def main():
    rows, pairs = load()
    out = dict(n_pairs=int(len(pairs)), n_pairs_with_stats=int(sum(1 for i in pairs["info"] if i and i.get("n_pre", 0) + i.get("n_pub", 0) > 0)),
               n_statistics=len(rows),
               status_counts=pd.Series([r["status"] for r in rows]).value_counts().to_dict(),
               class_counts=pd.Series([r.get("cls") for r in rows if r["status"] == "aligned"]).value_counts().to_dict())
    val = TAB / "alignment_validation.csv"
    precision = None
    if val.exists():
        v = pd.read_csv(val)
        cv = v[v.stratum == "crossing"]
        precision = float(cv.correct.mean()) if len(cv) else None
        out["alignment_validation"] = dict(precision_crossings=precision, n_crossings_checked=int(len(cv)),
                                           precision_other=float(v[v.stratum != "crossing"].correct.mean()) if (v.stratum != "crossing").any() else None)
    # primary population: pairs whose preprint full text is version 1 (plan section 1.2); all pairs as a sensitivity
    v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
    out["n_pairs_v1"] = int(len(v1))
    rows_all = rows
    rows = [r for r in rows_all if r["pair"] in v1]
    allc = crossings(rows)
    exact = crossings(rows, "exact")
    av = boot_share(crossings(rows_all))
    out["sensitivity_all_versions"] = dict(n_crossings=int(len(crossings(rows_all))), share_up=av[0], ci=[av[1], av[2]],
                                           verdict=verdict(*av))
    est = boot_share(allc)
    out["primary_all_crossings"] = dict(n_crossings=int(len(allc)), n_papers=int(allc.pair.nunique()) if len(allc) else 0,
                                        share_up=est[0], ci=[est[1], est[2]], verdict=verdict(*est))
    ex = boot_share(exact)
    out["exact_tuples_only"] = dict(n_crossings=int(len(exact)), share_up=ex[0], ci=[ex[1], ex[2]], verdict=verdict(*ex))
    out["primary_used"] = ("all_crossings" if precision is None or precision >= 0.90 else "exact_tuples_only (abort rule)")
    dropped = [r["pre"]["sig"] for r in rows if r["status"] == "dropped" and r["pre"]["sig"] is not None]
    added = [r["pub"]["sig"] for r in rows if r["status"] == "added" and r["pub"]["sig"] is not None]
    out["S1_dropped_vs_added"] = dict(n_dropped=len(dropped), share_sig_dropped=float(np.mean(dropped)) if dropped else None,
                                      n_added=len(added), share_sig_added=float(np.mean(added)) if added else None)
    tup = [r for r in rows if r["status"] == "aligned" and r["pre"]["kind"] == "tuple" and r["pub"]["kind"] == "tuple"]
    inc = [(consistent(r["pre"]), consistent(r["pub"])) for r in tup]
    pre_bad = [b for a, b in inc if a is False]
    out["S2_statcheck"] = dict(n_aligned_tuples=len(tup), preprint_inconsistent=int(sum(a is False for a, _ in inc)),
                               published_inconsistent=int(sum(b is False for _, b in inc)),
                               repair_rate=float(np.mean([b is True for b in pre_bad])) if pre_bad else None)
    srv = pairs.set_index("preprint_doi").server.to_dict()
    if len(allc):
        allc["server"] = allc.pair.map(lambda d: {"bioRxiv": "bioRxiv", "medRxiv": "medRxiv"}.get(srv.get(d), "other"))
        out["S3_by_server"] = {s: dict(zip(("share_up", "lo", "hi"), boot_share(g)), n=int(len(g))) for s, g in allc.groupby("server")}
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
