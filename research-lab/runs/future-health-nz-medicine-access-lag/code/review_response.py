"""Numbers for the response to review/review.md (D8). Reads the pre-review release (results/tables/linked.csv as
committed in c0386fc) and the corrected data/linked.csv; writes results/tables/review_response.json and
results/tables/link_validation(_v2)_rescored.csv."""
import json
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from names import components, norm  # noqa: E402

T = RUN / "results" / "tables"


def git_show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:research-lab/runs/{RUN.name}/{path}"], cwd=RUN, capture_output=True,
                          text=True, check=True).stdout


def main():
    out = {}
    old = pd.read_csv(StringIO(git_show("c0386fc", "results/tables/linked.csv")), parse_dates=["t0", "t1", "t2", "t3"]).set_index("substance")
    new = pd.read_csv(RUN / "data" / "linked.csv", parse_dates=["t0", "t1", "t2", "t3", "t3b", "t3h", "brand_t2", "consent_ended"]).set_index("substance")
    coh = pd.read_csv(RUN / "data" / "cohort.csv").set_index("substance")

    # R5: what the cohort corrections changed
    gone = sorted(set(old.index) - set(new.index))
    added = sorted(set(new.index) - set(old.index))
    com = old.index.intersection(new.index)
    t0c = [s for s in com if old.loc[s, "t0"] != new.loc[s, "t0"]]
    out["R5_cohort"] = dict(before=len(old), after=len(new), removed_or_merged=len(gone), added_or_renamed=added,
                            cber_matched=int(coh.cber_t0.sum()),
                            cber_only_added=int((coh.fda_name.fillna("").str.startswith("CBER") & coh.ema_name.isna()).sum()),
                            t0_changed=len(t0c), t0_changed_median_days=float((old.loc[t0c, "t0"] - new.loc[t0c, "t0"]).dt.days.median()),
                            wrong_before_share=round((len(gone) + len(t0c)) / len(old), 3))
    for c in ("t1", "t2", "t3"):
        ch = [s for s in com if not ((pd.isna(old.loc[s, c]) and pd.isna(new.loc[s, c])) or old.loc[s, c] == new.loc[s, c])]
        out[f"R5_{c}_changed"] = {s: [str(old.loc[s, c])[:10], str(new.loc[s, c])[:10]] for s in ch}

    # R10: brand matches against the register snapshot
    b = new[new.brand_t2.notna()]
    out["R10_brand_matches"] = dict(n=int(len(b)), set_t2=[s for s in b.index if s in com and pd.isna(old.loc[s, "t2"]) and pd.notna(new.loc[s, "t2"])],
                                    substances=sorted(b.index))

    # R4/R11: re-score the pre-D8 validation rows the review identified (Section 23 application visible in the evidence)
    fix = {"r018": dict(t1_ok=0, t2_ok=0), "m116": dict(t1_ok=0, t2_ok=0), "r059": dict(t1_ok=0), "m073": dict(t1_ok=0)}
    prec = lambda x: {c: [round(float(x[c].dropna().mean()), 3), int(x[c].notna().sum())] for c in ("t1_ok", "t2_ok", "t3_ok")}
    res = {}
    for tag, fn in (("v1", "link_validation"), ("v2", "link_validation_v2")):
        v = pd.read_csv(T / f"{fn}.csv")
        v2 = v.copy()
        for i, f in fix.items():
            for k, val in f.items():
                v2.loc[v2.id == i, k] = val
            v2.loc[v2.id == i, "note"] = (v2.loc[v2.id == i, "note"].fillna("") + " [D8 re-score: Section 23 application earlier]").str.strip()
        v2.to_csv(T / f"{fn}_rescored.csv", index=False)
        res[f"{tag}_as_reported"], res[f"{tag}_rescored"] = prec(v), prec(v2)
        res[f"{tag}_ids_rescored"] = sorted(set(fix) & set(v.id))
    res["reviewer_readjudication"] = {"t1_ok": [0.89, 64], "t2_ok": [0.94, 70], "t3_ok": [1.0, 69]}
    out["R11_validation"] = res

    # R15: recall sample - the chemicals with no cohort hit, dated against every FDA/EMA first approval (any year)
    r = pd.read_csv(RUN / "data" / "validation" / "recall_sample.csv")
    allf = pd.read_csv(RUN / "data" / "all_first_approvals.csv", index_col=0, parse_dates=["first"])["first"]
    miss = r[r.cohort_hits == "[]"].copy()

    def earliest(chem):
        ds = [allf.get(norm(x)) for x in components(chem)] + [allf.get(norm(re.sub(r"\[.*?\]", "", chem)))]
        ds = [d for d in ds if d is not None and pd.notna(d)]
        return min(ds) if ds else pd.NaT
    miss["first_fda_ema"] = miss.chemical.map(earliest)
    out["R15_recall"] = dict(sample=len(r), with_cohort_hit=int(len(r) - len(miss)), without=int(len(miss)),
                             without_first_approved_before_2010=int((miss.first_fda_ema < "2010-01-01").sum()),
                             without_first_approved_2010_2024=miss[(miss.first_fda_ema >= "2010-01-01")][["chemical", "first_fda_ema"]].astype(str).values.tolist(),
                             without_no_fda_ema_match=miss[miss.first_fda_ema.isna()].chemical.tolist())

    # R17: did the Schedule Update gap fill (D4) set any T3?
    gap = lambda d: pd.notna(d) and ((pd.Timestamp("2024-06-01") <= d <= pd.Timestamp("2025-12-31")) or d.strftime("%Y-%m") == "2018-01")
    g = new[new.t3b.map(gap)]
    decided = g[g.t3h.isna() | (g.t3b < g.t3h)]
    out["R17_D4"] = dict(gap_window_t3b=int(len(g)), t3_set_by_su=decided.index.tolist())

    # R8: forecast substances
    f = pd.read_csv(RUN / "results" / "forecast_2026.csv")
    out["R8_forecast"] = dict(n=len(f), lapsed_consent=int(new.reindex(f.substance).consent_ended.notna().sum()),
                              no_longer_in_cohort=sorted(set(f.substance) - set(new.index)))
    json.dump(out, open(T / "review_response.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
