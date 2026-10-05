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
    L = [l for l in json.load(open(LAB / "leads.json"))["leads"] if not l.get("meta")]  # the meta-study entry is not a scouted lead
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
    ok = a[a.passes & a.hours_plan_to_first_output.notna()]
    M["PreregMedianHours"] = f"{ok.hours_plan_to_first_output.median():.1f}"
    M["PreregMinHours"] = f"{ok.hours_plan_to_first_output.min():.2f}"
    M["PreregMaxHours"] = f"{ok.hours_plan_to_first_output.max():.1f}"
    M["PreregUnderHour"] = int((ok.hours_plan_to_first_output < 1).sum())
    M["PreregPassN"] = len(ok)
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
    # exclude the correction entry created by this audit after coding began (audit deviations A9)
    a = a[~((a.run == "llm-ml-science-mcf-emergence") & (a.entry_id.astype(str).str.strip() == "U1"))]
    rep = {p.name for p in (LAB / "runs").iterdir() if (p / "report.md").exists()}
    a, b = a[a.run.isin(rep)], b[b.run.isin(rep)]
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
    final = final[final.run.isin(rep)]
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
    tl = {"T1": "executor", "T2": "validation check", "T3": "independent reviewer"}
    ct = pd.crosstab(final.category.astype(str).str[:2], final.trigger.astype(str).str[:2]).reindex(index=list(lab), columns=list(tl), fill_value=0)
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    left = np.zeros(len(ct))
    cols = ["#2b6c8f", "#7fb069", "#c9a14a"]
    for t, col in zip(ct.columns, cols):
        ax.barh([lab[c] for c in ct.index], ct[t], left=left, color=col, label=tl[t])
        left += ct[t].values
    ax.invert_yaxis()
    ax.set_xlabel("number of logged deviations (no entry was triggered by an external event)")
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
    lit = rec.str.contains("fix first|fix-first") & ~rec.str.contains("refuted")
    M["ReviewFixFirst"] = int(lit.sum())
    M["ReviewRefutedRec"] = int(rec.str.contains("refuted").sum())
    M["ReviewPublishEdits"] = int(rec.str.contains("publish with edits").sum() - (rec.str.contains("publish with edits") & lit).sum())
    conf = final.confirmation_pass.astype(str).str.lower().str.strip() == "yes"
    M["ReviewConfAmongFix"] = int((conf & (lit | rec.str.contains("refuted"))).sum())
    M["ReviewFixOrRefuted"] = int((lit | rec.str.contains("refuted")).sum())
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


def untraced():
    a, b = AUD / "coder_A" / "D_untraced_classified.csv", AUD / "coder_B" / "D_untraced_classified.csv"
    if not (a.exists() and b.exists()):
        return
    a, b = pd.read_csv(a), pd.read_csv(b)
    m = a.merge(b, on="sample_id", suffixes=("_A", "_B"))
    ca = m.class_A.str.extract(r"(U\d)")[0]
    cb = m.class_B.str.extract(r"(U\d)")[0]
    M["UntracedN"] = len(m)
    M["UntracedKappa"] = f"{cohen_kappa_score(ca, cb):.2f}"
    M["UntracedUFourBoth"] = int(((ca == "U4") & (cb == "U4")).sum())
    M["UntracedUFiveAny"] = int(((ca == "U5") | (cb == "U5")).sum())
    M["UntracedUTwo"] = int(((ca == "U2") & (cb == "U2")).sum())
    M["UntracedOneThree"] = int((ca.isin(["U1", "U3"]) & cb.isin(["U1", "U3"])).sum())
    M["UntracedOneThreeDisagree"] = int((ca.isin(["U1", "U3"]) & cb.isin(["U1", "U3"]) & (ca != cb)).sum())
    M["UntracedSectionRefs"] = int(m.note_A.astype(str).str.contains("section cross-reference", case=False).sum())
    text = r"""\paragraph{Untraced numbers.} Both coders classified a seeded sample of \UntracedN{} untraced substantive numbers
(up to 10 per report; drawn before the matcher fix in \texttt{audit/deviations.md}~A8).
\begin{itemize}
\item \textbf{Inconsistent with the results:} \UntracedUFiveAny{}. Neither coder found any.
\item \textbf{Untraceable:} \UntracedUFourBoth{}, the same three for both coders. All three are numbers the
independent reviewer computed in its own scratch code and that were never saved: two canopy percentages from a
point-density thinning check, and a likelihood re-integration tolerance.
\item \textbf{From cited literature or data documentation:} \UntracedUTwo{}.
\item \textbf{Legitimately sourced:} the remaining \UntracedOneThree{} were arithmetic on traced numbers, design
parameters or sample counts. The coders differed only on which of these two classes \UntracedOneThreeDisagree{}
belonged to ($\kappa=\UntracedKappa{}$ overall).
\end{itemize}

Outside the sample, coder~A found one real error while recomputing a range. A report printed ``$-1.3$ to $+1.5$''
where the data give $-1.25$ to $+1.449$, so the upper end had been rounded twice. The report has been corrected.
"""
    (PAPER / "numbers_untraced.tex").write_text(text)


