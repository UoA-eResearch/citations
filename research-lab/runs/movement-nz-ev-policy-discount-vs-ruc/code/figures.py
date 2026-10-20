"""Figures for the report (each PNG has a .txt caption).

  F1  monthly light-vehicle first registrations by powertrain, and the plug-in share, with the two policy dates
  F2  the treated series against its fitted baseline: the December 2023 excess and the 2024 shortfall (H1)
  F3  the difference-in-differences across 1 April 2024 against the hybrid control, with placebo years (H2)
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
CCD, RUC = "#eb6834", "#8a5cd1"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json"))
    rows = list(csv.DictReader(open(T / "monthly.csv")))
    mon = [r["month"] for r in rows]
    x = np.arange(len(mon))
    get = lambda k: np.array([float(r[k]) for r in rows])
    treated = get("BEV") + get("PHEV")
    hev, ice = get("HEV"), get("ICE")
    share = np.array([p["share_treated_pct"][m] for m in mon])
    ev_x = {m: i for i, m in enumerate(mon)}
    xc, xr = ev_x["2023-12"] + 0.5, ev_x["2024-03"] + 0.5

    def xticks(ax):
        ks = [i for i, m in enumerate(mon) if m.endswith("-01")]
        ax.set_xticks(ks); ax.set_xticklabels([mon[i][:4] for i in ks])

    # F1
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.6, 5.0), sharex=True)
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.09, top=0.86, hspace=0.18)
    for s, c, lb in ((ice, "#52514e", "petrol and diesel"), (hev, "#1baf7a", "hybrid (no plug)"),
                     (treated, "#2a78d6", "plug-in: battery-electric + plug-in hybrid")):
        a1.plot(x, s, "-", color=c, lw=1.9, label=lb)
    a1.set_yscale("log"); a1.set_ylabel("first registrations a month")
    a1.legend(frameon=False, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    a2.plot(x, share, "-", color="#2a78d6", lw=2)
    a2.set_ylabel("plug-in share of light\nregistrations, %")
    for ax in (a1, a2):
        ax.axvline(xc, color=CCD, lw=1.3, ls="--"); ax.axvline(xr, color=RUC, lw=1.3, ls=":")
        ax.grid(axis="y", color=GRID, lw=0.5)
    a2.annotate("Clean Car Discount\nends 31 Dec 2023", (xc, a2.get_ylim()[1]), xytext=(-84, -4),
                textcoords="offset points", fontsize=7.4, color=CCD, va="top")
    a2.annotate("road user charges\non EVs, 1 Apr 2024", (xr, a2.get_ylim()[1]), xytext=(8, -4),
                textcoords="offset points", fontsize=7.4, color=RUC, va="top")
    xticks(a2)
    fig.suptitle("New Zealand light-vehicle registrations across two policy changes", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_registrations.png", dpi=170); plt.close(fig)
    caption("F1_registrations", """First New Zealand registrations of light vehicles (passenger cars, vans and utilities)
    by powertrain, from NZTA's Motor Vehicle Register, January 2021 to September 2026. Upper panel on a log scale.
    Lower panel: plug-in vehicles as a share of all light registrations. Dashed line: the Clean Car Discount ends.
    Dotted line: road user charges begin for light electric and plug-in hybrid vehicles.""")

    # F2
    fig, ax = plt.subplots(figsize=(7.6, 3.6)); fig.subplots_adjust(left=0.1, right=0.97, bottom=0.14, top=0.84)
    ax.plot(x, treated, "-o", color="#2a78d6", lw=2, ms=3, label="plug-in registrations")
    i0, i1 = ev_x["2021-01"], ev_x["2023-09"]
    ax.axvspan(i0 - 0.5, i1 + 0.5, color=GRID, alpha=0.5, lw=0)
    ax.annotate("baseline fitted here\n(trend + month effects)", ((i0 + i1) / 2, treated.max() * 0.92),
                ha="center", fontsize=7.6, color=INK2)
    d = ev_x["2023-12"]
    ax.annotate(f"December 2023 excess\n{p['december_2023_excess']:,.0f} vehicles", (d, treated[d]),
                xytext=(-96, 6), textcoords="offset points", fontsize=7.6, color=CCD)
    q1 = [ev_x[f"2024-0{m}"] for m in (1, 2, 3)]
    ax.annotate(f"Jan-Mar 2024 shortfall\n{p['q1_2024_shortfall']:,.0f} vehicles", (q1[1], treated[q1[1]]),
                xytext=(10, 40), textcoords="offset points", fontsize=7.6, color=CCD,
                arrowprops=dict(arrowstyle="->", color=CCD, lw=0.9))
    ax.axvline(xc, color=CCD, lw=1.3, ls="--"); ax.axvline(xr, color=RUC, lw=1.3, ls=":")
    xticks(ax); ax.set_ylabel("plug-in first registrations a month"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle(f"Pull-forward explains little of the collapse (ratio {p['H1']['R']:.2f})", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F2_pullforward.png", dpi=170); plt.close(fig)
    caption("F2_pullforward", """Monthly plug-in first registrations. The shaded span is the window the baseline was
    fitted on (January 2021 to September 2023, a linear trend with calendar-month effects); the December 2023 excess
    and the January-March 2024 shortfall are measured against that baseline projected forward. H1 asked whether the
    excess offsets at least half the shortfall.""")

    # F3
    pl = list(csv.DictReader(open(T / "placebos.csv")))
    years = [2024] + [int(r["year"]) for r in pl]
    vals = [p["delta_ruc"]["pct"]] + [float(r["pct"]) for r in pl]
    cis = [[100 * (np.exp(v) - 1) for v in p["delta_ruc"]["ci"]]] + [[None, None]] * len(pl)
    order = sorted(range(len(years)), key=lambda i: years[i])
    fig, ax = plt.subplots(figsize=(7.8, 3.1)); fig.subplots_adjust(left=0.31, right=0.96, bottom=0.19, top=0.79)
    for k, i in enumerate(order):
        real = years[i] == 2024
        c = RUC if real else INK2
        if cis[i][0] is not None:
            ax.plot(cis[i], [k, k], color=c, lw=2.4)
        ax.plot(vals[i], k, "o", color=c, ms=8 if real else 6, mec=SURF, mew=1.2)
        ax.annotate(f"{vals[i]:+.0f}%", (vals[i], k), xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=7.6, color=INK2)
    ax.axvline(0, color=INK2, lw=0.9)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([("1 Apr 2024 (the real change)" if years[i] == 2024 else f"1 Apr {years[i]} (placebo)")
                        for i in order])
    ax.set_xlabel("plug-in registrations after April, relative to hybrids (%)")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("No road-user-charge effect stands out from ordinary variation", x=0.31, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F3_ruc_did.png", dpi=170); plt.close(fig)
    caption("F3_ruc_did", """Difference-in-differences: the change in plug-in registrations from January-March to
    May-October, minus the same change for non-plug hybrids, which were not moved to road user charges. April is
    excluded as a transition month. The 2024 estimate carries a block-bootstrap 95% interval; the placebo years use
    the identical windows on dates with no policy change.""")
    print("figures written")


if __name__ == "__main__":
    main()
