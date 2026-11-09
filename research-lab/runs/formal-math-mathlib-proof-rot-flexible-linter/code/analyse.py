"""H1 GEE and secondaries (plan sections 4-5) -> results/tables/primary.json.

D3 (after the independent review): declarations flagged comment_before_by are dropped (unreliable replayed body);
error classes are recomputed from the stored replay messages with the corrected patterns, both as the class of the
first reported error and as the highest-priority class; the body-change rates replace the "unchanged bodies never
fail" figure (true by construction); the pooled analysis clusters by file across the two pairs, which share
declarations; the independence working correlation and the unadjusted odds ratio are reported beside the GEE.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

RUN = Path(__file__).resolve().parents[1]
WORK, TAB = RUN / "data" / "work", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import rot  # noqa: E402
TAB.mkdir(parents=True, exist_ok=True)


def frame(o, n):
    P = pd.read_parquet(WORK / f"pop_{o}_{n}.parquet")
    L = pd.read_parquet(WORK / f"label_{o}.parquet")
    R = pd.read_parquet(WORK / f"replay_{o}_{n}.parquet")
    d = P.merge(L, on=["file", "name"]).merge(R, on=["file", "name"])
    d = d[(d.o_errors == 0) & ~d.o_timeout]                 # validation: declarations that compile in O
    if "comment_before_by" in d:
        d = d[~d.comment_before_by]                          # D3
    msgs = d.msgs.fillna("").map(lambda m: [x for x in m.split(" || ") if x])
    keep = d.eclass.isin(["timeout", "lost_in_rewrite"])
    d["eclass_v1"] = d.eclass
    d["eclass"] = np.where(keep, d.eclass, msgs.map(rot.eclass))                 # highest-priority class
    d["eclass_first"] = np.where(keep, d.eclass_v1, msgs.map(rot.eclass_first))  # first reported error
    d["fail_i"] = d.fail.astype(int)
    d["flag_i"] = d.flagged.astype(int)
    d["log_tac"] = np.log(d.tactics)
    return d


def gee(d, y="fail_i", cov=None, groups="file"):
    if d[y].sum() < 5 or d.flag_i.sum() < 5:
        return None
    m = smf.gee(f"{y} ~ flag_i + log_tac + n_simp", groups=groups, data=d, family=sm.families.Binomial(),
                cov_struct=cov or sm.cov_struct.Exchangeable()).fit()
    b, se = m.params["flag_i"], m.bse["flag_i"]
    return {"or": round(float(np.exp(b)), 4), "ci": [round(float(np.exp(b - 1.96 * se)), 4), round(float(np.exp(b + 1.96 * se)), 4)],
            "p": round(float(m.pvalues["flag_i"]), 5), "n": int(len(d)), "files": int(d.file.nunique()),
            "fail_flagged": round(float(d[d.flag_i == 1][y].mean()), 4), "fail_unflagged": round(float(d[d.flag_i == 0][y].mean()), 4),
            "n_flagged": int(d.flag_i.sum())}


def verdict(r):
    if r is None:
        return "not testable"
    lo, hi = r["ci"]
    return "Supported" if (r["or"] >= 1.5 and lo > 1.0) else "Refuted" if hi < 1.5 else "Inconclusive"


if __name__ == "__main__":
    out = {}
    d = frame("O_2504", "N_2604")
    out["primary"] = gee(d)
    out["H1"] = verdict(out["primary"])
    out["primary_population"] = {"declarations": int(len(d)), "flagged": int(d.flag_i.sum()), "fail_rate": round(float(d.fail_i.mean()), 4),
                                 "body_changed_flagged": [int((~d[d.flag_i == 1].same_body).sum()), int((d.flag_i == 1).sum())],
                                 "body_changed_unflagged": [int((~d[d.flag_i == 0].same_body).sum()), int((d.flag_i == 0).sum())]}
    out["primary_independence"] = gee(d, cov=sm.cov_struct.Independence())
    a, b = d[d.flag_i == 1].fail_i, d[d.flag_i == 0].fail_i
    out["primary_unadjusted_or"] = round(float((a.sum() / (len(a) - a.sum())) / (b.sum() / (len(b) - b.sum()))), 4)
    out["error_classes"] = d[d.fail].eclass.value_counts().to_dict()
    out["error_classes_first"] = d[d.fail].eclass_first.value_counts().to_dict()
    out["error_classes_v1_patterns"] = d[d.fail].eclass_v1.value_counts().to_dict()
    out["error_classes_by_flag_first"] = {str(k): g.eclass_first.value_counts().to_dict() for k, g in d[d.fail].groupby("flag_i")}
    d2 = d.copy()
    d2["fail_nounk"] = (d2.fail & ~d2.only_unknown_id.fillna(False)).astype(int)
    out["excluding_unknown_identifier_only"] = gee(d2, "fail_nounk")
    d6 = frame("O_2504", "O_2510")
    out["decay"] = {"O+6": {"fail_flagged": round(float(d6[d6.flag_i == 1].fail_i.mean()), 4), "fail_unflagged": round(float(d6[d6.flag_i == 0].fail_i.mean()), 4), "n": int(len(d6))},
                    "O+12": {"fail_flagged": out["primary"]["fail_flagged"] if out["primary"] else None,
                             "fail_unflagged": out["primary"]["fail_unflagged"] if out["primary"] else None, "n": int(len(d))},
                    "O+6_gee": gee(d6)}
    dS = frame("O_2510", "N_2610")
    out["secondary_pair"] = gee(dS)
    # D3: the pairs share declarations; cluster by file across both pairs instead of prefixing file names
    shared = d.merge(dS, on=["file", "name"])
    pooled = pd.concat([d, dS])
    out["pooled"] = gee(pooled)
    if out["pooled"]:
        out["pooled"]["note"] = f"{len(shared)} (file, name) declarations appear in both pairs; clustered by file across pairs"
    out["secondary_pair_flagged_post_cleanup"] = {"O2_flagged": int(dS.flag_i.sum()), "O2_declarations": int(len(dS))}
    out["secondary_error_classes"] = dS[dS.fail].eclass.value_counts().to_dict()
    # D4 (confirmation finding N1, post hoc): proofs using `induction'` all fail because Mathlib.Tactic.Common stopped
    # importing Mathlib.Tactic.Cases between O and O2 (not simp fragility). Exclusion sensitivity, and the error mix.
    # D5 (second confirmation, item 2): a token match outside comments. The plain substring also hit three proofs that
    # only name the lemma `LieSubmodule.iSup_induction'` (`induction ... using ...`), which fail for another reason.
    import re
    tac = re.compile(r"(?<![\w.'])induction'(?![\w'])")
    nocomment = lambda b: re.sub(r"--[^\n]*", "", re.sub(r"/-.*?-/", "", b, flags=re.S))  # noqa: E731
    uses = lambda x: x.body_o.fillna("").map(lambda b: bool(tac.search(nocomment(b))))  # noqa: E731
    ind = lambda x: x[~uses(x)]  # noqa: E731
    sub = lambda x: x.body_o.str.contains("induction'", regex=False)  # noqa: E731
    out["induction_prime"] = {"match": "token outside comments (D5)", "primary_proofs": int(uses(d).sum()),
                              "primary_flagged_using": [int(uses(d[d.flag_i == 1]).sum()), int((d.flag_i == 1).sum())],
                              "primary_unflagged_using": [int(uses(d[d.flag_i == 0]).sum()), int((d.flag_i == 0).sum())],
                              "fail_rate_among_users": round(float(d[uses(d)].fail_i.mean()), 4),
                              "six_month_proofs": int(uses(d6).sum()), "second_pair_proofs": int(uses(dS).sum()),
                              "substring_matches_D4": {"primary": int(sub(d).sum()), "six_months": int(sub(d6).sum()), "second_pair": int(sub(dS).sum()),
                                                       "primary_fail_rate": round(float(d[sub(d)].fail_i.mean()), 4)}}
    out["excluding_induction_prime"] = {"primary": gee(ind(d)), "six_months": gee(ind(d6)), "pooled": gee(pd.concat([ind(d), ind(dS)])),
                                        "excluding_unknown_identifier_only": gee(ind(d2), "fail_nounk"),
                                        "primary_independence": gee(ind(d), cov=sm.cov_struct.Independence())}
    full = {"primary": out.get("primary"), "six_months": (out.get("decay") or {}).get("O+6_gee"), "pooled": out.get("pooled"),
            "excluding_unknown_identifier_only": out.get("excluding_unknown_identifier_only"),
            "primary_independence": out.get("primary_independence")}
    out["induction_prime_share_of_log_or_removed"] = {k: round(1 - np.log(out["excluding_induction_prime"][k]["or"]) / np.log(v["or"]), 3)
                                                      for k, v in full.items() if v and v.get("or")}
    out["induction_prime_raw_gap_points"] = {"all": round(100 * (d[d.flag_i == 1].fail_i.mean() - d[d.flag_i == 0].fail_i.mean()), 1),
                                             "excluding": round(100 * (ind(d)[ind(d).flag_i == 1].fail_i.mean() - ind(d)[ind(d).flag_i == 0].fail_i.mean()), 1)}
    fm = d[d.fail]
    out["first_error_unknown_tactic"] = {"all": int(fm.msgs.fillna("").str.split(" \\|\\| ").str[0].str.contains("unknown tactic", case=False).sum()),
                                         "flagged": int(fm[fm.flag_i == 1].msgs.fillna("").str.split(" \\|\\| ").str[0].str.contains("unknown tactic", case=False).sum()),
                                         "failures": int(len(fm)), "flagged_failures": int((fm.flag_i == 1).sum())}
    out["first_error_invalid_field_env"] = int(fm.msgs.fillna("").str.split(" \\|\\| ").str[0].str.contains("environment does not contain", case=False).sum())
    (TAB / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
