"""D3: post-hoc checks after the independent review (review/review.md). Frozen models are re-scored, never refitted.

1. The frozen models' fitting curves (validation and training scores per iteration, n_iter_), against the constant
   base-rate predictor (iteration 0).
2. Host audit of the top 1% for the full and H2 models, with OpenAlex display names.
3. E@1% with the publisher-clustered bootstrap, excluding (a) the NIH / PubMed Central repository host I1299303238,
   (b) Hindawi (P4310319869), (c) both; and an iid-article bootstrap for contrast.
4. What the H2 top 1% rides on: shares with an institution prior rate, an author with a prior retraction, a reference
   to retracted work, against the cohort.
5. H3 addendum inputs: the sealed forward cohort as (wid, doi) and the works already retracted at sealing, each
   written to data/forecast/ (never published) with only their SHA-256 committed.

Writes results/tables/posthoc_review.json.
"""
import hashlib
import json
import pickle
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
PMC, HINDAWI = 1299303238, 4310319869


def name_of(hid):
    key = (Path.home() / ".config" / "openalex" / "api_key").read_text().strip()
    for pre, kind in (("P", "publishers"), ("I", "institutions")):
        try:
            u = f"https://api.openalex.org/{kind}/{pre}{hid}?select=display_name&api_key={key}"
            return json.load(urllib.request.urlopen(u, timeout=30))["display_name"]
        except Exception:
            continue
    return None


def e1(s, y, cl):
    e, _ = M.enrichment(s, y, 0.01)
    return {"E@1%": round(float(e), 3), "ci": M.boot(s, y, cl, 0.01), "n": int(len(s)), "retracted": int(y.sum())}


def iid_ci(s, y, B=1000):
    rng = np.random.default_rng(M.SEED)
    n1 = max(1, int(round(0.01 * len(s))))
    intop = np.zeros(len(s), bool); intop[np.argsort(-s, kind="stable")[:n1]] = True
    out = []
    for _ in range(B):
        w = rng.poisson(1.0, len(s))
        out.append(((w * y * intop).sum() / max((w * intop).sum(), 1)) / ((w * y).sum() / w.sum()))
    return [round(float(np.percentile(out, 2.5)), 3), round(float(np.percentile(out, 97.5)), 3)]


def main():
    hashes = json.load(open(T / "model_hashes.json"))
    for name, h in hashes["models"].items():
        assert M.sha(M.MD / name) == h["sha256"], name
    out = {"fit_curves": {}}
    bundles = {n: pickle.load(open(M.MD / n, "rb")) for n in hashes["models"]}
    for n, b in bundles.items():
        m = b["model"]
        if hasattr(m, "validation_score_"):
            out["fit_curves"][n] = {"n_iter": int(m.n_iter_), "validation_score": [round(float(v), 5) for v in m.validation_score_],
                                    "train_score": [round(float(v), 5) for v in m.train_score_]}
    test = M.load(M.TEST)
    y = (test.ret > 0).to_numpy().astype(float)
    cl = M.clusters_of(test)
    host = test.host.to_numpy().astype(np.int64)
    sc = {k: M.predict(bundles[k], test) for k in ("hgb_full.pkl", "hgb_no_A.pkl")}
    n1 = max(1, int(round(0.01 * len(y))))
    names = {}
    out["host_audit"], out["exclusions"], out["iid_contrast"] = {}, {}, {}
    for k, s in sc.items():
        top = np.zeros(len(s), bool); top[np.argsort(-s, kind="stable")[:n1]] = True
        g = pd.DataFrame({"h": host, "top": top, "y": y}).groupby("h").agg(n=("top", "size"), top=("top", "sum"), ret=("y", "sum"))
        g = g.sort_values("top", ascending=False).head(8)
        rows = {}
        for hid, r in g.iterrows():
            if hid not in names:
                names[hid] = "no host" if hid == 0 else name_of(int(hid))
            rows[str(int(hid))] = {"name": names[hid], "cohort_share": round(r.n / len(s), 4), "top1_share": round(r.top / n1, 4),
                                   "retraction_rate": round(r.ret / r.n, 5)}
        out["host_audit"][k] = rows
        res = {"all": e1(s, y, cl)}
        for tag, keep in (("without_pmc_host", host != PMC), ("without_hindawi", host != HINDAWI),
                          ("without_both", (host != PMC) & (host != HINDAWI))):
            res[tag] = e1(s[keep], y[keep], cl[keep])
        out["exclusions"][k] = res
        out["iid_contrast"][k] = iid_ci(s, y)
    s = sc["hgb_no_A.pkl"]
    top = np.zeros(len(s), bool); top[np.argsort(-s, kind="stable")[:n1]] = True
    comp = {}
    for col, label in (("inst_max_rate", "institution prior rate > 0"), ("auth_prior_ret_n", "author with a prior retraction"),
                       ("ref_retracted_share", "cites retracted work")):
        if col in test:
            v = test[col].to_numpy() > 0
            comp[label] = {"top1": round(float(v[top].mean()), 4), "cohort": round(float(v.mean()), 4)}
    out["h2_signal_composition"] = comp
    json.dump(out, open(T / "posthoc_review.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "fit_curves"}, indent=1, default=str))
    print({n: (c["n_iter"], c["validation_score"][:3], c["validation_score"][-1]) for n, c in out["fit_curves"].items()})


def h3_inputs():
    """Section 5 alone (run as `posthoc_review.py h3`): the sealed forward cohort as (wid, doi), by hash lookup on the
    2025-2026 rows of each cohort file, and the works already retracted at sealing."""
    import glob
    fw = pd.read_parquet(RUN / "data" / "forecast" / "forward_scores.parquet", columns=["wid"])
    want = pd.Index(np.unique(fw.wid.astype(np.int64).to_numpy()))
    rows = []
    for f in sorted(glob.glob(str(RUN / "data" / "cohort_raw" / "*.npz"))):
        z = np.load(f, allow_pickle=True)
        if "wid" not in z.files or len(z["wid"]) == 0:
            continue
        yr = z["year"]
        sel = (yr >= 2025)
        if not sel.any():
            continue
        w = z["wid"].astype(np.int64)
        m = sel & pd.Index(w).isin(want)
        if m.any():
            rows.append(pd.DataFrame({"wid": w[m], "doi": z["doi"][m]}))
    wd = pd.concat(rows).drop_duplicates("wid").sort_values("wid")
    wd["doi"] = wd.doi.astype(str).str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True).str.lower()
    p = RUN / "data" / "forecast" / "forward_wid_doi.csv"
    wd.to_csv(p, index=False)
    lab = pd.read_parquet(RUN / "data" / "labels.parquet")
    already = wd[wd.doi.isin(set(lab.doi.str.lower()))].wid.sort_values()
    q = RUN / "data" / "forecast" / "forward_retracted_at_seal_wids.csv"
    already.to_csv(q, index=False)
    out = json.load(open(T / "posthoc_review.json"))
    out["h3_inputs"] = {"forward_wid_doi_rows": int(len(wd)), "forward_works_in_seal": int(len(want)),
                        "forward_wid_doi_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                        "retracted_at_seal": int(len(already)), "retracted_at_seal_sha256": hashlib.sha256(q.read_bytes()).hexdigest()}
    json.dump(out, open(T / "posthoc_review.json", "w"), indent=1, default=str)
    print(out["h3_inputs"])


if __name__ == "__main__":
    h3_inputs() if sys.argv[1:] == ["h3"] else main()
