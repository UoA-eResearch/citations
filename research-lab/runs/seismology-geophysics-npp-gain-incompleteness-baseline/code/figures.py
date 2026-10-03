"""Figure: test-period target-event temporal log-likelihood per event vs input cutoff, per sequence (S0, NPP, S2, A, B).
Output: results/figures/ll_vs_cutoff.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
rows = []
for f in sorted((RUN / "results" / "pointwise").glob("*.parquet")):
    cfg, cut = f.stem.rsplit("_", 1)
    if cfg == "synthetic":
        continue
    m = pd.read_parquet(f)[["S0", "NPP", "S2", "A", "B"]].mean()
    rows.append(dict(config=cfg, cutoff=float(cut), **m.to_dict()))
r = pd.DataFrame(rows)
r.to_csv(RUN / "results" / "tables" / "cutoff_sweep.csv", index=False)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
style = {"S0": ("#888888", "standard ETAS (published)", "--"), "S2": ("#bbbbbb", "standard ETAS (refit, full history)", ":"),
         "NPP": ("#d08a2c", "neural point process (published)", "-"), "A": ("#2f5d8a", "ETAS-I: rate-dependent detection (A)", "-"),
         "B": ("#7aa6c2", "time-varying completeness (B)", "-.")}
for ax, seq in zip(axes, ["Visso", "Norcia", "Campotosto"]):
    q = r[r.config == seq].sort_values("cutoff")
    for k, (col, lab, ls) in style.items():
        ax.plot(q.cutoff, q[k], ls, color=col, marker="o", ms=3.5, lw=1.6 if k in ("A", "NPP") else 1.1, label=lab)
    ax.set_title(seq, fontsize=10)
    ax.set_ylim(-2.0, 0.9)
    off = q[q.B < -2.0]
    for _, rr in off.iterrows():
        ax.annotate(f"B: {rr.B:.1f} (degenerate fit)", (rr.cutoff, -1.95), fontsize=6.5, ha="right", color="#7aa6c2")
    ax.set_xlabel("input magnitude cutoff")
axes[0].set_ylabel("target-event temporal log-likelihood\nper M>=3 event (test period)")
axes[0].legend(fontsize=7, frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(RUN / "results" / "figures" / "ll_vs_cutoff.png", dpi=150)
