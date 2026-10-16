"""Omission rates, contrasts and decision rules, as preregistered in plan.md. Reads the generations for one set
(main, or pilot for checking) and the frozen scorer (score.py).

  unit          one response = (record, condition, framing, model)
  omission      1 - mentions(response, condition)
  H1            pooled omission over the five Local Contexts conditions (LC_CB, LC_NC, LC_BC, LC_TK, LC_CO), all
                models and framings, is >= 70%. Supported if the record-cluster bootstrap 95% interval's lower end is
                >= 0.70; Refuted if its upper end is < 0.70; Inconclusive otherwise.
  H2            pooled LC omission minus pooled conventional omission (CV_NC, CV_DUA, CV_CONTACT) is >= 25 points.
                Supported if the interval's lower end is >= 0.25; Refuted if its upper end is < 0.25.
  H3            agent framing: the share of (record, model, LC condition) whose stated verdict (commercial_use_allowed,
                permission_or_contact_required) differs from the same record and model with NONE is <= 20%.
                Supported if the interval's upper end is <= 0.20; Refuted if its lower end is > 0.20.
  intervals     2,000 bootstrap resamples of records (each record keeps all its conditions, framings and models).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GEN, TAB = RUN / "data" / "generations", RUN / "results" / "tables"
MODELS = ["qwen3-32b", "olmo2-13b", "mistral-small-24b"]
NBOOT, SEED = 2000, 20261017


def load(which):
    rows = []
    for m in MODELS:
        f = GEN / f"{m}_{which}.jsonl"
        if f.exists():
            rows += [json.loads(l) for l in open(f)]
    d = pd.DataFrame(rows)
    d["ok"] = d.get("error").isna() if "error" in d else True
    return d


def score_frame(d):
    d = d[d.ok].copy()
    d["mention"] = [S.mentions(t, c) if c in S.PATTERNS else np.nan for t, c in zip(d.text, d.condition)]
    d["named_lc"] = [S.named_lc(t) for t in d.text]
    d["mention_name"] = [S.mentions_by_name(t, c) if c in S.NAMES else np.nan for t, c in zip(d.text, d.condition)]
    d["omit"] = 1 - d.mention
    return d


def fp_rates(d):
    """Each pattern's hit rate on the NONE responses (its false-positive rate)."""
    n = d[d.condition == "NONE"]
    return {c: float(np.mean([S.mentions(t, c) for t in n.text])) for c in S.PATTERNS}


def boot(d, stat, nboot=NBOOT, seed=SEED):
    recs = d.doi.unique()
    groups = {k: g for k, g in d.groupby("doi")}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(nboot):
        b = pd.concat([groups[k] for k in rng.choice(recs, len(recs))], ignore_index=True)
        vals.append(stat(b))
    return float(stat(d)), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def lc_omit(d):
    return d[d.condition.isin(S.LC_CONDITIONS)].omit.mean()


def cv_omit(d):
    return d[d.condition.isin(S.CV_CONDITIONS)].omit.mean()


def verdict_change(d):
    a = d[d.framing == "agent"].copy()
    a["fields"] = [S.agent_fields(t) for t in a.text]
    base = a[a.condition == "NONE"].set_index(["doi", "model"]).fields
    lc = a[a.condition.isin(S.LC_CONDITIONS)].copy()
    lc["base"] = [base.get((r.doi, r.model)) for r in lc.itertuples()]
    v = lc[lc.fields.notna() & lc.base.notna()]
    return v, int(len(lc) - len(v))


def h3_stat(d):
    v, _ = verdict_change(d)
    return float(np.mean([f != b for f, b in zip(v.fields, v.base)])) if len(v) else np.nan


def decide(est, lo, hi, line, direction):
    if direction == "ge":
        return "Supported" if lo >= line else ("Refuted" if hi < line else "Inconclusive")
    return "Supported" if hi <= line else ("Refuted" if lo > line else "Inconclusive")


