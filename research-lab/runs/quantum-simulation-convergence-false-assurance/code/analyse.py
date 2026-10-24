"""Analysis (plan section 3; D1). Written before any main-set approximate result was read.

H1  per method: share of apparently converged instances (|v_finest - v_second| <= 0.01) whose true error
    |v_finest - exact| > 0.03, with a bootstrap 95% interval (2,000 resamples of instances).
    Reading of the plan: a method with fewer than 20 apparently converged instances cannot decide anything.
    Supported if any deciding method has lower bound > 0.10; Refuted if both methods decide with upper bound < 0.10;
    Inconclusive otherwise.
H2  per method: k = 90th percentile of |error| / spread over a random half (seed 20261025) with spread > 0; coverage of
    |error| <= k * spread on the other half. Supported if both coverages lie in [0.85, 0.95]; Refuted if neither does.
Finest two settings: the two finest with status ok (D1.3); instances with fewer than two are excluded and counted.
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
T.mkdir(parents=True, exist_ok=True)
TOL, BAD, SEED, B = 0.01, 0.03, 20261025, 2000
FINE_FIRST = {"bp": False, "pp": True}           # bp: larger chi is finer; pp: smaller eps is finer


def load(name="main"):
    ex = json.loads((D / "results" / f"exact_{name}.json").read_text())
    I = {x["id"]: x for x in json.loads((D / "instances" / f"{name}.json").read_text())}
    rows = []
    for f in sorted(glob.glob(str(D / "results" / name / "*.json"))):
        rows += json.loads(Path(f).read_text())
    r = pd.DataFrame(rows)
    r["exact"] = r["id"].map(ex)
    out, excluded = [], {}
    for (m, i), g in r.groupby(["method", "id"]):
        ok = g[g["status"] == "ok"].sort_values("setting", ascending=FINE_FIRST[m])
        if len(ok) < 2:
            excluded[m] = excluded.get(m, 0) + 1
            continue
        f1, f2 = ok.iloc[-1], ok.iloc[-2]
        ins = I[i]
        out.append({"method": m, "id": i, "family": ins["family"], "n": ins["n"], "depth": ins["depth"],
                    "compact": ins["compact"], "loops": ins["loops"], "finest": f1["setting"], "second": f2["setting"],
                    "v1": f1["value"], "v2": f2["value"], "exact": f1["exact"], "secs": g["secs"].sum(),
                    "diag": f1["diag"]})
    d = pd.DataFrame(out)
    d["spread"] = (d["v1"] - d["v2"]).abs()
    d["err"] = (d["v1"] - d["exact"]).abs()
    d["conv"] = d["spread"] <= TOL
    d["fa"] = d["conv"] & (d["err"] > BAD)
    return d, excluded, r, I


def share_ci(g, rng):
    """Share of false assurance among apparently converged, with an instance bootstrap."""
    conv, fa = g["conv"].to_numpy(), g["fa"].to_numpy()
    if conv.sum() == 0:
        return {"n": int(len(g)), "n_conv": 0, "n_fa": 0, "share": None, "ci": [None, None]}
    bs = []
    for _ in range(B):
        k = rng.integers(len(g), size=len(g))
        c = conv[k].sum()
        if c:
            bs.append(fa[k].sum() / c)
    return {"n": int(len(g)), "n_conv": int(conv.sum()), "n_fa": int(fa.sum()), "share": float(fa.sum() / conv.sum()),
            "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}


def h2(g, seed=SEED):
    rng = np.random.default_rng(seed)
    ids = sorted(g["id"])
    fit_ids = set(rng.choice(ids, len(ids) // 2, replace=False))
    fit, test = g[g["id"].isin(fit_ids)], g[~g["id"].isin(fit_ids)]
    f = fit[fit["spread"] > 0]
    k = float(np.percentile(f["err"] / f["spread"], 90))
    cov = float((test["err"] <= k * test["spread"]).mean())
    return {"k": k, "fit_n": int(len(fit)), "test_n": int(len(test)), "coverage": cov,
            "within": bool(0.85 <= cov <= 0.95),
            "coverage_by_family": {fam: float((t["err"] <= k * t["spread"]).mean()) for fam, t in test.groupby("family")}}


def main(name="main"):
    d, excluded, raw, I = load(name)
    rng = np.random.default_rng(SEED)
    res = {"excluded_fewer_than_two_settings": excluded, "n_instances": len(I), "methods": {}}
    for m, g in d.groupby("method"):
        s = share_ci(g, rng)
        s["decides"] = s["n_conv"] >= 20
        s["apparent_convergence_rate"] = float(g["conv"].mean())
        s["median_err"] = float(g["err"].median())
        s["median_err_converged"] = float(g.loc[g["conv"], "err"].median()) if g["conv"].any() else None
        s["finest_pair"] = {f"{a}->{b}": int(c) for (a, b), c in g.groupby(["second", "finest"]).size().items()}
        s["h2"] = h2(g)
        s["by_family"] = {k: share_ci(x, rng) for k, x in g.groupby("family")}
        s["by_n"] = {str(k): share_ci(x, rng) for k, x in g.groupby("n")}
        s["by_depth_family"] = {f"{a}{b}": share_ci(x, rng) for (a, b), x in g.groupby(["family", "depth"])}
        s["by_loops"] = {str(k): share_ci(x, rng) for k, x in g.groupby("loops")}
        s["by_compact"] = {str(k): share_ci(x, rng) for k, x in g.groupby("compact")}
        res["methods"][m] = s
    M = res["methods"]
    deciding = {m: s for m, s in M.items() if s["decides"]}
    if any(s["ci"][0] > 0.10 for s in deciding.values()):
        res["H1"] = "Supported"
    elif len(deciding) == 2 and all(s["ci"][1] < 0.10 for s in deciding.values()):
        res["H1"] = "Refuted"
    else:
        res["H1"] = "Inconclusive"
    w = [M[m]["h2"]["within"] for m in ("bp", "pp")]
    res["H2"] = "Supported" if all(w) else "Refuted" if not any(w) else "Inconclusive"
    # exploratory (labelled post hoc in the report): threshold grid and error-diagnostic association
    grid = []
    for m, g in d.groupby("method"):
        for tol in (0.005, 0.01, 0.02):
            for bad in (0.02, 0.03, 0.05):
                c = g["spread"] <= tol
                grid.append({"method": m, "tol": tol, "bad": bad, "n_conv": int(c.sum()),
                             "share": float((c & (g["err"] > bad)).sum() / c.sum()) if c.sum() else None})
    res["exploratory_threshold_grid"] = grid
    diag = {}
    for m, g in d.groupby("method"):
        key = "max_gate_err" if m == "bp" else "final_terms"
        x = g["diag"].map(lambda v: v.get(key) if isinstance(v, dict) else None).astype(float)
        diag[m] = {"diagnostic": key, "spearman_with_err": float(pd.Series(x.to_numpy()).corr(g["err"].reset_index(drop=True), method="spearman")),
                   "spearman_spread_err": float(g["spread"].corr(g["err"], method="spearman"))}
    res["exploratory_diagnostics"] = diag
    rt = raw[raw["status"] == "ok"].groupby(["method", "setting"])["secs"].agg(["median", "max"])
    res["runtime"] = {f"{a}:{b}": {"median_s": float(r["median"]), "max_s": float(r["max"])} for (a, b), r in rt.iterrows()}
    res["status_counts"] = {f"{a}:{b}": int(c) for (a, b), c in raw.groupby(["method", "status"]).size().items()}
    if name != "main":                           # smoke test on other sets: nothing written
        return res
    (T / "primary.json").write_text(json.dumps(res, indent=1))
    d.drop(columns=["diag"]).to_csv(T / "instances.csv", index=False)
    for m, s in M.items():
        print(m, {k: s[k] for k in ("n", "n_conv", "n_fa", "share", "ci", "apparent_convergence_rate", "median_err")},
              "H2", {k: s["h2"][k] for k in ("k", "coverage", "within")})
    print("H1", res["H1"], "H2", res["H2"], "excluded", excluded)


if __name__ == "__main__":
    main()
