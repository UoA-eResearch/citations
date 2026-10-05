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
W = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}


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
    for i in range(1, 9):
        M[f"DevC{W[i]}"] = int(cat.get(f"C{i}", 0))
    trig = final.trigger.astype(str).str.extract(r"(T\d)")[0].value_counts()
    for i in range(1, 5):
        M[f"DevT{W[i]}"] = int(trig.get(f"T{i}", 0))
    tim = final.timing.astype(str).str.lower().str.strip().value_counts()
    M["DevAfter"], M["DevBefore"] = int(tim.get("after", 0)), int(tim.get("before", 0))
    M["DevUnclearTiming"] = int(tim.get("unclear", 0))
    M["DevAdjudications"] = len(pd.read_csv(AUD / "adjudication.csv").query("measure == 'B'")) if (AUD / "adjudication.csv").exists() else 0
    M["DevDisagreeEntries"] = int(((m.category_A.astype(str).str[:2].str.lower() != m.category_B.astype(str).str[:2].str.lower()) |
                                   (m.trigger_A.astype(str).str[:2].str.lower() != m.trigger_B.astype(str).str[:2].str.lower()) |
                                   (m.timing_A.astype(str).str.lower().str.strip() != m.timing_B.astype(str).str.lower().str.strip()) |
                                   (m.verdict_relevance_A.astype(str).str.lower().str.strip() != m.verdict_relevance_B.astype(str).str.lower().str.strip())).sum())
    # verdict-relevant deviations made after the outcome was seen, and the C4 entries
    M["DevRelevantAfter"] = int(((vr == "yes") & (final.timing.astype(str).str.lower().str.strip() == "after")).sum())
    final.assign(cat=final.category.astype(str).str[:2]).query("cat == 'C4'")[["run", "entry_id", "entry_title"]].to_csv(AUD / "B_decision_rule_changes.csv", index=False)
    # figure: categories by trigger
    lab = {"C1": "bug/numerical fix", "C2": "data problem", "C3": "primary spec change", "C4": "decision-rule change",
           "C5": "added secondary analysis", "C6": "environment/logistics", "C7": "clarification", "C8": "claim withdrawn/corrected"}
    tl = {"T1": "executor", "T2": "validation check", "T3": "independent reviewer", "T4": "external event"}
    ct = pd.crosstab(final.category.astype(str).str[:2], final.trigger.astype(str).str[:2]).reindex(index=list(lab), columns=list(tl), fill_value=0)
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    left = np.zeros(len(ct))
    cols = ["#2b6c8f", "#7fb069", "#c9a14a", "#a05a7a"]
    for t, col in zip(ct.columns, cols):
        ax.barh([lab[c] for c in ct.index], ct[t], left=left, color=col, label=tl[t])
        left += ct[t].values
    ax.invert_yaxis()
    ax.set_xlabel("number of logged deviations")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.45, -0.18), ncol=4)
    fig.tight_layout()
    fig.savefig(FIG / "deviations.pdf", bbox_inches="tight")
    plt.close(fig)
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
    nb = pd.to_numeric(final.n_issues_B, errors="coerce") if "n_issues_B" in final else n
    M["ReviewIssuesMedian"] = f"{n.median():.0f}"
    M["ReviewIssuesMedianB"] = f"{nb.median():.0f}"
    M["ReviewIssuesTotal"] = f"{n.sum():.0f}"
    M["ReviewIssuesTotalB"] = f"{nb.sum():.0f}"
    for i in range(1, 7):
        M[f"ReviewR{W[i]}"] = int(pd.to_numeric(final[f"R{i}"], errors="coerce").fillna(0).sum())
        if f"R{i}_B" in final:
            M[f"ReviewR{W[i]}B"] = int(pd.to_numeric(final[f"R{i}_B"], errors="coerce").fillna(0).sum())
    M["ReviewIssuesExactAgree"] = pct((n == nb).mean(), 0)


def inventory():
    f = AUD / "inventory" / "plan_inventory_adjudicated.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    norm = lambda s: s.astype(str).str.lower().str.strip()  # noqa: E731
    M["InvPower"] = int((norm(d.power) == "yes").sum())
    M["InvPowerPartial"] = int((norm(d.power) == "partial").sum())
    ob = norm(d.outcome_blinding)
    for k in ["sealed", "prospective", "formal", "none", "partial"]:
        M[f"InvBlind{k.title()}"] = int(ob.str.startswith(k).sum())
    M["InvBlindStrong"] = M["InvBlindSealed"] + M["InvBlindProspective"]
    M["InvVerifFormal"] = int(d.verification_formal.astype(bool).sum())
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


