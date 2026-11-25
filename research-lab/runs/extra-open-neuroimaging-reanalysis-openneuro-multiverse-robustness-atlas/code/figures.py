"""Report figures and key-result tiles.

  figures.py -> results/figures/robustness_vs_n.png (+ .txt caption), results/figures/which_choice.png (+ .txt),
                results/tables/tiles.json
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
atlas = pd.read_csv(T / "atlas.csv")
primary = json.loads((T / "primary.json").read_text())
ext = json.loads((T / "external_fitlins.json").read_text())

# 1. R against N, coloured by the median suprathreshold extent
d = atlas.dropna(subset=["R"]).copy()
fig, ax = plt.subplots(figsize=(7, 4.6))
sc = ax.scatter(d.N, d.R, c=np.log10(d.supra_median + 1), cmap="viridis", s=55, edgecolor="k", linewidth=0.5)
for r in d.itertuples():
    ax.annotate(r.ds.replace("ds0", "").lstrip("0"), (r.N, r.R), fontsize=7, xytext=(4, 2), textcoords="offset points")
ax.axvline(25, color="grey", ls=":", lw=1)
ax.text(25.5, 0.02, "N = 25 (H2)", fontsize=8, color="grey")
ax.set_xscale("log")
ax.set_xlabel("Analysed subjects (log scale)")
ax.set_ylabel("Robustness R (mean pairwise signed Dice)")
ax.set_ylim(-0.03, 1)
cb = fig.colorbar(sc, ax=ax)
cb.set_label("log10 (median suprathreshold voxels + 1)")
fig.tight_layout()
fig.savefig(FIG / "robustness_vs_n.png", dpi=150)
sp = lambda c: d[["R", c]].corr("spearman").iloc[0, 1]  # noqa: E731
(FIG / "robustness_vs_n.txt").write_text(
    f"Robustness R against the number of analysed subjects for the {len(d)} datasets where R is defined (labels: "
    "dataset number). Colour: the median number of suprathreshold voxels over the 48 configurations. R follows how "
    f"much of the brain passes the threshold (Spearman {sp('supra_median'):.2f}, post hoc, and largely built into "
    f"Dice and the empty-map rule) more than N ({sp('N'):.2f}) or tSNR ({sp('tsnr'):.2f}).")

# 2. which choice matters: per-dataset Dice between configurations that differ on one axis only
# D11: software and the confound comparison on the same subjects, on the datasets where both are defined
paired = atlas.dropna(subset=["software_dice", "confound_dice_subset"])
axes = [("axis_smoothing", "Smoothing\n(4/6/8 mm)"), ("axis_confounds", "Confounds\n(6P/24P/\naCompCor/spikes)"),
        ("axis_hrf", "HRF\n(± derivative)"), ("axis_noise", "Noise model\n(AR(1)/OLS)"),
        ("confound_dice_subset", f"Confounds,\nFSL subjects\n({len(paired)} datasets)"),
        ("software_dice", f"Software\n(FSL vs nilearn,\n{len(paired)} datasets)")]
fig, ax = plt.subplots(figsize=(8.2, 4.4))
for i, (col, label) in enumerate(axes):
    v = (paired if col in ("software_dice", "confound_dice_subset") else atlas)[col].dropna().to_numpy()
    ax.boxplot(v, positions=[i], widths=0.5, showfliers=False)
    ax.scatter(np.full(len(v), i) + np.random.default_rng(i).uniform(-0.15, 0.15, len(v)), v, s=12, alpha=0.6)
ax.set_xticks(range(len(axes)), [a[1] for a in axes], fontsize=8)
ax.set_ylabel("Signed Dice between maps that differ\nonly in this choice (per dataset)")
ax.set_ylim(-0.03, 1.03)
fig.tight_layout()
fig.savefig(FIG / "which_choice.png", dpi=150)
sw = primary["secondary"]["software_paired"]
(FIG / "which_choice.txt").write_text(
    "How much each choice moves the thresholded map. For each dataset, the mean signed Dice between configurations "
    "that differ only in that choice (the first four, all datasets with R), then, on the "
    f"{sw['datasets']} datasets where both are defined, nilearn maps that differ only in confounds on the FSL "
    "subjects (up to 20) and FSL against nilearn maps that differ only in software. Lower means the choice matters "
    f"more. Smoothing and confounds move the maps most; switching software moves them less than switching confounds "
    f"(mean {sw['software_dice_mean']:.2f} against {sw['confound_dice_mean']:.2f}; software higher in "
    f"{sw['software_higher_in']} of {sw['datasets']}). Software bundles smoothing kernel, HRF shape, high-pass filter "
    "and scaling.")

# key-result tiles: [label, value, note]
h1, h2 = primary["H1"], primary["H2"]
tiles = [
    ["H1: N and tSNR explain R", f"R² {h1['R2']:.2f}", f"95% CI {h1['ci'][0]:.2f}–{h1['ci'][1]:.2f} · {h1['verdict']}"],
    ["H2: small datasets fragile", f"median {h2['median']:.2f}", f"95% CI {h2['ci'][0]:.2f}–{h2['ci'][1]:.2f} · {h2['verdict']}"],
    ["Median robustness", f"{primary['secondary']['R_median_all']:.2f}", f"{int(atlas.R.notna().sum())} datasets, 736 subjects"],
    ["Software vs confounds", f"{sw['software_dice_mean']:.2f} vs {sw['confound_dice_mean']:.2f}",
     f"Dice, {sw['datasets']} matched datasets; software higher in {sw['software_higher_in']}"],
    ["External check (G4)", f"{ext['corr_at_least_0.7']}/{ext['datasets_compared']}", f"FitLins r ≥ 0.7, median {ext['corr_median']:.2f}"],
]
(T / "tiles.json").write_text(json.dumps(tiles, ensure_ascii=False, indent=1) + "\n")
print("figures and tiles written")
