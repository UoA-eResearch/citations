"""The report's per-dataset table, generated from results/tables/atlas.csv and external_fitlins.csv (D11: no
hand-copied numbers). Prints Markdown and checks the summary counts quoted in the report.

  report_table.py
"""
from pathlib import Path

import pandas as pd

T = Path(__file__).resolve().parents[1] / "results" / "tables"
TEMPLATE_VOXELS = 235840
AX = {"axis_smoothing": "smoothing", "axis_hrf": "HRF", "axis_confounds": "confounds", "axis_noise": "noise model"}


def f2(x):
    return "–" if pd.isna(x) else f"{x:.2f}"


def main():
    A = pd.read_csv(T / "atlas.csv")
    X = pd.read_csv(T / "external_fitlins.csv").set_index("ds")
    A = A.assign(_r=A.R.fillna(-1)).sort_values(["_r", "ds"], ascending=[False, True])
    print("| Dataset | Task: contrast | N | tSNR | Brain covered | R | Correlation index | Configurations with any voxel "
          "| Most influential choice | FSL vs nilearn Dice | FitLins r |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, a in A.iterrows():
        mi = "–" if pd.isna(a.R) else AX[a[list(AX)].astype(float).idxmin()]
        nany = round(a["any"] * 48)
        cov = f"{100 * a.voxels / TEMPLATE_VOXELS:.0f}%"
        fr = X["corr"].get(a.ds) if a.ds in X.index and X.loc[a.ds, "status"] == "ok" else None
        print(f"| {a.ds} | {a.task}: {a.contrast} | {int(a.N)} | {a.tsnr:.0f} | {cov} | {f2(a.R)} | {a['corr']:.2f} "
              f"| {nany}/48 | {mi} | {f2(a.software_dice)} | {f2(fr)} |")
    d = A.dropna(subset=["R"])
    print("\nmost influential:", d[list(AX)].astype(float).idxmin(axis=1).map(AX).value_counts().to_dict())
    print("R >= 0.6:", int((d.R >= 0.6).sum()), "all 48 non-empty among them:", int(((d.R >= 0.6) & (d["any"] == 1)).sum()),
          "| R < 0.2:", int((d.R < 0.2).sum()), "| any == 1:", int((A["any"] == 1).sum()))
    print("voxels: min", int(A.voxels.min()), A.loc[A.voxels.idxmin(), "ds"], "median", int(A.voxels.median()))
    print("corr index vs supra (Spearman, 24):", round(A[["corr", "supra_median"]].corr("spearman").iloc[0, 1], 3))
    print("R vs N, R vs tSNR (Spearman, 22):", round(d[["R", "N"]].corr("spearman").iloc[0, 1], 3),
          round(d[["R", "tsnr"]].corr("spearman").iloc[0, 1], 3))
    tp = A.dropna(subset=["R_task_positive"])
    print("task-positive > primary:", int((tp.R_task_positive > tp.R).sum()), "+ R undefined:", int(tp.R.isna().sum()),
          "ties:", int((tp.R_task_positive == tp.R).sum()), "of", len(tp))
    print("tsnr range", round(A.tsnr.min(), 1), round(A.tsnr.max(), 1), "median", round(A.tsnr.median(), 1))
    print("corr range", round(A["corr"].min(), 2), round(A["corr"].max(), 2))


if __name__ == "__main__":
    main()
