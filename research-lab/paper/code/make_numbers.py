"""Compute every number quoted in the paper from the audit files and write paper/numbers.tex (LaTeX macros),
paper/tables/*.tex and paper/figures/*.pdf. Nothing in results.tex is typed by hand except through these macros.
Coder-dependent parts use the adjudicated files when present (audit/adjudicated_*.csv), else coder A/B raw files."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import cohen_kappa_score  # noqa: E402

PAPER = Path(__file__).resolve().parents[1]
LAB = PAPER.parent
AUD = PAPER / "audit"
TAB = PAPER / "tables"
FIG = PAPER / "figures"
M = {}


def pct(x, d=0):
    return f"{100 * x:.{d}f}\\%"


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def leads_and_verdicts():
    L = json.load(open(LAB / "leads.json"))["leads"]
    runs = sorted(p.name for p in (LAB / "runs").iterdir() if p.is_dir())
    byid = {l["id"]: l for l in L}
    M["LeadsTotal"] = len(L)
    M["LeadDomains"] = len({l["domain"] for l in L})
    M["StudiesTotal"] = len(runs)
    M["StudyDomains"] = len({byid[r]["domain"] for r in runs})
    rep = [r for r in runs if (LAB / "runs" / r / "report.md").exists()]
    M["StudiesReported"] = len(rep)
    vt = pd.Series([byid[r].get("verdict_tag") for r in rep]).value_counts()
    for k in ["Supported", "Refuted", "Unsupported", "Inconclusive", "Pending"]:
        M[f"Verdict{k}"] = int(vt.get(k, 0))
    M["VerdictsDecided"] = sum(M[f"Verdict{k}"] for k in ["Supported", "Refuted", "Unsupported", "Inconclusive"])
    rows = [dict(run=r, domain=byid[r]["domain"], verdict=byid[r].get("verdict_tag") or "in progress", value=byid[r].get("value_score"),
                 cost=byid[r].get("cost_score"), title=byid[r].get("title", "")) for r in runs]
    return pd.DataFrame(rows)


def prereg():
    a = pd.read_csv(AUD / "A_prereg_timing.csv")
    M["PreregPassStrict"] = int(a.passes.sum())
    # classification from audit/deviations.md A1: same-commit material is pre-outcome except GWTC-4
    fail = a[~a.passes]
    benign = {"auckland-nz-speed-limit-reversal-crashes", "auckland-nz-wastewater-testing-gap-deprivation", "health-econ-wastewater-flusight-value"}
    M["PreregPassClassified"] = int(a.passes.sum() + fail.run.isin(benign).sum())
    M["PreregSameCommit"] = int(a.same_commit.sum())
    e = pd.read_csv(AUD / "A_plan_edits.csv") if (AUD / "A_plan_edits.csv").stat().st_size > 2 else pd.DataFrame()
    M["PlanEditsAfterCommit"] = len(e)
    M["PreregMedianHours"] = f"{a.hours_plan_to_first_output.median():.1f}"
    return a


def numbers():
    s = pd.read_csv(AUD / "D_numbers_summary.csv")
    allm = pd.read_csv(AUD / "D_numbers_all.csv")
    sub = allm[allm.substantive]
    M["NumAll"] = f"{len(allm):,}".replace(",", "{,}")
    M["NumSubstantive"] = f"{len(sub):,}".replace(",", "{,}")
    M["NumTracedSubst"] = pct(sub.traced.mean(), 1)
    nl = pd.read_csv(AUD / "D_numbers_null.csv")
    M["NumChanceAll"] = pct(nl.traced_cross_mean.mean(), 0)
    M["NumOwnAll"] = pct(nl.traced_own.mean(), 0)
    g = pd.read_csv(AUD / "D_numbers_by_sigdigits.csv", index_col=0)
    M["NumCorrectedThree"] = pct(g.loc[3, "corrected"], 0)
    M["NumOwnThree"] = pct(g.loc[3, "traced_own"], 1)
    M["NumChanceThree"] = pct(g.loc[3, "traced_chance"], 1)
    M["NumNThree"] = int(g.loc[3, "n"])
    M["NumOwnFour"] = pct(g.loc[4, "traced_own"], 1)
    M["NumChanceFour"] = pct(g.loc[4, "traced_chance"], 1)
    M["NumOwnFive"] = pct(g.loc[5, "traced_own"], 1)
    M["NumNFive"] = int(g.loc[5, "n"])
    M["NumMinReport"] = pct(s.traced_substantive.min(), 0)
    # figure: own vs chance by significant digits
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    x = np.arange(len(g))
    ax.bar(x - 0.2, g.traced_own, 0.4, label="own study's results", color="#2b6c8f")
    ax.bar(x + 0.2, g.traced_chance, 0.4, label="other studies' results (chance)", color="#c9a14a")
    ax.set_xticks(x, [f"{i}{'+' if i == 5 else ''}\n(n={int(n)})" for i, n in zip(g.index, g.n)])
    ax.set_xlabel("significant digits printed in the report")
    ax.set_ylabel("share of numbers that 'trace'")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG / "number_tracing.pdf")
    plt.close(fig)


def refs():
    r = pd.read_csv(AUD / "E_refs.csv").drop_duplicates(["kind", "id"])
    M["RefArxiv"] = int((r.kind == "arxiv").sum())
    M["RefDoi"] = int((r.kind == "doi").sum())
    M["RefArxivOK"] = int(r[r.kind == "arxiv"].resolves.astype(bool).sum())
    M["RefDoiOKRaw"] = int(r[r.kind == "doi"].resolves.fillna(False).astype(bool).sum())


def calibration():
    f = pd.read_csv(AUD / "F_calibration.csv")
    mid = (f.est_lo_days + f.est_hi_days) / 2
    M["ScoutDaysTotal"] = f"{mid.sum():.0f}"
    M["ScoutDaysMedian"] = f"{mid.median():.1f}"
    a = pd.read_csv(AUD / "A_prereg_timing.csv")
    t0 = pd.to_datetime(a.t_plan.min(), unit="s", utc=True).tz_convert("Pacific/Auckland")
    rep = [r for r in a.run if (LAB / "runs" / r / "report.md").exists()]
    first_rep = []
    import subprocess
    for r in rep:
        out = subprocess.check_output(["git", "log", "--diff-filter=A", "--format=%ct", "--", f"research-lab/runs/{r}/report.md"], cwd=LAB.parent, text=True).split()
        first_rep.append(int(out[-1]))
    t1 = pd.to_datetime(max(first_rep), unit="s", utc=True).tz_convert("Pacific/Auckland")
    t_first = pd.to_datetime(min(first_rep), unit="s", utc=True).tz_convert("Pacific/Auckland")
    M["CalendarFirstReport"] = t_first.strftime("%-d %B %Y")
    M["CalendarLastReport"] = t1.strftime("%-d %B %Y")
    M["CalendarSpanDays"] = f"{(t1 - t_first).total_seconds() / 86400:.0f}"
    after = sorted(first_rep)[1:]
    M["ReportsAfterFirst"] = len(after)
    M["CalendarBulkDays"] = f"{(max(after) - min(after)) / 86400:.1f}"
    by = f.groupby("verdict")[["value", "cost"]].mean()
    by.round(2).to_csv(AUD / "F_verdict_by_scores.csv")


def coders():
    """Deviations (B) and review (C): agreement between coders, then adjudicated values if present."""
    out = {}
    fa, fb = AUD / "coder_A" / "B_deviations.csv", AUD / "coder_B" / "B_deviations.csv"
    if not (fa.exists() and fb.exists()):
        return out
    a, b = pd.read_csv(fa), pd.read_csv(fb)
    for d in (a, b):
        d["key"] = d.run.astype(str) + "|" + d.entry_id.astype(str).str.strip()
    m = a.merge(b, on="key", suffixes=("_A", "_B"))
    M["DevCodedA"], M["DevCodedB"], M["DevMatched"] = len(a), len(b), len(m)
    for col in ["category", "trigger", "timing", "verdict_relevance"]:
        xa = m[f"{col}_A"].astype(str).str.strip().str.lower()
        xb = m[f"{col}_B"].astype(str).str.strip().str.lower()
        out[col] = dict(kappa=cohen_kappa_score(xa, xb), agree=(xa == xb).mean())
        M[f"Kappa{col.title().replace('_', '')}"] = f"{out[col]['kappa']:.2f}"
        M[f"Agree{col.title().replace('_', '')}"] = pct(out[col]["agree"], 0)
    adj = AUD / "adjudicated_B.csv"
    final = pd.read_csv(adj) if adj.exists() else a
    M["DevTotal"] = len(final)
    M["DevStudies"] = final.run.nunique()
    vr = final.verdict_relevance.astype(str).str.lower().str.strip()
    M["DevVerdictRelevant"] = int((vr == "yes").sum())
    M["DevVerdictRelevantPct"] = pct((vr == "yes").mean(), 0)
    cat = final.category.astype(str).str.extract(r"(C\d)")[0].value_counts()
    for c in [f"C{i}" for i in range(1, 9)]:
        M[f"Dev{c}"] = int(cat.get(c, 0))
    trig = final.trigger.astype(str).str.extract(r"(T\d)")[0].value_counts()
    for t in [f"T{i}" for i in range(1, 5)]:
        M[f"Dev{t}"] = int(trig.get(t, 0))
    tim = final.timing.astype(str).str.lower().str.strip().value_counts()
    M["DevAfter"], M["DevBefore"] = int(tim.get("after", 0)), int(tim.get("before", 0))
    M["DevCFour"] = M["DevC4"]
    return out


def review():
    ca, cb = AUD / "coder_A" / "C_review.csv", AUD / "coder_B" / "C_review.csv"
    if not (ca.exists() and cb.exists()):
        return
    a, b = pd.read_csv(ca), pd.read_csv(cb)
    m = a.merge(b, on="run", suffixes=("_A", "_B"))
    for col in ["headline_changed", "verdict_changed", "confirmation_pass"]:
        xa = m[f"{col}_A"].astype(str).str.lower().str.strip()
        xb = m[f"{col}_B"].astype(str).str.lower().str.strip()
        M[f"Agree{col.title().replace('_', '')}"] = pct((xa == xb).mean(), 0)
    adj = AUD / "adjudicated_C.csv"
    final = pd.read_csv(adj) if adj.exists() else a
    M["ReviewStudies"] = len(final)
    rec = final.recommendation.astype(str).str.lower()
    M["ReviewFixFirst"] = int(rec.str.contains("fix").sum())
    M["ReviewConfirmation"] = int((final.confirmation_pass.astype(str).str.lower().str.strip() == "yes").sum())
    M["ReviewHeadlineChanged"] = int((final.headline_changed.astype(str).str.lower().str.strip() == "yes").sum())
    M["ReviewVerdictChanged"] = int((final.verdict_changed.astype(str).str.lower().str.strip() == "yes").sum())
    n = pd.to_numeric(final.n_issues, errors="coerce")
    M["ReviewIssuesMedian"] = f"{n.median():.0f}"
    M["ReviewIssuesTotal"] = f"{n.sum():.0f}"
    for r in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        M[f"Review{r}"] = int(pd.to_numeric(final[r], errors="coerce").fillna(0).sum())


def inventory():
    f = AUD / "inventory" / "plan_inventory.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    norm = lambda s: s.astype(str).str.lower().str.strip()  # noqa: E731
    M["InvPower"] = int((norm(d.power) == "yes").sum())
    M["InvPowerPartial"] = int((norm(d.power) == "partial").sum())
    ob = norm(d.outcome_blinding)
    for k in ["sealed", "prospective", "formal", "none", "partial"]:
        M[f"InvBlind{k.title()}"] = int(ob.str.startswith(k).sum())
    M["InvBlindStrong"] = M["InvBlindSealed"] + M["InvBlindProspective"] + M["InvBlindFormal"]
    for c in ["disclosure", "decision_rule", "validation", "independent_review", "data_open"]:
        M[f"Inv{c.title().replace('_', '')}"] = int((norm(d[c]) == "yes").sum())
        M[f"Inv{c.title().replace('_', '')}Partial"] = int((norm(d[c]) == "partial").sum())
    M["InvMultiplicityYes"] = int((norm(d.multiplicity) == "yes").sum())
    M["InvMultiplicityNo"] = int((norm(d.multiplicity) == "no").sum())


def write():
    lines = ["% generated by paper/code/make_numbers.py; do not edit"]
    for k, v in sorted(M.items()):
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    (PAPER / "numbers.tex").write_text("\n".join(lines) + "\n")
    print(f"{len(M)} macros written")


def main():
    TAB.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    port = leads_and_verdicts()
    port.to_csv(AUD / "portfolio.csv", index=False)
    prereg()
    numbers()
    refs()
    calibration()
    coders()
    review()
    inventory()
    write()


if __name__ == "__main__":
    main()
