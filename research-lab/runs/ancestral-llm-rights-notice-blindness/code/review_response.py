"""Checks prompted by the adversarial review (review/review.md), in the study's own code (deviations D7). Post hoc;
none changes a preregistered verdict.

  R1  corrected omission: the reviewer's independent hand judgements of 270 main-set responses (including all 48
      Local Contexts scored omissions and 30 OLMo-2 CV_NC scored omissions) applied to the scorer's output; and the
      OLMo-2 researcher CV_NC cell re-scored two ways - (a) any non-commercial statement counts (plan section 4's
      content rule, literally), (b) the licence must be NAMED - with H2 recomputed under each
  R2  H3 decomposed: changes only to "unclear" vs definite changes (a field moves to a different yes/no), by element
      and model, with record-bootstrap intervals
  R3  false-positive rates of every pattern on NONE responses, by model x framing
  R4  omission by framing (the researcher framing is the one that tests whether a model volunteers the element), and
      the share of Local Contexts mentions that SPELL OUT the instrument (Local Contexts / Traditional Knowledge /
      Biocultural / Indigenous / cultural rights) rather than repeat a "TK ..." string
  R5  TK Community Use Only "commercial use allowed: yes" and TK CB "contact required" by model
  R6  invented CC terms (V3) without disclaimers: OLMo-2 NONE prose answers that tell the user commercial use is
      forbidden or needs permission, excluding answers that only say the clause does not apply; researcher vs direct
  R7  determinism: the 204 set-aside 700-token Qwen pilot rows against the final 1,100-token rows for the same prompts
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import score as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SPELLED = re.compile(r"local\s*contexts|traditional\s+knowledge|indigenous|biocultural|cultural\s+(rights|protocols?|responsibilit)", re.I)
ANY_NC = re.compile(r"non[- ]?commercial|commercial\s+(use|purposes?)", re.I)
FORBID = re.compile(r"(may\s+not|cannot|can't|must\s+not|not\s+(be\s+)?(allowed|permitted))[^.]{0,60}commercial|"
                    r"commercial[^.]{0,60}(not\s+(allowed|permitted)|prohibited|without\s+(prior\s+|specific\s+|explicit\s+)?permission)", re.I)
DISCLAIM = re.compile(r"not\s+(activated|applicable|included|part\s+of)|does\s+not\s+(have|include|apply)|non-applicable|n/?a\b", re.I)


def boot_rate(df, col, nboot=2000, seed=20261017):
    recs = df.doi.unique(); g = {k: v for k, v in df.groupby("doi")}
    rng = np.random.default_rng(seed); vals = []
    for _ in range(nboot):
        b = pd.concat([g[k] for k in rng.choice(recs, len(recs))])
        vals.append(b[col].mean())
    return float(df[col].mean()), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    d = A.score_frame(A.load("main"))
    d["mention_name"] = [S.mentions_by_name(t, c) if c in S.NAMES else np.nan for t, c in zip(d.text, d.condition)]
    out = {}
    # R1
    rj = pd.read_csv(RUN / "review" / "reviewer_checks" / "reviewer_judgements.csv")
    out["R1_reviewer_judgements"] = rj.groupby("stratum").apply(lambda g: dict(
        n=int(len(g)), scorer_mention_reviewer_mention=int(((g.auto == 1) & (g.reviewer == 1)).sum()),
        scorer_omit_reviewer_omit=int(((g.auto == 0) & (g.reviewer == 0)).sum()),
        scorer_omit_reviewer_mention=int(((g.auto == 0) & (g.reviewer == 1)).sum()),
        scorer_mention_reviewer_omit=int(((g.auto == 1) & (g.reviewer == 0)).sum()))).to_dict()
    lc = d[d.condition.isin(S.LC_CONDITIONS)]
    lc_false = int(((rj.stratum == "lc_omit") & (rj.reviewer == 1)).sum())
    out["R1_lc_omission_corrected"] = dict(scored=int((lc.omit == 1).sum()), false_per_reviewer=lc_false,
                                           corrected=float(((lc.omit == 1).sum() - lc_false) / len(lc)))
    cell = (d.model == "olmo2-13b") & (d.framing == "researcher") & (d.condition == "CV_NC")
    da = d.copy(); da.loc[cell, "omit"] = [0.0 if ANY_NC.search(t) else 1.0 for t in da[cell].text]
    dn = d.copy(); dn.loc[cell, "omit"] = 1 - dn.loc[cell, "mention_name"].astype(float)
    for name, x in (("a_any_nc_statement_counts", da), ("b_licence_must_be_named", dn)):
        cvx = x[x.condition.isin(S.CV_CONDITIONS)]
        est = A.boot(x, lambda b: A.lc_omit(b) - A.cv_omit(b), nboot=1000)
        out[f"R1_H2_{name}"] = dict(cv_omission=float(cvx.omit.mean()), lc_minus_cv=est[0], ci=[est[1], est[2]],
                                    cell_omission=float(x[cell].omit.mean()))
    out["R1_olmo_researcher_names"] = dict(cv_nc_named=float(d[cell].mention_name.mean()),
                                           lc_nc_named=float(d[(d.model == "olmo2-13b") & (d.framing == "researcher") & (d.condition == "LC_NC")].mention_name.mean()),
                                           none_nc_statement=float(np.mean([bool(ANY_NC.search(t)) for t in
                                                                            d[(d.model == "olmo2-13b") & (d.framing == "researcher") & (d.condition == "NONE")].text])))
    # R2
    a = d[d.framing == "agent"].copy(); a["f"] = [S.agent_fields(t) for t in a.text]
    base = a[a.condition == "NONE"].set_index(["doi", "model"]).f
    l = a[a.condition.isin(S.LC_CONDITIONS)].copy()
    l["b"] = [base.get((r.doi, r.model)) for r in l.itertuples()]
    l = l[l.f.notna() & l.b.notna()].copy()
    def kind(f, b):
        ch = [(x, y) for x, y in zip(f, b) if x != y]
        if not ch: return "none"
        return "only_to_unclear" if all(x == "unclear" for x, _ in ch) else "definite"
    l["kind"] = [kind(f, b) for f, b in zip(l.f, l.b)]
    l["any"] = (l.kind != "none").astype(float); l["definite"] = (l.kind == "definite").astype(float)
    out["R2_H3_decomposition"] = dict(pairs=int(len(l)), any_change=boot_rate(l, "any", 1000), definite=boot_rate(l, "definite", 1000),
                                      only_to_unclear_share_of_changes=float((l.kind == "only_to_unclear").sum() / (l.kind != "none").sum()),
                                      definite_by_condition=l.groupby("condition").definite.mean().round(3).to_dict(),
                                      definite_by_model=l.groupby("model").definite.mean().round(3).to_dict(),
                                      any_by_model=l.groupby("model")["any"].mean().round(3).to_dict())
    # R3
    n = d[d.condition == "NONE"]
    out["R3_fp_by_model_framing"] = {f"{m}|{fr}": {c: round(float(np.mean([S.mentions(t, c) for t in g.text])), 3) for c in S.PATTERNS}
                                     for (m, fr), g in n.groupby(["model", "framing"])}
    # R4
    nn = d[d.condition != "NONE"]
    out["R4_omission_by_framing_model"] = {f"{fr}|{m}": dict(lc=float(A.lc_omit(g)), cv=float(A.cv_omit(g)))
                                           for (fr, m), g in nn.groupby(["framing", "model"])}
    lm = d[d.condition.isin(S.LC_CONDITIONS) & (d.mention == 1)].copy()
    lm["spelled"] = [bool(SPELLED.search(S.strip_echo(t))) for t in lm.text]
    out["R4_spelled_out_share"] = {f"{fr}|{c}": round(float(g.spelled.mean()), 3) for (fr, c), g in lm.groupby(["framing", "condition"])}
    # R5
    a2 = a[a.f.notna()].copy(); a2["comm"] = [f[0] for f in a2.f]; a2["cont"] = [f[1] for f in a2.f]
    out["R5_tk_co_commercial_by_model"] = {m: g.comm.value_counts(normalize=True).round(3).to_dict()
                                           for m, g in a2[a2.condition == "LC_CO"].groupby("model")}
    out["R5_tk_cb_contact_by_model"] = {m: g.cont.value_counts(normalize=True).round(3).to_dict()
                                        for m, g in a2[a2.condition == "LC_CB"].groupby("model")}
    # R6
    o = d[(d.model == "olmo2-13b") & (d.condition == "NONE") & (d.framing != "agent")].copy()
    def forbids(t):
        sents = re.split(r"(?<=[.!?])\s+|\n+", t)
        return any(FORBID.search(s) and not DISCLAIM.search(s) for s in sents)
    o["forbid"] = [forbids(t) for t in o.text]
    out["R6_olmo_forbids_commercial_in_NONE"] = dict(all=float(o.forbid.mean()),
                                                    by_framing=o.groupby("framing").forbid.mean().round(3).to_dict())
    # R7
    disc = [json.loads(x) for x in open(RUN / "data" / "generations" / "discarded_700tok" / "qwen3-32b_pilot.jsonl")]
    fin = {(r["doi"], r["condition"], r["framing"]): r for r in map(json.loads, open(RUN / "data" / "generations" / "qwen3-32b_pilot.jsonl"))}
    same, mention_same, n_el, fields_same, n_ag = 0, 0, 0, 0, 0
    for r in disc:
        f = fin.get((r["doi"], r["condition"], r["framing"]))
        if not f or "text" not in r: continue
        same += r["text"] == f["text"]
        if r["condition"] in S.PATTERNS:
            n_el += 1; mention_same += S.mentions(r["text"], r["condition"]) == S.mentions(f["text"], r["condition"])
        if r["framing"] == "agent":
            n_ag += 1; fields_same += S.agent_fields(r["text"]) == S.agent_fields(f["text"])
    out["R7_determinism"] = dict(rows=len(disc), identical_text=int(same), element_rows=n_el, mention_same=int(mention_same),
                                 agent_rows=n_ag, agent_fields_same=int(fields_same))
    json.dump(out, open(TAB / "review_response.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("R3")}, indent=1, default=float)[:6000])


if __name__ == "__main__":
    sys.exit(main())
