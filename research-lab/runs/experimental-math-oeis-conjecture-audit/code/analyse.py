"""Summary tables (plan sections 0 and 4) -> results/tables/primary.json, falsifications.csv, selection.csv,
bdeep_contradictions.csv. Rewritten in D2 after the independent review.

Population for H1 (plan section 1): parsed C/G/D conjectures. D2 changes what counts as screenable:
  - data_status "consistent" (>= 5 data terms checked); "unchecked" and "few_checked" are reported, not screened;
  - class P (polynomial closed forms, which the plan lists as "not parsed") is reported separately;
  - lines the editors already tagged [Wrong]/[Incorrect] are reported separately and do not count toward H1;
  - rates are given separately for entries with and without a real b-file (LODA programs are validated against
    b-files, so in the first stratum LODA is not an independent second source; finding 2).
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
CGD = ["C", "G", "D"]


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 6), round(c + h, 6)]


def rate(k, n):
    return {"k": int(k), "n": int(n), "rate": round(k / n, 6) if n else None, "wilson": wilson(int(k), int(n))}


def boot_entries(d, flag, B=2000, seed=20261107):
    """Line-level rate with a bootstrap over entries (lines on one entry are not independent)."""
    g = d.groupby("anum")[flag].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    rng = np.random.default_rng(seed)
    r = []
    for _ in range(B):
        i = rng.integers(0, len(g), len(g))
        r.append(s[i].sum() / c[i].sum())
    return [round(float(np.quantile(r, .025)), 6), round(float(np.quantile(r, .975)), 6)]


if __name__ == "__main__":
    C = pd.read_parquet(INT / "conjectures.parquet")
    S = pd.read_parquet(INT / "screen.parquet")
    F = pd.read_parquet(INT / "confirm.parquet")
    S = S.merge(C[["anum", "line_no", "flagged_wrong", "mentions_proof", "in_block", "gf_shifted", "keywords", "offset"]],
                on=["anum", "line_no"], how="left")
    parsed = C[C.status == "parsed"]
    cgd = parsed[parsed.cls.isin(CGD)]
    out = {"candidate_lines": int(len(C)), "entries_with_candidates": int(C.anum.nunique()),
           "status": C.status.value_counts().to_dict(),
           "parsed_by_class": parsed.cls.value_counts().to_dict(),
           "cgd_data_status": cgd.data_status.value_counts().to_dict(),
           "cgd_data_status_by_class": {c: g.data_status.value_counts().to_dict() for c, g in cgd.groupby("cls")},
           "P_data_status": parsed[parsed.cls == "P"].data_status.value_counts().to_dict(),
           "cgd_consistent_flagged_wrong": int(((cgd.data_status == "consistent") & cgd.flagged_wrong).sum()),
           "in_block_lines": int(C.in_block.sum())}

    pop = S[S.cls.isin(CGD) & ~S.flagged_wrong]
    out["screen_cgd_unflagged"] = pop.screen.value_counts().to_dict()
    scr = pop[pop.screen.isin(["agree", "disagree"])].copy()
    scr["dis"] = scr.screen == "disagree"
    scr["has_bfile"] = scr.bfile_bytes.notna()
    out["screened"] = rate(scr.dis.sum(), len(scr))
    out["screened_by_bfile_stratum"] = {
        "with_bfile (LODA validated against it: not an independent source)": rate(scr[scr.has_bfile].dis.sum(), scr.has_bfile.sum()),
        "without_bfile (LODA mined on the data alone: an unresolved extrapolation)": rate(scr[~scr.has_bfile].dis.sum(), (~scr.has_bfile).sum())}
    out["entries_screened_by_bfile_stratum"] = {"with": int(scr[scr.has_bfile].anum.nunique()), "without": int(scr[~scr.has_bfile].anum.nunique())}
    out["by_class"] = {c: rate(scr[scr.cls == c].dis.sum(), (scr.cls == c).sum()) for c in CGD}
    out["by_class_and_stratum"] = {c: {"with_bfile": rate(g[g.has_bfile].dis.sum(), g.has_bfile.sum()),
                                       "without_bfile": rate(g[~g.has_bfile].dis.sum(), (~g.has_bfile).sum())} for c, g in scr.groupby("cls")}
    ag = scr[~scr.dis]
    out["agree_loda_states_same_recurrence"] = int(ag.loda_same_recurrence.fillna(False).sum())
    out["screened_mentions_proof"] = int(scr.mentions_proof.sum())
    out["screened_gf_matched_only_shifted"] = int(scr[scr.cls == "G"].gf_shifted.sum())
    out["beyond_data_terms_checked"] = {"median": float(scr.beyond_data_checked.median()), "p10": float(scr.beyond_data_checked.quantile(.1)),
                                        "p90": float(scr.beyond_data_checked.quantile(.9)),
                                        "share_capped_at_data_length": round(float((scr.beyond_data_checked == scr.nterms).mean()), 4)}
    # flagged lines (already known wrong) and P lines, outside the H1 count
    fl = S[S.cls.isin(CGD) & S.flagged_wrong]
    out["flagged_wrong_screen"] = fl.screen.value_counts().to_dict()
    out["P_screen"] = S[S.cls == "P"].screen.value_counts().to_dict()

    F = F.merge(C[["anum", "line_no", "flagged_wrong"]], on=["anum", "line_no"], how="left")
    out["confirm"] = F.confirm.value_counts().to_dict()
    conf = F[F.confirm == "confirmed"]
    out["confirmed_falsifications_all"] = int(len(conf))
    out["confirmed_already_flagged_wrong"] = int(conf.flagged_wrong.sum())
    out["confirmed_falsifications_new"] = int((~conf.flagged_wrong).sum())
    out["confirmed_new_anums"] = sorted(conf[~conf.flagged_wrong].anum.unique().tolist())
    out["H1_preregistered_rule"] = "Supported" if out["confirmed_falsifications_new"] >= 100 else "Refuted"
    fals = F.merge(S[["anum", "line_no", "nterms", "beyond_data_checked", "loda_value", "pred_value", "bfile_bytes"]],
                   on=["anum", "line_no"], how="left")
    fals["has_bfile"] = fals.bfile_bytes.notna()
    fals["note"] = ""
    fals.loc[fals.flagged_wrong.fillna(False), "note"] = "already tagged [Wrong] by OEIS editors"
    fals.loc[fals.anum == "A301424", "note"] = "the line's '(conjectured)' qualifies the denominator's factorisation, not the g.f."
    fals.drop(columns=["bfile_bytes"]).to_csv(TAB / "falsifications.csv", index=False)

    # selection into the screened set (finding 9): share with no LODA program, among consistent unflagged C/G/D lines
    sel = pop[pop.screen.isin(["agree", "disagree", "no_program", "loda_failed", "loda_mismatch_or_short"])].copy()
    sel["no_program"] = sel.screen == "no_program"
    num = sel.anum.str[1:].astype(int)
    sel["range"] = pd.cut(num, [0, 100000, 200000, 300000, 10**7], labels=["A000001-A100000", "A100001-A200000", "A200001-A300000", "A300001+"])
    sel["easy"] = sel.keywords.fillna("").str.contains(r"\beasy\b")
    rows = []
    for dim, col in (("keyword easy", "easy"), ("A-number range", "range"), ("in a (Start)/(End) block", "in_block"), ("class", "cls")):
        for v, g in sel.groupby(col, observed=True):
            rows.append({"dimension": dim, "value": str(v), "lines": int(len(g)), "share_no_loda_program": round(float(g.no_program.mean()), 3)})
    pd.DataFrame(rows).to_csv(TAB / "selection.csv", index=False)
    out["selection_table"] = "results/tables/selection.csv"

    # direct b-file test on a random sample (post hoc)
    bp = INT / "bdeep.parquet"
    if bp.exists():
        B = pd.read_parquet(bp)
        t = B[B.bdeep.isin(["agrees", "contradicted"])].copy()
        t["contra"] = t.bdeep == "contradicted"
        ent_pop = int(json.loads((INT / "bdeep_meta.json").read_text())["population_entries"]) if (INT / "bdeep_meta.json").exists() else None
        out["bdeep"] = {"status": B.bdeep.value_counts().to_dict(),
                        "entries_tested": int(t.anum.nunique()), "lines_tested": int(len(t)),
                        "contradicted": rate(t.contra.sum(), len(t)),
                        "contradicted_ci_bootstrap_entries": boot_entries(t, "contra"),
                        "contradicted_entries": int(t[t.contra].anum.nunique()),
                        "by_class": {c: rate(g.contra.sum(), len(g)) for c, g in t.groupby("cls")},
                        "beyond_data_checked": {"median": float(t.beyond_data_checked.median()), "p10": float(t.beyond_data_checked.quantile(.1)),
                                                "p90": float(t.beyond_data_checked.quantile(.9))},
                        "fail_beyond_data": {"median": float(t[t.contra].fail_beyond_data.median()) if t.contra.any() else None,
                                             "max": float(t[t.contra].fail_beyond_data.max()) if t.contra.any() else None},
                        "with_loda_program": rate(t[t.has_program].contra.sum(), t.has_program.sum()),
                        "without_loda_program": rate(t[~t.has_program].contra.sum(), (~t.has_program).sum()),
                        "agreeing_bfile_comment_mentions_a_formula": round(float(t[~t.contra].comment_mentions_formula.fillna(False).mean()), 3)
                        if "comment_mentions_formula" in t else None,
                        "population_entries_with_bfile": ent_pop}
        t[t.contra].drop(columns=["contra"]).to_csv(TAB / "bdeep_contradictions.csv", index=False)
    (TAB / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))