def main(which="main"):
    d = score_frame(load(which))
    out = dict(set=which, n_responses=int(len(d)), n_records=int(d.doi.nunique()), fp_rates=fp_rates(d))
    h1 = boot(d, lc_omit)
    h2 = boot(d, lambda b: lc_omit(b) - cv_omit(b))
    h3 = boot(d, h3_stat)
    _, unparsed = verdict_change(d)
    out["H1"] = dict(lc_omission=h1[0], ci=h1[1:], verdict=decide(*h1, 0.70, "ge"))
    out["H2"] = dict(lc_minus_cv=h2[0], ci=h2[1:], cv_omission=float(cv_omit(d)), verdict=decide(*h2, 0.25, "ge"))
    out["H3"] = dict(verdict_change_rate=h3[0], ci=h3[1:], unparsed_agent_pairs=unparsed, verdict=decide(*h3, 0.20, "le"))
    tab = d[d.condition != "NONE"].groupby(["condition", "model", "framing"]).omit.mean().unstack("framing").round(3)
    out["omission_by_condition_model_framing"] = {f"{c}|{m}": r.to_dict() for (c, m), r in tab.iterrows()}
    out["omission_by_condition"] = d[d.condition != "NONE"].groupby("condition").omit.mean().round(4).to_dict()
    out["omission_by_model"] = {m: dict(lc=float(lc_omit(g)), cv=float(cv_omit(g))) for m, g in d.groupby("model")}
    out["omission_by_framing"] = {f: dict(lc=float(lc_omit(g)), cv=float(cv_omit(g))) for f, g in d.groupby("framing")}
    out["named_as_indigenous_governance_given_lc_mention"] = float(
        d[d.condition.isin(S.LC_CONDITIONS) & (d.mention == 1)].named_lc.mean())
    out["matched_pairs"] = {
        "nc_restriction: LC_NC vs CV_NC": [float(d[d.condition == "LC_NC"].omit.mean()), float(d[d.condition == "CV_NC"].omit.mean())],
        "invitation: LC_CB vs CV_CONTACT": [float(d[d.condition == "LC_CB"].omit.mean()), float(d[d.condition == "CV_CONTACT"].omit.mean())],
        "uri_cue: LC_CB vs LC_CB_NOURI": [float(d[d.condition == "LC_CB"].omit.mean()), float(d[d.condition == "LC_CB_NOURI"].omit.mean())]}
    nm = d[d.condition != "NONE"]
    out["omission_name_only"] = dict(lc=float(1 - nm[nm.condition.isin(S.LC_CONDITIONS)].mention_name.mean()),
                                     cv=float(1 - nm[nm.condition.isin(S.CV_CONDITIONS)].mention_name.mean()),
                                     by_condition=(1 - nm.groupby("condition").mention_name.mean()).round(4).to_dict())
    out["truncated_share"] = float((d.finish == "length").mean()) if "finish" in d else None
    nt = d[d.finish != "length"] if "finish" in d else d
    out["sensitivity_excluding_truncated"] = dict(lc_omission=float(lc_omit(nt)), cv_omission=float(cv_omit(nt)),
                                                  n=int(len(nt)))
    out["by_record_source"] = {("neotoma" if k else "other"): dict(lc=float(lc_omit(g)), cv=float(cv_omit(g)))
                               for k, g in d.merge(pd.read_json(RUN / "data" / "corpus" / f"{which}.jsonl", lines=True)
                                                   [["doi", "condition", "neotoma"]], on=["doi", "condition"]).groupby("neotoma")}
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(TAB / f"primary_{which}.json", "w"), indent=1, default=float)
    d[["doi", "condition", "framing", "model", "mention", "named_lc"]].to_csv(TAB / f"scored_{which}.csv", index=False)
    print(json.dumps({k: out[k] for k in ("H1", "H2", "H3", "omission_by_condition", "fp_rates")}, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "main"))
