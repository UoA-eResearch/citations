"""v2 (confirmation pass): same recomputation run on the D5 data files (census.jsonl, views.jsonl after rescore.py). Writes recomputed_v2.json."""
"""Reviewer's recomputation of H1 and H2 from data/census.jsonl, data/uri_status.json, data/views.jsonl and
results/tables/precision.csv, with sensitivity analyses: D4 on/off, unavailable-as-drop, leave-one-view-out, the
'k dropping views of 9' arithmetic, and per-view / per-stratum intervals. Writes recomputed.json."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as st

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
TAB = RUN / "results" / "tables"

def exact(k, n):
    lo = 0.0 if k == 0 else float(st.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(st.beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]

def wilson(k, n, z=1.959964):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]

def cluster_boot(df, seed=20261021, B=2000):
    g = df.groupby("doi")["drop"].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), size=(B, len(g)))
    bs = s[idx].sum(1) / n[idx].sum(1)
    return dict(n_dois=int(len(g)), n_pairs=int(n.sum()), n_drop=int(s.sum()), share=float(s.sum() / n.sum()),
                ci=[float(x) for x in np.percentile(bs, [2.5, 97.5])])

def verdict_h2(lo, hi):
    return "Supported" if lo >= 0.40 else "Refuted" if hi < 0.40 else "Inconclusive"

out = {}
c = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "census.jsonl")])
pr = pd.read_csv(TAB / "precision.csv")
bad = set(zip(pr[pr.genuine == 0].platform, pr[pr.genuine == 0].record.astype(str)))
c_all = c.copy()
c = c[[(p, str(i)) not in bad for p, i in zip(c.platform, c.id)]].copy()
us = json.load(open(RUN / "data" / "uri_status.json"))
live = lambda ps: any(us.get(f"https://localcontextshub.org/projects/{p}/") == 200 for p in ps)
for d in (c, c_all):
    d["has_label"] = d.uri_labels.map(bool) | d.name_labels.map(bool)
    d["has_notice"] = d.uri_notices.map(bool) | d.name_notices.map(bool)
    d["label_hub"] = d.has_label & d.hub_projects.map(live)
    d["label_uri"] = d.uri_labels.map(bool)
    d["neotoma"] = d.doi.fillna("").str.lower().str.startswith("10.21233/")
    d["key"] = np.where(d.doi.fillna("") != "", d.doi.fillna("").str.lower(), d.platform + ":" + d.id.astype(str))
u = c.sort_values("platform").drop_duplicates("key")
u_all = c_all.sort_values("platform").drop_duplicates("key")
out["H1"] = {}
for name, g in (("all", u), ("without_neotoma", u[~u.neotoma]), ("all_before_precision_exclusion", u_all),
                ("without_neotoma_before_precision_exclusion", u_all[~u_all.neotoma])):
    k, n = int(g.label_hub.sum()), len(g)
    ci = exact(k, n)
    out["H1"][name] = dict(n=n, label_with_live_hub=k, share=k / n, exact_ci=ci, wilson_ci=wilson(k, n),
                           verdict_by_prereg_rule=("Supported" if ci[1] < 0.001 else "Refuted" if ci[0] >= 0.001 else "Inconclusive"),
                           labels_by_name_or_uri=int(g.has_label.sum()), label_uri_only=int(g.label_uri.sum()),
                           notices=int(g.has_notice.sum()), hub_project_any=int(g.hub_projects.map(bool).sum()),
                           hub_project_live=int(g.hub_projects.map(live).sum()))
# the H1 numerator rule: Label (by name or URI) AND live Hub project. Which records have a live Hub project at all?
out["H1"]["records_with_live_hub_project"] = u[u.hub_projects.map(live)][["platform", "id", "doi", "publisher", "name_labels", "uri_notices", "name_notices", "hub_projects"]].to_dict("records")
out["H1"]["per_platform_wilson"] = {}
for p, g in u.groupby("platform"):
    k, n = int(g.label_hub.sum()), len(g)
    out["H1"]["per_platform_wilson"][p] = dict(n=n, k=k, wilson_ci=wilson(k, n))
# concentration
top = u.groupby(u.publisher.fillna("?")).size().sort_values(ascending=False)
out["concentration"] = dict(top_publisher=top.index[0], top_share=float(top.iloc[0] / top.sum()), hhi=float(((top / top.sum()) ** 2).sum()),
                            n_publishers=int(len(top)), by_year_neotoma=u[u.neotoma].year.astype(str).value_counts().to_dict(),
                            by_year_other=u[~u.neotoma].year.astype(str).value_counts().to_dict())

# ---------------- H2 ----------------
v = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "views.jsonl")])
bad_doi = {str(r).lower() for p_, r in bad}
v["excluded_D4"] = v.doi.str.lower().isin(bad_doi)
v["stratum"] = np.where(v.doi.str.lower().str.startswith("10.21233/"), "neotoma", "other")
v["drop"] = (v.result == "drop").astype(float)
out["H2"] = {}
def h2(df, label, unavailable_as=None):
    d = df.copy()
    if unavailable_as is None:
        d = d[d.result != "unavailable"]
    else:
        d.loc[d.result == "unavailable", "drop"] = 1.0 if unavailable_as == "drop" else 0.0
    r = cluster_boot(d); r["verdict"] = verdict_h2(*r["ci"]); r["label"] = label
    return r
base = v[~v.excluded_D4]
out["H2"]["as_reported_D4"] = h2(base, "D4 applied, unavailable excluded")
out["H2"]["without_D4"] = h2(v, "no D4 exclusion (2,000 DOIs)")
out["H2"]["unavailable_as_drop"] = h2(base, "unavailable counted as drop", unavailable_as="drop")
out["H2"]["unavailable_as_kept"] = h2(base, "unavailable counted as not-drop", unavailable_as="kept")
out["H2"]["by_stratum"] = {s: h2(base[base.stratum == s], s) for s in ("neotoma", "other")}
out["H2"]["other_without_D4"] = h2(v[v.stratum == "other"], "other publishers, no D4 exclusion")
# leave-one-view-out and drop-the-citation-formats
views = sorted(v.view.unique())
out["H2"]["leave_one_view_out"] = {vw: h2(base[base.view != vw], f"without {vw}") for vw in views}
out["H2"]["without_openaire_and_citation_text"] = h2(base[~base.view.isin(["openaire", "citation_text"])], "without OpenAIRE and formatted citation")
out["H2"]["only_rights_capable_views"] = h2(base[base.view.isin(["datacite_xml", "oai_datacite", "oai_dc", "crosscite_json", "schemaorg_jsonld", "openaire"])], "views with any rights/licence field")
out["H2"]["only_cn_views"] = h2(base[base.view.isin(["datacite_xml", "schemaorg_jsonld", "crosscite_json", "csl_json", "bibtex", "citation_text"])], "the six doi.org content-negotiation formats")
# 'k of 9' arithmetic for Neotoma
neo = base[(base.stratum == "neotoma") & (base.result != "unavailable")]
out["H2"]["neotoma_arithmetic"] = dict(views_dropping=sorted(neo[neo.result == "drop"].view.unique().tolist()),
                                       drop_pairs=int(neo["drop"].sum()), pairs=int(len(neo)),
                                       note="4 of 9 views drop for every Neotoma record; 203 OpenAIRE views unavailable -> (3*1971+1768)/(8*1971+1768)")
# per view exact intervals and by stratum
out["H2"]["per_view"] = {}
for vw, g in base[base.result != "unavailable"].groupby("view"):
    k, n = int((g.result == "drop").sum()), len(g)
    out["H2"]["per_view"][vw] = dict(drop=k, n=n, share=k / n, exact_ci=exact(k, n), results=g.result.value_counts().to_dict())
out["H2"]["matrix_by_stratum"] = {f"{s}:{vw}": g.result.value_counts().to_dict() for (s, vw), g in base.groupby(["stratum", "view"])}
out["H2b_warnings"] = int(base.warning.sum())
out["H2_counts"] = dict(rows=int(len(base)), unavailable=int((base.result == "unavailable").sum()), returned=int((base.result != "unavailable").sum()))
# between-record variance: how many distinct per-record patterns?
pat = base.pivot_table(index="doi", columns="view", values="result", aggfunc="first").astype(str).agg("|".join, axis=1)
out["H2"]["distinct_record_patterns"] = dict(n_patterns=int(pat.nunique()), top=pat.value_counts().head(5).to_dict())

json.dump(out, open(HERE / "recomputed_v2.json", "w"), indent=1, default=str)
# concise print
print("H1", {k: (d["label_with_live_hub"], d["n"], [round(x * 100, 4) for x in d["exact_ci"]], d["verdict_by_prereg_rule"]) for k, d in out["H1"].items() if isinstance(d, dict) and "n" in d})
for k in ("as_reported_D4", "without_D4", "unavailable_as_drop", "unavailable_as_kept", "without_openaire_and_citation_text", "only_rights_capable_views", "only_cn_views"):
    r = out["H2"][k]; print(f"H2 {k:40s} {r['n_drop']}/{r['n_pairs']} = {r['share']:.4f}  CI {r['ci'][0]:.4f}-{r['ci'][1]:.4f}  {r['verdict']}")
for vw, r in out["H2"]["leave_one_view_out"].items():
    print(f"H2 without {vw:18s} {r['n_drop']}/{r['n_pairs']} = {r['share']:.4f}  CI {r['ci'][0]:.4f}-{r['ci'][1]:.4f}  {r['verdict']}")
for s, r in out["H2"]["by_stratum"].items():
    print(f"H2 stratum {s:10s} {r['n_drop']}/{r['n_pairs']} = {r['share']:.4f}  CI {r['ci'][0]:.4f}-{r['ci'][1]:.4f}  {r['verdict']}")
print("other w/o D4", out["H2"]["other_without_D4"])
print("neotoma arithmetic", out["H2"]["neotoma_arithmetic"])
print("patterns", out["H2"]["distinct_record_patterns"])
print("warnings", out["H2b_warnings"], out["H2_counts"])
print("live hub records:", len(out["H1"]["records_with_live_hub_project"]))
print("concentration", {k: out["concentration"][k] for k in ("top_publisher", "top_share", "hhi", "n_publishers")})
