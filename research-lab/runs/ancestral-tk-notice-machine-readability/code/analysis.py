"""H1, H2 and descriptives (plan section 4). Reads data/census.jsonl, data/uri_status.json, data/views.jsonl.
Writes results/tables/primary.json and the per-platform and per-view tables."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def exact(k, n):
    if n == 0:
        return [None, None]
    return [0.0 if k == 0 else float(st.beta.ppf(0.025, k, n - k + 1)), 1.0 if k == n else float(st.beta.ppf(0.975, k + 1, n - k))]


def main():
    c = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "census.jsonl")])
    # free-text (name-only) hits were adjudicated in full (precision.py); drop those judged not genuine
    pr = pd.read_csv(TAB / "precision.csv")
    bad = set(zip(pr[pr.genuine == 0].platform, pr[pr.genuine == 0].record.astype(str)))
    out_ft = dict(name_only=int(len(pr)), genuine=int(pr.genuine.sum()))
    c = c[[(p, str(i)) not in bad for p, i in zip(c.platform, c.id)]].copy()
    us = json.load(open(RUN / "data" / "uri_status.json")) if (RUN / "data" / "uri_status.json").exists() else {}
    live_project = lambda ps: any(us.get(f"https://localcontextshub.org/projects/{p}/") == 200 for p in ps)
    c["has_label"] = c.uri_labels.map(bool) | c.name_labels.map(bool)
    c["has_notice"] = c.uri_notices.map(bool) | c.name_notices.map(bool)
    c["label_hub"] = c.has_label & c.hub_projects.map(live_project)
    c["neotoma"] = c.doi.fillna("").str.lower().str.startswith("10.21233/")
    # deduplicate across platforms by DOI where present (a DataCite DOI also held by Zenodo/Dryad counts once)
    c["key"] = np.where(c.doi.fillna("") != "", c.doi.fillna("").str.lower(), c.platform + ":" + c.id.astype(str))
    u = c.sort_values("platform").drop_duplicates("key")
    out = dict(n_records=int(len(u)), by_platform=c.groupby("platform").size().to_dict(), free_text=out_ft)
    for name, g in (("all", u), ("without_neotoma", u[~u.neotoma])):
        k, n = int(g.label_hub.sum()), len(g)
        out[f"H1_{name}"] = dict(n=n, label_hub=k, share=k / n if n else None, ci=exact(k, n), labels_any=int(g.has_label.sum()),
                                 notices=int(g.has_notice.sum()), hub_any=int(g.hub_projects.map(bool).sum()))
    h = out["H1_all"]
    out["H1_verdict"] = "Supported" if h["ci"][1] is not None and h["ci"][1] < 0.001 else "Refuted" if h["ci"][0] is not None and h["ci"][0] >= 0.001 else "Inconclusive"
    top = u.groupby(u.publisher.fillna("?")).size().sort_values(ascending=False)
    out["concentration"] = dict(top_publisher=top.index[0] if len(top) else None, top_share=float(top.iloc[0] / top.sum()) if len(top) else None,
                                hhi=float(((top / top.sum()) ** 2).sum()) if len(top) else None)
    u.groupby(["platform", "has_label", "has_notice"]).size().reset_index(name="n").to_csv(TAB / "census_by_platform.csv", index=False)
    vf = RUN / "data" / "views.jsonl"
    if vf.exists():
        v = pd.DataFrame([json.loads(l) for l in open(vf)])
        # D4: DOIs whose element was judged not genuine (precision.csv) are not element-bearing
        bad_doi = {str(r).lower() for p_, r in bad}
        out["H2_excluded_not_genuine"] = int(v[v.doi.str.lower().isin(bad_doi)].doi.nunique())
        v = v[~v.doi.str.lower().isin(bad_doi)].copy()
        a = v[v.result != "unavailable"].copy()
        a["drop"] = (a.result == "drop").astype(float)
        g = a.groupby("doi")["drop"].agg(["sum", "count"])
        s, nn = g["sum"].to_numpy(), g["count"].to_numpy()
        idx = np.random.default_rng(20261021).integers(0, len(g), size=(2000, len(g)))
        bs = s[idx].sum(1) / nn[idx].sum(1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        share = float(s.sum() / nn.sum())
        out["H2"] = dict(n_dois=int(len(g)), n_pairs=int(nn.sum()), drop_share=share, ci=[float(lo), float(hi)],
                         verdict="Supported" if lo >= 0.40 else "Refuted" if hi < 0.40 else "Inconclusive",
                         warnings=int(v.warning.sum()))
        m = v.pivot_table(index="view", columns="result", values="doi", aggfunc="count", fill_value=0)
        m.to_csv(TAB / "view_matrix.csv")
        # plan section 4: the preserve/degrade/drop matrix by stratum (Neotoma vs other publishers), and H2 per stratum
        v["stratum"] = np.where(v.doi.str.lower().str.startswith("10.21233/"), "neotoma", "other")
        v.pivot_table(index=["stratum", "view"], columns="result", values="doi", aggfunc="count", fill_value=0).to_csv(TAB / "view_matrix_by_stratum.csv")
        a["stratum"] = np.where(a.doi.str.lower().str.startswith("10.21233/"), "neotoma", "other")
        out["H2_by_stratum"] = {}
        for stv, gg in a.groupby("stratum"):
            g2 = gg.groupby("doi")["drop"].agg(["sum", "count"])
            s2, n2 = g2["sum"].to_numpy(), g2["count"].to_numpy()
            ix = np.random.default_rng(20261021).integers(0, len(g2), size=(2000, len(g2)))
            b2 = s2[ix].sum(1) / n2[ix].sum(1)
            out["H2_by_stratum"][stv] = dict(n_dois=int(len(g2)), n_pairs=int(n2.sum()), drop_share=float(s2.sum() / n2.sum()),
                                             ci=[float(x) for x in np.percentile(b2, [2.5, 97.5])],
                                             results=gg.result.value_counts().to_dict())
        out["per_view"] = {vw: dict(drop=int((a[a.view == vw].result == "drop").sum()), n=int((a.view == vw).sum()),
                                    ci=exact(int((a[a.view == vw].result == "drop").sum()), int((a.view == vw).sum()))) for vw in sorted(a.view.unique())}
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in out if k.startswith("H")}, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
