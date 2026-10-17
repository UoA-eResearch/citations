"""Difference-in-differences, as preregistered in plan.md (section 7).

  outcome     y = log(1 + violation nodes per 1,000 DOM elements), frozen rule subset (axe_run.js); snapshots with
              < 50 elements or an axe error are dropped and counted
  periods     pre = 2024-01, 2024-04, 2024-07, 2024-10; anticipation = 2025-01, 2025-04; transition = 2025-07 (the Act
              applied from 2025-06-28); post = 2025-10, 2026-01, 2026-04. Anticipation and transition quarters are
              excluded from H1-H3 and kept in the event study.
  H1          EU sites: y_it = site FE + period FE + b * InScope_i * Post_t; relative change = exp(b) - 1.
              Supported if exp(b) - 1 <= -15% and the 95% interval's upper end < 0; Refuted if the interval's lower end
              > -15% (a 15% reduction is ruled out); Inconclusive otherwise. Standard errors clustered by site.
              If the sector validation (plan 5) finds in-scope or out-of-scope precision < 0.80, a Refuted H1 is
              reported as Inconclusive (misclassification attenuates b toward zero).
  H2 placebo  the same in the non-EU placebo sites (.com.au, .co.nz, .ca): Supported (no effect) if the 95% interval
              of exp(b) - 1 lies within (-5%, +5%); Refuted if it lies wholly outside; Inconclusive otherwise.
  H3          (restated, plan 1.3) among EU in-scope sites, did those that newly installed an overlay script improve
              their static markup less than those that did not? y = site FE + period FE + c * NewOverlay_i * Post_t.
              Supported (substitution) if c's 95% interval lies above 0; Refuted if it lies below 0; else Inconclusive.
  secondary   S1 triple difference (EU vs placebo); S2 the UK (.co.uk) separately; S3 event study (InScope x quarter,
              EU, reference 2024-10); S4 overlay adoption: the same DiD as H1 with overlay presence (0/1) as the
              outcome, EU and placebo; S5 the lead's literal windows (pre 2024-01 + 2024-04, post 2026-01 + 2026-04);
              S6 per-rule descriptive changes (EU in-scope vs out-of-scope, mean nodes per 1,000 elements).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RUN = Path(__file__).resolve().parents[1]
PRE = ["202401", "202404", "202407", "202410"]
ANTIC = ["202501", "202504", "202507"]
POST = ["202510", "202601", "202604"]
REF = "202410"


def load():
    m = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "metrics.jsonl")])
    m["target"] = m.target.astype(str)
    fr = pd.read_csv(RUN / "data" / "frame" / "sample.csv")
    sec = pd.read_csv(RUN / "data" / "sector.csv")
    d = m.merge(fr[["domain", "group", "tld"]], on="domain").merge(sec[["domain", "status", "sector"]], on="domain")
    bad = d["error"].notna() if "error" in d else pd.Series(False, index=d.index)
    d["drop"] = bad | (d.elements.fillna(0) < 50)
    dropped = d.groupby("group")["drop"].sum().to_dict()
    d = d[~d["drop"]].copy()
    d["y"] = np.log1p(1000 * d.violation_nodes / d.elements)
    d = d[d.status.isin(["in_scope", "out_of_scope"])].copy()
    d["inscope"] = (d.status == "in_scope").astype(float)
    d["post"] = d.target.isin(POST).astype(float)
    d["overlay"] = d.overlay.astype(float)
    return d, dropped


def did(df, y="y", treat="inscope", pre=PRE, post=POST, log=True):
    x = df[df.target.isin(pre + post)].copy()
    x["treat_post"] = x[treat] * x.target.isin(post).astype(float)
    if x.treat_post.nunique() < 2:
        return None
    r = smf.ols(f"{y} ~ treat_post + C(domain) + C(target)", data=x).fit(cov_type="cluster", cov_kwds={"groups": x.domain})
    b, se = float(r.params["treat_post"]), float(r.bse["treat_post"])
    out = dict(b=b, se=se, ci_b=[b - 1.96 * se, b + 1.96 * se], n_sites=int(x.domain.nunique()), n_obs=int(len(x)),
               n_treated_sites=int(x[x[treat] == 1].domain.nunique()))
    if log:
        rel = lambda v: float(np.exp(v) - 1)
        out.update(rel=rel(b), ci=[rel(b - 1.96 * se), rel(b + 1.96 * se)])
    return out


def sector_precision():
    f = RUN / "results" / "tables" / "sector_validation.csv"
    if not f.exists():
        return None
    v = pd.read_csv(f)
    return {s: float(g.agree.mean()) for s, g in v.groupby("rule_status")}


def main():
    d, dropped = load()
    out = dict(n_snapshots=int(len(d)), dropped_snapshots=dropped,
               sites_by_group=d.groupby("group").domain.nunique().to_dict(),
               inscope_by_group=d[d.inscope == 1].groupby("group").domain.nunique().to_dict())
    eu, pl, uk = d[d.group == "eu"], d[d.group == "placebo"], d[d.group == "uk"]
    h1 = did(eu)
    h1["verdict"] = ("Supported" if h1["rel"] <= -0.15 and h1["ci"][1] < 0 else
                     "Refuted" if h1["ci"][0] > -0.15 else "Inconclusive")
    sp = sector_precision()
    out["sector_precision"] = sp
    if sp and min(sp.values()) < 0.80 and h1["verdict"] == "Refuted":
        h1["verdict"] = "Inconclusive (Refuted downgraded: sector precision < 0.80)"
    h2 = did(pl)
    lo, hi = h2["ci"]
    h2["verdict"] = "Supported" if (lo > -0.05 and hi < 0.05) else ("Refuted" if (hi < -0.05 or lo > 0.05) else "Inconclusive")
    out["H1_eu"], out["H2_placebo"] = h1, h2
    # H3: new overlay adopters among EU in-scope sites
    ins = eu[eu.inscope == 1]
    newov = ins.groupby("domain").apply(lambda g: float((g[g.target.isin(PRE)].overlay.max() == 0)
                                                        and (g[g.target.isin(POST)].overlay.max() == 1)))
    ins = ins.assign(new_overlay=ins.domain.map(newov))
    h3 = did(ins, treat="new_overlay")
    if h3:
        h3["n_new_adopters"] = int(newov.sum())
        h3["verdict"] = ("Supported" if h3["ci_b"][0] > 0 else "Refuted" if h3["ci_b"][1] < 0 else "Inconclusive")
    out["H3_overlay_substitution"] = h3 or dict(verdict="not estimable", n_new_adopters=int(newov.sum()))
    # S1 triple difference
    x = pd.concat([eu, pl]); x = x[x.target.isin(PRE + POST)].copy()
    x["eu"] = (x.group == "eu").astype(float); x["ddd"] = x.inscope * x.post * x.eu
    x["ip"] = x.inscope * x.post; x["ep"] = x.eu * x.post
    r = smf.ols("y ~ ddd + ip + ep + C(domain) + C(target)", data=x).fit(cov_type="cluster", cov_kwds={"groups": x.domain})
    b, se = float(r.params["ddd"]), float(r.bse["ddd"])
    out["S1_triple_difference"] = dict(b=b, se=se, rel=float(np.exp(b) - 1),
                                       ci=[float(np.exp(b - 1.96 * se) - 1), float(np.exp(b + 1.96 * se) - 1)])
    out["S2_uk"] = did(uk) if len(uk) else None
    # S3 event study
    ev = eu.copy()
    for t in PRE + ANTIC + POST:
        if t != REF:
            ev[f"e{t}"] = ev.inscope * (ev.target == t)
    terms = " + ".join(c for c in ev.columns if c.startswith("e2"))
    r = smf.ols(f"y ~ {terms} + C(domain) + C(target)", data=ev).fit(cov_type="cluster", cov_kwds={"groups": ev.domain})
    out["S3_event_study_eu"] = {c[1:]: dict(b=float(r.params[c]), se=float(r.bse[c])) for c in ev.columns if c.startswith("e2")}
    # S4 overlay adoption
    out["S4_overlay_adoption"] = dict(eu=did(eu, y="overlay", log=False), placebo=did(pl, y="overlay", log=False),
                                      share_overlay={g: {t: float(v) for t, v in gg.groupby("target").overlay.mean().items()}
                                                     for g, gg in d[d.inscope == 1].groupby("group")})
    # S5 the lead's literal windows
    out["S5_lead_windows"] = dict(eu=did(eu, pre=["202401", "202404"], post=["202601", "202604"]),
                                  placebo=did(pl, pre=["202401", "202404"], post=["202601", "202604"]))
    # S6 per-rule change, EU
    rules = sorted({k for br in d.by_rule.dropna() for k in br})
    rr = []
    for g, gg in eu[eu.target.isin(PRE + POST)].groupby(["inscope", "post"]):
        dens = {k: float((gg.by_rule.map(lambda b: (b or {}).get(k, 0)) * 1000 / gg.elements).mean()) for k in rules}
        rr.append(dict(inscope=g[0], post=g[1], **dens))
    pd.DataFrame(rr).to_csv(RUN / "results" / "tables" / "per_rule_eu.csv", index=False)
    (RUN / "results" / "tables").mkdir(parents=True, exist_ok=True)
    json.dump(out, open(RUN / "results" / "tables" / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("H1_eu", "H2_placebo", "H3_overlay_substitution", "S1_triple_difference")},
                     indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
