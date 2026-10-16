"""Figures for the report. Each PNG gets a .txt caption beside it.

  F1  the shares as anomalies from their own 1980-2009 mean, so observed catch (~80-90%) and model
      biomass (~49%) share one axis without a second scale; the 2010 closure is marked
  F2  power to detect a decline, preregistered test and size-calibrated test, against SEAPODYM's rate
  F3  the 2010 step in each EEZ's share of domain catch, by whether the EEZ borders a closed pocket
  F4  the zonal centroid trend, observed and modelled

Palette: the dataviz skill's reference categorical slots 1-4, in fixed order, colour following the
entity; the model is also dashed, so identity never rests on colour alone. Text stays in neutral ink.
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
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def f1():
    obs = pd.read_csv(T / "observed_annual.csv", index_col=0)
    obs = obs[obs.convention == "sw"].loc[1980:2021]
    m = json.load(open(T / "model_targets.json"))
    hist = pd.Series({int(k): v for k, v in m["series"]["hist_share"].items()})
    proj = pd.Series({int(k): v for k, v in m["series"]["proj_share_mean"].items()}).loc[2011:2050]
    anom = lambda s, ref: 100 * (s - ref.loc[1980:2009].mean())
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    style(ax)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(2010, color=INK2, lw=0.8, ls=":")
    ax.text(2010.5, -10.5, "2010: high-seas pockets\nclosed to purse seiners", fontsize=8, color=INK2, va="top")
    series = [("catch share inside EEZs (O1, primary)", obs.skj_catch_share, BLUE, "-"),
              ("density share (O2)", obs.skj_density_share, ORANGE, "-"),
              ("fishing-days share", obs.days_eez_share, AQUA, "-")]
    for lab, s, c, ls in series:
        ax.plot(s.index, anom(s, s), color=c, lw=2, ls=ls, label=lab)
    both = pd.concat([hist, proj])
    ax.plot(hist.index, anom(hist, hist), color=YELLOW, lw=2, ls="--", label="SEAPODYM biomass share (hist, then 4-ESM mean)")
    ax.plot(proj.index, anom(proj, hist), color=YELLOW, lw=2, ls="--")
    ax.set_xlim(1979, 2051)
    ax.set_ylim(-16, 17)
    ax.set_ylabel("share inside the 12 EEZ areas,\npp from its own 1980-2009 mean")
    ax.set_title("Observed shares swing by up to 15 points and jump in 2010; SEAPODYM's projected fall begins later",
                 fontsize=10, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(F / "F1_shares.png", dpi=170)
    plt.close(fig)
    caption("F1_shares", """Share of skipjack inside the twelve EEZ areas of the ten Pacific SIDS in Bell et al.
    (2021), within the domain 20S-20N, 120E-228E, each shown as percentage points from its own 1980-2009 mean so
    that observed catch shares (about 81% before 2010) and modelled biomass shares (about 49%) share one axis.
    Solid lines are WCPFC public-domain purse-seine data: catch share (the preregistered primary series),
    density share (each fished cell weighted by catch per fishing day, which removes where the fleet is allowed
    to fish), and the share of fishing days. The dashed line is SEAPODYM skipjack biomass: the reanalysis-forced
    historical run to 2010, then the mean of the four ESM-forced RCP 8.5 projections. The dotted line marks the
    2010 closure of the high-seas pockets to purse seiners.""")


def f2():
    p = json.load(open(T / "primary.json"))
    e = json.load(open(T / "exploratory.json"))
    tau = abs(p["tau_pp"])
    pre = {float(k): v for k, v in p["H4_power"]["curve"].items()}
    cal = {float(k): v for k, v in e["calibrated_power"]["curve"].items()}
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    style(ax)
    ax.plot(list(pre), list(pre.values()), color=BLUE, lw=2, label="preregistered test (actual size 14%)")
    ax.plot(list(cal), list(cal.values()), color=ORANGE, lw=2, label="size-calibrated test (size 5%)")
    ax.axhline(0.8, color=INK2, lw=0.8, ls=":")
    ax.axvline(tau, color=INK2, lw=0.8)
    ax.text(tau + 0.01, 0.04, f"SEAPODYM's projected\nrate, {tau:.3f} pp/yr", fontsize=8, color=INK2)
    ax.text(0.99, 0.81, "80% power", fontsize=8, color=INK2, ha="right", va="bottom", transform=ax.get_yaxis_transform())
    ax.set_xlim(0, 0.8)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("injected decline in the EEZ catch share (pp per year)")
    ax.set_ylabel("share of simulations detecting it")
    ax.set_title("42 years of catch data cannot detect a decline at the projected rate", fontsize=10, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="center right", labelcolor=INK)
    fig.tight_layout()
    fig.savefig(F / "F2_power.png", dpi=170)
    plt.close(fig)
    caption("F2_power", f"""Injection-recovery power for a linear decline in the primary series (EEZ catch share,
    1980-2021): the fitted trend is removed, a known decline added, block-resampled residuals re-added, and the
    same ENSO-adjusted estimator re-fitted. The preregistered one-sided HAC test fires in 14% of simulations
    with no decline injected, against a nominal 5%, so its curve overstates power; the size-calibrated curve
    takes its critical value from those null simulations. The vertical line is SEAPODYM's projected 2011-2050
    rate of change in the identical share ({tau:.3f} pp/yr), the dotted line 80% power.""")


SHORT = {"Micronesian Exclusive Economic Zone": "FSM", "Palauan Exclusive Economic Zone": "Palau",
         "Papua New Guinean Exclusive Economic Zone": "Papua New Guinea",
         "Solomon Islands Exclusive Economic Zone": "Solomon Islands", "Nauruan Exclusive Economic Zone": "Nauru",
         "Marshallese Exclusive Economic Zone": "Marshall Islands", "Tuvaluan Exclusive Economic Zone": "Tuvalu",
         "Kiribati Exclusive Economic Zone (Gilbert Islands)": "Kiribati (Gilbert)",
         "Kiribati Exclusive Economic Zone (Phoenix Group)": "Kiribati (Phoenix)",
         "Kiribati Exclusive Economic Zone (Line Group)": "Kiribati (Line)",
         "New Zealand Exclusive Economic Zone (Tokelau)": "Tokelau",
         "New Zealand Exclusive Economic Zone (Cook Islands)": "Cook Islands"}


def f3():
    e = json.load(open(T / "exploratory.json"))
    t = pd.DataFrame(e["per_eez"]).sort_values("step_pp")
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    y = np.arange(len(t))
    cols = [BLUE if a else ORANGE for a in t.pocket_adjacent]
    ax.hlines(y, t.step_lo, t.step_hi, color=cols, lw=1.4)
    ax.scatter(t.step_pp, y, color=cols, s=36, zorder=3, edgecolor=SURF, linewidth=1.2)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([SHORT.get(n, n) for n in t.eez], color=INK)
    ax.set_xlabel("ENSO-adjusted step in the EEZ's share of domain skipjack catch at 2010 (pp, HAC 95%)")
    ax.scatter([], [], color=BLUE, s=36, label="borders a high-seas pocket closed in 2010")
    ax.scatter([], [], color=ORANGE, s=36, label="does not border one")
    ax.legend(frameon=False, fontsize=8, loc="lower right", labelcolor=INK)
    ax.set_title("The 2010 step by EEZ: no clean pattern by pocket, and PNG's step is barely identified",
                 fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(F / "F3_per_eez_step.png", dpi=170)
    plt.close(fig)
    caption("F3_per_eez_step", """The 2010 step in each EEZ area's share of skipjack purse-seine catch in the domain,
    from a regression of the annual share on a linear trend, Nino 3.4 (current and lagged), the warm-pool edge and a
    2010 step, with Newey-West (3-lag) 95% intervals. Colour marks whether the EEZ borders one of the two high-seas
    pockets closed to purse seiners from 2010; the grouping was fixed in deviations.md D5 before this was computed.
    Shares are catch shares only and say nothing about revenue.""")


def f4():
    e = json.load(open(T / "exploratory.json"))
    fp = json.load(open(T / "footprint.json"))["min_frac_0.8"]
    c = e["centroid_deg_per_yr"]
    cv = fp["centroid_trend_covered_years"]
    rows = [("observed catch, all fished cells", c["obs_catch_1980_2021"], BLUE),
            ("observed density, all fished cells", c["obs_density_1980_2021"], ORANGE),
            ("density, fixed core grounds, 1980-2021", fp["centroid_trend_deg_per_yr"], ORANGE),
            (f"density, fixed core, covered years {cv['years'][0]}-{cv['years'][1]}", cv, ORANGE),
            ("SEAPODYM historical, 1980-2010", c["model_hist_1980_2010"], YELLOW)]
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for i, (lab, v, col) in enumerate(rows):
        ax.hlines(i, v["lo"], v["hi"], color=col, lw=1.6)
        ax.scatter(v["point"], i, color=col, s=40, zorder=3, edgecolor=SURF, linewidth=1.2)
    pr = c["model_proj_2011_2050_deg_per_yr"]
    ax.scatter(pr, len(rows), color=YELLOW, s=40, marker="D", zorder=3, edgecolor=SURF, linewidth=1.2)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(range(len(rows) + 1))
    ax.set_yticklabels([r[0] for r in rows] + ["SEAPODYM projected, 2011-2050"], color=INK)
    ax.invert_yaxis()
    ax.set_xlabel("ENSO-adjusted centroid trend (degrees east per year)")
    ax.set_title("On fixed grounds, the eastward move vanishes", fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(F / "F4_centroid.png", dpi=170)
    plt.close(fig)
    caption("F4_centroid", """Trend in the mean longitude of skipjack within the domain. The top two rows use every cell fished that year, weighted by observed
    catch and by observed density (catch per fishing day times cell area); the next two restrict density to a
    fixed set of 86 core cells (141.5-159.5E) fished in at least 80% of years, first over all years and then
    over the 31 years in which those cells were actually covered (deviations D6, D7). Each is ENSO-adjusted with a
    95% block-bootstrap interval. The SEAPODYM rows use modelled biomass; the projected value is the four-ESM
    mean linear trend for 2011-2050 and has no interval. A centroid over fished cells moves east whenever the
    fishery opens new eastern grounds, so only the fixed-footprint rows speak to where the fish are.""")


if __name__ == "__main__":
    F.mkdir(parents=True, exist_ok=True)
    f1(); f2(); f3(); f4()
    print("figures written:", sorted(p.name for p in F.glob("*.png")))
