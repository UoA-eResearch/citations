"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  curtailment by 12-month window, split into the noise mass built into the preregistered rule and the rest
  F2  each plant's detection floor relative to its mean potential in 2025/26, against the 25% measurability gate
  F3  monthly price-driven curtailment (node price at or below the plant's own offer), with available energy
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
NOISE, PRICE, OTHER = "#b8b6ae", "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    dg = json.load(open(T / "diagnostics.json"))
    p = json.load(open(T / "primary.json"))

    # F1: windows, primary share split into noise and price-driven + rest
    w = dg["by_12_month_window"]
    labels = list(w)
    prim = np.array([w[k]["primary_share"] for k in labels]) * 100
    price = np.array([w[k]["price_driven_share"] for k in labels]) * 100
    # the unconstrained (noise) mass is known exactly for the two hypothesis periods; for the others it is the
    # primary share minus price-driven minus a rest we do not split, so the figure shows price-driven against the rest
    rest = prim - price
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.2, top=0.84)
    ax.bar(x, price, color=PRICE, width=0.62, label="at or below the plant's own offer price (price-driven)")
    ax.bar(x, rest, bottom=price, color=NOISE, width=0.62, label="all other flagged periods (mostly forecast noise)")
    for i in range(len(x)):
        ax.text(x[i], prim[i] + 0.1, f"{prim[i]:.1f}%", ha="center", fontsize=7.5, color=INK2)
        if price[i] >= 0.4:
            ax.text(x[i], price[i] / 2, f"{price[i]:.1f}%", ha="center", va="center", fontsize=7.5, color=SURF)
    ax.set_xticks(x); ax.set_xticklabels([k.replace("..", " to\n") for k in labels], fontsize=7.5)
    ax.set_ylabel("curtailed share of available energy, %"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.6, loc="upper left")
    fig.suptitle("The preregistered measure has a floor of about 2%; price-driven curtailment grew from almost nil",
                 x=0.09, ha="left", fontsize=9.8, color=INK)
    fig.savefig(F / "F1_windows.png", dpi=170); plt.close(fig)
    caption("F1_windows", """Curtailed energy as a share of available (bias-corrected potential) energy for New Zealand's
    offered wind and solar plants, by 12-month window (the first window is January 2020 to June 2021). The full bar
    is the preregistered measure. Its grey part includes the mass that the rule flags by construction in unconstrained
    periods (about 5% of them), which is forecast error rather than curtailment. The blue part is curtailment in
    periods whose node price was at or below the plant's own offer price.""")

    # F2: gate per plant
    g = pd.Series(p["gate_by_poc"]).dropna().sort_values()
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.2, top=0.86)
    cols = ["#2a78d6" if v <= 0.25 else "#b8b6ae" for v in g.values]
    ax.bar(np.arange(len(g)), g.values * 100, color=cols, width=0.7)
    ax.axhline(25, color=INK, lw=1, ls="--")
    ax.axhline(g.median() * 100, color="#eb6834", lw=1.2)
    ax.text(len(g) - 0.5, 25 + 2, "measurability gate, 25%", ha="right", fontsize=7.5, color=INK)
    ax.text(0, g.median() * 100 + 2, f"median {g.median() * 100:.0f}%", fontsize=7.5, color="#eb6834")
    ax.set_xticks(np.arange(len(g))); ax.set_xticklabels(g.index, rotation=70, fontsize=7)
    ax.set_ylabel("detection floor / mean potential, %"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Forecast error is large next to the curtailment it must reveal (2025/26)", x=0.12, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F2_gate.png", dpi=170); plt.close(fig)
    caption("F2_gate", """For each plant (point of connection), the detection floor, the 95th percentile of the gap
    between bias-corrected potential and metered output in unconstrained periods, divided by the plant's mean
    potential, July 2025 to June 2026. The plan set a gate: if the median exceeds 25%, curtailment is not reliably
    measurable from offers alone. Solar plants sit high partly because their mean potential includes nights.""")

    # F3: monthly price-driven curtailment from the ledger
    led = pd.read_csv(T / "ledger_monthly.csv")
    m = led.groupby("month")[["available_mwh", "curtailed_price-driven_mwh"]].sum()
    m.index = pd.PeriodIndex(m.index, freq="M").to_timestamp()
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.13, top=0.85)
    ax.bar(m.index, m["curtailed_price-driven_mwh"] / 1000, width=25, color=PRICE)
    ax.set_ylabel("price-driven curtailment, GWh a month"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Price-driven curtailment comes in spells; the largest were in 2022 and 2025/26", x=0.09, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F3_monthly_price_driven.png", dpi=170); plt.close(fig)
    caption("F3_monthly_price_driven", """Monthly curtailed energy, in periods when the plant's node price was at or
    below its own offer price, summed over New Zealand's offered wind and solar plants (calibration by plant and
    quarter over the whole panel, so monthly values differ slightly from the 12-month figures).""")
    print("figures written")


if __name__ == "__main__":
    main()
