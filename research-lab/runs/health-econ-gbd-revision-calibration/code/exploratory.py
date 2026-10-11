"""Exploratory analyses added after the primary outcomes were seen (deviations.md D2). Labelled exploratory in the
report; none changes a preregistered verdict. Writes results/tables/exploratory.csv.

X1  C1/C2 excluding 'Other neoplasms', whose GBD 2023 increase the GBD 2023 appendix (p. 361) attributes to fixing a
    CoDCorrect error that excluded 'Other benign and in situ neoplasms' deaths, and to brain-tumour codes dropped in
    previous rounds.
X2  C1/C2 excluding every residual cause whose name starts with 'Other' (a name rule, not an outcome rule).
X3  Cause-level view: the distribution of per-cause C2 (unweighted across causes).
X4  Calibration at several nominal levels: share of cells with |z| <= Phi^-1(1 - a/2), a = 0.5, 0.2, 0.1, 0.05, 0.01.
X5  The H4 contrast (C2 high - low) within each year separately.
X6  C2 with asymmetric half-widths: each release contributes the half-width on the side facing the other estimate,
    instead of the symmetric log-normal s."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

import analysis as A

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def contrast(p, q, ycol, ecol, label):
    g = A.groups_of(q)
    r = A.boot_share(p, ycol, ecol, groups=g)
    d = r["high"][1] - r["low"][1]
    lo, hi = A.ci(d)
    return dict(analysis=label, group="high - low", estimate=r["high"][0] - r["low"][0], lower95=lo, upper95=hi)


def main():
    p = A.metrics(pd.read_parquet(RUN / "data" / "panel.parquet"))
    q = pd.read_parquet(RUN / "data" / "quality.parquet")
    rows = []
    x1 = p[p.cause_name != "Other neoplasms"]
    rows += A.row("X1 C1 excluding Other neoplasms", x1, "cov1", "elig1")
    rows += A.row("X1 C2 excluding Other neoplasms", x1, "cov2", "elig2")
    x2 = p[~p.cause_name.str.startswith("Other")]
    rows.append(dict(analysis="X2 number of residual 'Other ...' causes excluded", group="all",
                     estimate=float(p[p.cause_name.str.startswith("Other")].cause_id.nunique())))
    rows += A.row("X2 C1 excluding residual 'Other ...' causes", x2, "cov1", "elig1")
    rows += A.row("X2 C2 excluding residual 'Other ...' causes", x2, "cov2", "elig2")
    rows.append(contrast(x2, q, "cov2", "elig2", "X2 C2 high - low, excluding residual causes"))
    per = p[p.elig2].groupby("cause_id").cov2.mean()
    for qq in (0.1, 0.25, 0.5, 0.75, 0.9):
        rows.append(dict(analysis=f"X3 per-cause C2, {int(qq * 100)}th percentile across {len(per)} causes", group="all", estimate=float(per.quantile(qq))))
    rows.append(dict(analysis="X3 causes with per-cause C2 >= 0.95", group="all", estimate=float((per >= 0.95).sum())))
    e = p[p.elig2]
    for a in (0.5, 0.2, 0.1, 0.05, 0.01):
        rows.append(dict(analysis=f"X4 share |z| <= {norm.ppf(1 - a / 2):.3f} (nominal {1 - a:.2f})", group="all", n_cells=len(e),
                         estimate=float((np.abs(e.z) <= norm.ppf(1 - a / 2)).mean())))
    rows.append(dict(analysis="X4 SD of z (1 if calibrated and independent)", group="all", estimate=float(np.std(e.z))))
    rows.append(dict(analysis="X4 median |z| (0.674 if calibrated and independent)", group="all", estimate=float(np.median(np.abs(e.z)))))
    for qq in (0.80, 0.90, 0.95):
        rows.append(dict(analysis=f"X4 widening factor so that {int(qq * 100)}% of |z| fall within the nominal {int(qq * 100)}% band",
                         group="all", estimate=float(np.quantile(np.abs(e.z), qq) / norm.ppf(0.5 + qq / 2))))
    for y in (2019, 2021):
        rows.append(contrast(p[p.year == y], q, "cov2", "elig2", f"X5 C2 high - low, year {y}"))
    # X6 asymmetric half-widths on the log scale
    up = np.log(e.p23) > np.log(e.p21)
    h21 = np.where(up, np.log(e.U21) - np.log(e.p21), np.log(e.p21) - np.log(e.L21)) / A.Z
    h23 = np.where(up, np.log(e.p23) - np.log(e.L23), np.log(e.U23) - np.log(e.p23)) / A.Z
    with np.errstate(divide="ignore", invalid="ignore"):
        za = (np.log(e.p23) - np.log(e.p21)) / np.sqrt(h21 ** 2 + h23 ** 2)
    pa = p.copy()
    pa["cov2a"] = False
    pa.loc[e.index, "cov2a"] = np.abs(za) <= A.Z
    pa["elig2a"] = pa.elig2 & pd.Series(False, index=p.index).where(~p.index.isin(e.index), np.isfinite(pd.Series(za, index=e.index)).reindex(p.index).fillna(False))
    rows += A.row("X6 C2 with asymmetric half-widths", pa, "cov2a", "elig2a", groups=A.groups_of(q))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "exploratory.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    main()
