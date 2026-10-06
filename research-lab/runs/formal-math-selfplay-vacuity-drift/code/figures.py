"""Figure: per-iteration certified-vacuity rate (Wilson 95% CI) for conjecture rows, with the statement-tag control
and phase boundaries. Writes results/figures/vacuity_by_iteration.png."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    p = pd.read_csv(T / "per_iteration.csv")
    s = pd.read_csv(T / "statement_per_iteration.csv")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for lo, hi in [(1, 23), (25, 47)]:
        q = p[(p.iteration >= lo) & (p.iteration <= hi)]
        ax.fill_between(q.iteration, 100 * q.lo, 100 * q.hi, color="#2b6c8f", alpha=0.18, lw=0)
        ax.plot(q.iteration, 100 * q.rate, "o-", color="#2b6c8f", ms=3, lw=1.2, label="conjectures" if lo == 1 else None)
        r = s[(s.iteration >= lo - 1) & (s.iteration <= hi)]
        ax.plot(r.iteration, 100 * r.rate, "s", color="#c9a14a", ms=3, label="LeanWorkbook statements (control)" if lo == 1 else None)
    for x in (0, 24):
        ax.axvline(x, color="grey", lw=0.8, ls="--")
    ax.text(0.5, ax.get_ylim()[1] * 0.92, "self-play\nrestart", fontsize=7, color="grey")
    ax.text(24.5, ax.get_ylim()[1] * 0.92, "restart from\nre-trained model", fontsize=7, color="grey")
    ax.axvspan(1, 9, color="#999", alpha=0.08)
    ax.axvspan(38, 47, color="#999", alpha=0.08)
    ax.set_xlabel("STP self-play iteration (shaded: preregistered early 1-9 and late 38-47 windows)")
    ax.set_ylabel("certified vacuous (%)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    (RUN / "results" / "figures").mkdir(exist_ok=True, parents=True)
    fig.savefig(RUN / "results" / "figures" / "vacuity_by_iteration.png", dpi=150)


if __name__ == "__main__":
    main()