if __name__ == "__main__":
    untraced()
    write()


def ci(k, n):
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.0f}\\%; 95\\% CI {100 * lo:.0f}--{100 * hi:.0f}\\%"


def revisions():
    """Numbers added in response to the independent review (paper/review/review.md)."""
    import re
    import subprocess
    rep = sorted(p.name for p in (LAB / "runs").iterdir() if (p / "report.md").exists())
    G = "astronomy-gwtc4-q-chieff-copula-stress-test"
    # Wilson intervals for verdict shares
    M["CISupported"] = ci(M["VerdictSupported"], M["VerdictsDecided"])
    M["CIInconclusive"] = ci(M["VerdictInconclusive"], M["VerdictsDecided"])
    M["CINotSupported"] = ci(M["VerdictsDecided"] - M["VerdictSupported"], M["VerdictsDecided"])
    M["CIPreregClassified"] = ci(M["PreregPassClassified"], M["StudiesTotal"])
    # push events: lag between plan commit time and server-side push
    ev = AUD / "github_push_events_2026-10-06.json"
    if ev.exists():
        evs = json.load(open(ev))
        evs = evs if isinstance(evs, list) else evs.get("events", [])
        pushes = []
        for e in evs:
            if e.get("type") != "PushEvent":
                continue
            t = pd.Timestamp(e["created_at"])
            pl = e.get("payload", {})
            shas = [c.get("sha") for c in pl.get("commits", []) or []] + [pl.get("head"), pl.get("before")]
            pushes.append((t, [x for x in shas if x]))
        a = pd.read_csv(AUD / "A_prereg_timing.csv")
        rw = pd.read_csv(AUD / "A_rewrite_map.csv") if (AUD / "A_rewrite_map.csv").exists() else pd.DataFrame(columns=["original_sha", "current_sha"])
        orig = dict(zip(rw.current_sha, rw.original_sha))
        lags = []
        for r in a.itertuples():
            full = subprocess.check_output(["git", "rev-parse", r.plan_commit], cwd=LAB.parent, text=True).strip()
            ct = pd.Timestamp(int(r.t_plan), unit="s", tz="UTC")
            ids = [full] + ([orig[full]] if full in orig else [])  # rewritten commits are matched through their originals
            cand = []
            for t, shas in sorted(pushes):
                head = shas[0] if shas else None
                if t >= ct and head and any(subprocess.run(["git", "merge-base", "--is-ancestor", i, head], cwd=LAB.parent,
                                                           capture_output=True).returncode == 0 for i in ids):
                    cand = [t]
                    break
            if cand:
                lags.append(dict(run=r.run, plan_commit=r.plan_commit, lag_min=(min(cand) - ct).total_seconds() / 60,
                                 pushed_before_first_output=bool(pd.isna(r.t_out) or min(cand).timestamp() < r.t_out)))
        L = pd.DataFrame(lags)
        L.to_csv(AUD / "A_push_lag.csv", index=False)
        M["PushMatched"] = len(L)
        M["PushMaxLagMin"] = f"{L.lag_min.max():.1f}" if len(L) else "--"
        M["PushBeforeOutput"] = int(L.pushed_before_first_output.sum()) if len(L) else 0
    # deviations with and without GWTC-4
    f = pd.read_csv(AUD / "adjudicated_B.csv")
    f = f[f.run.isin(rep)]
    for tag, d in (("", f), ("NoG", f[f.run != G])):
        vr = d.verdict_relevance.astype(str).str.lower().str.strip() == "yes"
        aft = d.timing.astype(str).str.lower().str.strip() == "after"
        trig = d.trigger.astype(str).str[:2].str.upper()
        M[f"DevN{tag}"] = len(d)
        M[f"DevRelevant{tag}"] = int(vr.sum())
        M[f"DevRelevantAfter{tag}"] = int((vr & aft).sum())
        M[f"DevRelevantAfterExec{tag}"] = int((vr & aft & (trig == "T1")).sum())
        M[f"DevRelevantAfterValRev{tag}"] = int((vr & aft & trig.isin(["T2", "T3"])).sum())
        M[f"DevAfterNotReviewer{tag}"] = int((aft & (trig != "T3")).sum())
        M[f"CIDevRelevant{tag}"] = ci(int(vr.sum()), len(d))
    M["DevGWTC"] = int((f.run == G).sum())
    M["DevRelevantAfterGWTC"] = M["DevRelevantAfter"] - M["DevRelevantAfterNoG"]
    g = f[(f.run == G) & (f.verdict_relevance.astype(str).str.lower() == "yes") & (f.timing.astype(str).str.lower() == "after") & (f.trigger.astype(str).str[:2].str.upper() == "T1")]
    M["GWTCExecAfterIDs"] = ", ".join(g.entry_id.astype(str))
    M["DevAfterReviewer"] = int(((f.timing.astype(str).str.lower() == "after") & (f.trigger.astype(str).str[:2].str.upper() == "T3")).sum())
    # measure C: coder A, coder B, either
    ca, cb = pd.read_csv(AUD / "coder_A" / "C_review.csv"), pd.read_csv(AUD / "coder_B" / "C_review.csv")
    m = ca.merge(cb, on="run", suffixes=("_A", "_B"))
    for col, key in (("headline_changed", "Headline"), ("verdict_changed", "Verdict")):
        ya = m[f"{col}_A"].astype(str).str.lower().str.strip() == "yes"
        yb = m[f"{col}_B"].astype(str).str.lower().str.strip() == "yes"
        M[f"C{key}A"], M[f"C{key}B"], M[f"C{key}Either"] = int(ya.sum()), int(yb.sum()), int((ya | yb).sum())
    # protocol compliance counts measured from the run directories
    rv = sum(1 for r in rep if re.search(r"(?i)fable", (LAB / "runs" / r / "deviations.md").read_text()))
    M["ReviewerModelRecorded"] = rv
    M["ReviewSections"] = sum(1 for r in rep if re.search(r"(?im)^#+\s*(independent )?review", (LAB / "runs" / r / "report.md").read_text()))
    words = []
    for r in rep:
        t = (LAB / "runs" / r / "report.md").read_text()
        mm = re.search(r"(?ims)^##\s*In plain terms\s*$(.*?)(?=^##\s)", t)
        if mm:
            words.append(len(re.findall(r"\b\w[\w'’-]*\b", mm.group(1))))
    M["PlainWordsMin"], M["PlainWordsMax"], M["PlainN"] = min(words), max(words), len(words)
    gd = (LAB / "runs" / G / "deviations.md").read_text()
    heads = re.findall(r"(?m)^#{2,4}\s.*$", gd)
    M["GWTCHeaders"] = len(heads)
    M["GWTCHeadersNoTime"] = sum(1 for h in heads if not re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", h))
    # effort
    e = pd.read_csv(AUD / "F_effort.csv")
    M["EffortActiveHoursTotal"] = f"{e.active_hours.sum():.0f}"
    M["GWTCSpanDays"] = f"{e.set_index('run').loc[G, 'span_days']:.0f}"
    # number tracing (perturbation null) and the verification sample
    pz = pd.read_csv(AUD / "D_numbers_perturbation_detail.csv")
    for src, key in (("results only", "R"), ("results+plan+deviations", "All")):
        h = pz[pz.sources == src]
        o, c = h.own.mean(), h.chance.mean()
        M[f"Trace{key}Own"], M[f"Trace{key}Chance"] = pct(o, 0), pct(c, 0)
        h3 = h[h.sig == 3]
        M[f"Trace{key}OwnThree"], M[f"Trace{key}ChanceThree"] = pct(h3.own.mean(), 0), pct(h3.chance.mean(), 0)
    s = pd.read_csv(AUD / "D_numbers_summary.csv")
    # untraced 5+ significant-figure numbers, by study
    det = pd.read_csv(AUD / "D_numbers_sig_detail.csv")
    u5 = det[(det.sig >= 5) & (~det.own.astype(bool))]
    M["UntracedFivePlus"] = len(u5)
    M["UntracedFivePlusTop"] = u5.run.value_counts().index[0] if len(u5) else ""
    M["UntracedFivePlusTopN"] = int(u5.run.value_counts().iloc[0]) if len(u5) else 0
    smp = pd.read_csv(AUD / "D_sample_untraced_v1.csv")  # the 85-number sample the coders classified
    M["SampleReportsTen"] = int((smp.run.value_counts() == 10).sum())
    M["SampleReports"] = smp.run.nunique()


if __name__ == "__main__":
    revisions()
    write()


def revisions2():
    import re
    L = pd.read_csv(AUD / "A_push_lag.csv")
    M["PushUnderMinute"] = int((L.lag_min < 1).sum())
    M["PushMaxLagSec"] = f"{L.lag_min.max() * 60:.0f}"
    rw = pd.read_csv(AUD / "A_rewrite_map.csv")
    M["RewrittenCommits"] = len(rw)
    M["RewrittenAllIdentical"] = "yes" if (rw.tree_identical & rw.committer_date_identical).all() else "no"
    a = pd.read_csv(AUD / "A_prereg_timing.csv").set_index("run")
    strict = L[L.run.map(a.passes)]
    M["PushStrictBeforeOutput"] = int(strict.pushed_before_first_output.sum())
    M["PushStrictN"] = len(strict)
    # coders' classification of the four same-commit cases
    fa, fb = AUD / "coder_A" / "A_same_commit.csv", AUD / "coder_B" / "A_same_commit.csv"
    if fa.exists() and fb.exists():
        va = pd.read_csv(fa).query("file == 'VERDICT'").set_index("run")["class"].str.lower()
        vb = pd.read_csv(fb).query("file == 'VERDICT'").set_index("run")["class"].str.lower()
        both_pre = [r for r in va.index if "pre-outcome only" in va[r] and "pre-outcome only" in vb.get(r, "")]
        M["SameCommitPreBoth"] = len(both_pre)
        M["SameCommitAgree"] = int(sum((("pre-outcome only" in va[r]) == ("pre-outcome only" in vb.get(r, ""))) for r in va.index))
    # direct verification sample
    da, db = AUD / "coder_A" / "D_verify.csv", AUD / "coder_B" / "D_verify.csv"
    if da.exists() and db.exists():
        x, y = pd.read_csv(da), pd.read_csv(db)
        m = x.merge(y, on="verify_id", suffixes=("_A", "_B"))
        ca = m.class_A.astype(str).str.extract(r"(V\d)")[0]
        cb = m.class_B.astype(str).str.extract(r"(V\d)")[0]
        M["VerifyN"] = len(m)
        M["VerifyKappa"] = f"{cohen_kappa_score(ca, cb):.2f}"
        ok = lambda c: c.isin(["V1", "V2", "V3"])  # noqa: E731
        M["VerifyOKA"], M["VerifyOKB"] = int(ok(ca).sum()), int(ok(cb).sum())
        M["VerifyOKBoth"] = int((ok(ca) & ok(cb)).sum())
        M["VerifyCIOKBoth"] = ci(int((ok(ca) & ok(cb)).sum()), len(m))
        M["VerifyFourA"], M["VerifyFourB"] = int((ca == "V4").sum()), int((cb == "V4").sum())
        M["VerifyFourEither"] = int(((ca == "V4") | (cb == "V4")).sum())
        M["VerifyFiveA"], M["VerifyFiveB"] = int((ca == "V5").sum()), int((cb == "V5").sum())
        M["VerifyFiveEither"] = int(((ca == "V5") | (cb == "V5")).sum())
        M["VerifyOneA"], M["VerifyOneB"] = int((ca == "V1").sum()), int((cb == "V1").sum())
        prob = m[(ca.isin(["V4", "V5"])) | (cb.isin(["V4", "V5"]))]
        prob[["verify_id", "run_A", "token_A", "class_A", "class_B", "located_value_A", "located_value_B", "note_A", "note_B"]].to_csv(AUD / "D_verify_problems.csv", index=False)
    # bibliography of this paper through measure E
    bib = (PAPER / "references.bib").read_text()
    arx = sorted(set(re.findall(r"arXiv:(\d{4}\.\d{4,5})", bib)))
    dois = sorted(set(re.findall(r"doi[:\s]*(10\.\d{4,9}/[^\s},;]+)", bib)))
    M["BibArxiv"], M["BibDoi"] = len(arx), len(dois)
    port = pd.read_csv(AUD / "portfolio.csv")
    rp = port[port.verdict != "in progress"]
    M["ValueMin"], M["ValueMax"] = int(rp.value.min()), int(rp.value.max())
    M["CostMin"], M["CostMax"] = int(rp.cost.min()), int(rp.cost.max())
    # Figure 2 (revised): own vs size-matched chance (perturbation null), results/ only
    g = pd.read_csv(AUD / "D_numbers_perturbation_by_sig.csv")
    g = g[g.sources == "results only"].set_index("sig")
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    x = np.arange(len(g))
    ax.bar(x - 0.2, g.traced_own, 0.4, label="printed value", color="#2b6c8f")
    ax.bar(x + 0.2, g.traced_chance, 0.4, label="value shifted 3-7 units in last digit", color="#c9a14a")
    ax.set_xticks(x, [f"{i}{'+' if i == 5 else ''}\n(n={int(n)})" for i, n in zip(g.index, g.n)])
    ax.set_xlabel("significant figures printed in the report")
    ax.set_ylabel("share matching a value\nin the study's results/")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "number_tracing.pdf")
    plt.close(fig)


if __name__ == "__main__":
    revisions2()
    write()