SHORT = {
    "astronomy-gwtc4-q-chieff-copula-stress-test": ("Astronomy", "Is the GWTC-4 mass-ratio--spin anticorrelation real?"),
    "bioinformatics-vep-acmg-calibration-drift": ("Bioinformatics", "Do ClinGen variant-predictor thresholds still hold?"),
    "climate-earth-record-margin-obs": ("Climate", "Are heat records broken by growing margins?"),
    "health-econ-wastewater-flusight-value": ("Health economics", "Does flu wastewater improve hospitalisation forecasts?"),
    "metascience-citation-context-replication": ("Metascience", "Does citing language predict replication outcomes?"),
    "climate-earth-ai-humid-heat-attribution": ("Climate", "Does moisture treatment change AI humid-heat attribution?"),
    "comp-social-science-temp-accounts-vandalism": ("Computational social science", "Did Wikipedia temporary accounts raise vandalism?"),
    "extra-open-neuroimaging-reanalysis-metaanalytic-prior-shrinkage": ("Neuroimaging", "Is shrinking small fMRI maps to a meta-analytic prior worth it?"),
    "llm-ml-science-mcf-emergence": ("ML science", "Does answer-letter mass predict multiple-choice format emergence?"),
    "cheminformatics-drug-discovery-cliff-noise-ceiling": ("Cheminformatics", "Are benchmark activity cliffs partly measurement noise?"),
    "auckland-nz-crl-structural-uplift-prereg": ("Transport (NZ)", "Is City Rail Link ridership uplift structural?"),
    "auckland-nz-speed-limit-reversal-crashes": ("Transport (NZ)", "Did reversing speed-limit cuts increase crashes?"),
    "auckland-nz-wastewater-testing-gap-deprivation": ("Public health (NZ)", "Is COVID-19 under-ascertainment greater in deprived towns?"),
    "auckland-nz-equity-adjustor-waitlist-did": ("Health policy (NZ)", "Did ending an ethnicity-inclusive waitlist score change waits?"),
    "ai-evaluation-science-swe-audit-concordance": ("AI evaluation", "Do independent audits of SWE-bench Verified agree?"),
    "auckland-nz-upzoning-canopy-lidar-did": ("Urban environment (NZ)", "Did Auckland's 2016 upzoning cost tree canopy?"),
    "seismology-geophysics-npp-gain-incompleteness-baseline": ("Seismology", "Do neural point processes beat ETAS only via incompleteness?"),
    "quantum-simulation-peaked-98q-classical-crack": ("Quantum simulation", "Can one GPU recover 98-qubit peaked-circuit answers?"),
    "formal-math-selfplay-vacuity-drift": ("Formal mathematics", "Do self-play provers drift toward vacuous conjectures?"),
}


def study_table():
    p = pd.read_csv(AUD / "portfolio.csv")
    inv = pd.read_csv(AUD / "inventory" / "plan_inventory_adjudicated.csv").set_index("run")
    a = pd.read_csv(AUD / "A_prereg_timing.csv").set_index("run")
    import subprocess
    order = []
    for r in p.run:
        out = subprocess.check_output(["git", "log", "--diff-filter=A", "--format=%ct", "--", f"research-lab/runs/{r}/plan.md"], cwd=LAB.parent, text=True).split()
        order.append(int(out[-1]))
    p["t"] = order
    p = p.sort_values("t")
    lines = [r"\begin{tabularx}{\textwidth}{@{}rl X l l l l@{}}", r"\toprule",
             r"\# & Field & Question & Verdict & Plan first & Blinding & Power \\", r"\midrule"]
    yn = {"yes": "yes", "no": "--", "partial": "partial"}
    for i, row in enumerate(p.itertuples(), 1):
        f, q = SHORT[row.run]
        pf = "yes" if a.loc[row.run, "passes"] else ("same commit$^\\dagger$" if row.run != "astronomy-gwtc4-q-chieff-copula-stress-test" else "\\textbf{no}")
        bl = inv.loc[row.run, "outcome_blinding"]
        bl = {"none": "--"}.get(bl, bl)
        pw = yn.get(str(inv.loc[row.run, "power"]).lower(), "?")
        v = row.verdict if row.verdict != "in progress" else "\\emph{in progress}"
        lines.append(f"{i} & {f} & {q} & {v} & {pf} & {bl} & {pw} \\\\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    (TAB / "studies.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    study_table()
