"""Figures (written before unsealing): (1) quarterly event study of the calibrated LLM fraction for DOT and the other
cabinet departments, 2019Q1-2026Q3, with the ChatGPT release and DOT's January 2026 announcement marked;
(2) validation: V1 estimate vs truth (documents construction) and V2 power curve. Writes results/figures/*.png."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
F = RUN / "results" / "figures"
COL = {"DOT": "#b5452c", "other_cabinet": "#2e5e8c"}
LAB = {"DOT": "Department of Transportation", "other_cabinet": "Other 14 cabinet departments"}


def qnum(q):
    y, k = q.split("Q")
    return int(y) + (int(k) - 1) / 4


def event_study():
    e = pd.read_csv(T / "event_study.csv")
    fig, ax = plt.subplots(figsize=(9, 3.8))
    for g, d in e.groupby("group"):
        x = d.quarter.map(qnum)
        ax.fill_between(x, 100 * d.lo, 100 * d.hi, color=COL[g], alpha=0.15, lw=0)
        ax.plot(x, 100 * d.alpha, "o-", color=COL[g], ms=3, lw=1.2, label=LAB[g])
    for xv, txt in [(2022 + 10.97 / 12, "ChatGPT\nrelease"), (2026.0, "DOT Gemini\nannouncement")]:
        ax.axvline(xv, color="grey", lw=0.8, ls="--")
        ax.text(xv + 0.05, ax.get_ylim()[1] * 0.9, txt, fontsize=7, color="grey", va="top")
    ax.axhline(0, color="black", lw=0.5)
    ax.set_ylabel("estimated LLM-assisted sentences (%)")
    ax.set_xlabel("quarter of publication (2019-2021 reference-pool documents excluded)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(F / "event_study.png", dpi=150)


def validation():
    v1 = pd.read_csv(T / "validation_v1.csv")
    v2 = pd.read_csv(T / "validation_v2.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    for c, m in (("documents", "o"), ("pseudo-documents", "s")):
        d = v1[v1.construction == c].groupby("alpha").agg(est=("est", "mean"), cov=("covered", "mean"))
        a1.plot(100 * d.index, 100 * d.est, m + "-", ms=4, lw=1, label=f"{c} (coverage {', '.join(f'{x:.0%}' for x in d['cov'])})")
    a1.plot([0, 25], [0, 25], color="grey", lw=0.8, ls=":")
    a1.set_xlabel("true LLM share in synthetic mixture (%)")
    a1.set_ylabel("mean calibrated estimate (%)")
    a1.legend(frameon=False, fontsize=6.5)
    p = v2.groupby("delta").detect.mean()
    a2.plot(100 * p.index, 100 * p.values, "o-", color="#2e5e8c", ms=4, label="real group sizes (D3)")
    if (T / "validation_v2_capped.csv").exists():
        pc = pd.read_csv(T / "validation_v2_capped.csv").groupby("delta").detect.mean()
        a2.plot(100 * pc.index, 100 * pc.values, "s--", color="#8a8a8a", ms=3.5, lw=1, label="groups capped at 320 documents")
    a2.legend(frameon=False, fontsize=7, loc="lower right")
    a2.axhline(80, color="grey", lw=0.8, ls=":")
    a2.axhline(5, color="grey", lw=0.8, ls=":")
    a2.set_xlabel("injected DiD (percentage points)")
    a2.set_ylabel("power: 95% CI excludes 0 (%)")
    fig.tight_layout()
    fig.savefig(F / "validation.png", dpi=150)


def departments():
    """D9 (post-review): calibrated alpha by cabinet department and DOT administration, 2024-25 vs Feb-Sep 2026."""
    d = pd.read_csv(T / "department_pre_post.csv").sort_values("n_pre", ascending=False)
    s = pd.read_csv(T / "dot_subagency_pre_post.csv")
    s = s[(s.n_pre >= 10) & (s.n_post >= 10)].sort_values("n_pre", ascending=False)
    short = {"Federal Aviation Administration": "FAA", "Pipeline and Hazardous Materials Safety Administration": "PHMSA",
             "Federal Railroad Administration": "FRA", "National Highway Traffic Safety Administration": "NHTSA",
             "Federal Motor Carrier Safety Administration": "FMCSA", "Office of the Secretary": "Office of the Secretary"}
    s["label"] = "DOT: " + s.subagency.map(short).fillna(s.subagency)
    d["label"] = d.department
    rows = pd.concat([d, s], ignore_index=True)
    ypos = list(range(len(d))) + [len(d) + 1 + k for k in range(len(s))]  # a gap before the DOT administrations
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(rows) + 1.4))
    for i, r in zip(ypos, rows.itertuples()):
        dot = r.label.startswith("DOT")
        for per, col, off in (("pre", "#9aa5b1", -0.15), ("post", "#b5452c" if dot else "#2e5e8c", 0.15)):
            a, lo, hi = getattr(r, f"alpha_{per}"), getattr(r, f"lo_{per}"), getattr(r, f"hi_{per}")
            ax.plot([100 * lo, 100 * hi], [i + off] * 2, color=col, lw=1.2)
            ax.plot(100 * a, i + off, "o", color=col, ms=4)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{r.label} ({int(r.n_pre)}/{int(r.n_post)})" for r in rows.itertuples()], fontsize=7.5)
    ax.invert_yaxis()
    ax.axvline(0, color="black", lw=0.5)
    ax.set_xlabel("estimated LLM-assisted sentences (%): grey 2024-2025, colour Feb-Sep 2026, with 95% CI")
    fig.subplots_adjust(left=0.3, right=0.98, top=0.98, bottom=0.07)
    fig.savefig(F / "departments.png", dpi=150)


def main():
    F.mkdir(parents=True, exist_ok=True)
    validation()
    if (T / "department_pre_post.csv").exists():
        departments()
    if (T / "event_study.csv").exists():
        event_study()


if __name__ == "__main__":
    main()
