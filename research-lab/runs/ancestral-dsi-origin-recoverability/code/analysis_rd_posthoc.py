"""Post hoc checks on limb 1 (deviations D1), added after the placebo cutoffs failed. Descriptive; H1's verdict is
the preregistered estimate's.

1. The preregistered RD excluding SARS-CoV-2 samples (taxonomy 2697049), whose surveillance volumes swung the pooled
   series in 2020-2022.
2. A within-submitter comparison: for submitting organisations present in both the 23 months before and the 23 months
   after the cutoff (donut of a month either side), the change in their usable / placeholder / absent shares, each
   organisation weighted by its total samples; cluster bootstrap over organisations (1,000 resamples, seed 20261022).
   Run at the real cutoff and at the two placebo cutoffs.

Writes results/tables/rd_posthoc.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_rd as A  # noqa: E402

TAB = A.TAB


def within_owner(d, cut, months=24, donut=1, b=A.B, seed=A.SEED):
    lo, hi = cut - pd.DateOffset(months=months), cut + pd.DateOffset(months=months)
    w = d[(d.date >= lo) & (d.date < hi) &
          ((d.date < cut - pd.DateOffset(months=donut)) | (d.date >= cut + pd.DateOffset(months=donut)))].copy()
    w["post"] = w.date >= cut
    g = w.groupby(["owner", "post"]).country_class.value_counts().unstack(fill_value=0)
    g["n"] = g.sum(axis=1)
    g = g.reset_index()
    pre, post = g[~g.post].set_index("owner"), g[g.post].set_index("owner")
    both = pre.index.intersection(post.index)
    pre, post = pre.loc[both], post.loc[both]
    wt = (pre.n + post.n).to_numpy(float)
    out = {"owners_in_both": int(len(both)), "samples": int(wt.sum())}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(both), size=(b, len(both)))
    for c in A.CLASSES:
        if c not in pre:
            continue
        diff = (post[c] / post.n - pre[c] / pre.n).to_numpy(float)
        est = float(np.average(diff, weights=wt))
        bs = np.array([np.average(diff[i], weights=wt[i]) for i in idx])
        out[c] = {"change_pp": round(100 * est, 3),
                  "ci_pp": [round(100 * float(np.percentile(bs, 2.5)), 3), round(100 * float(np.percentile(bs, 97.5)), 3)]}
    return out


def main():
    import glob
    cols = ["submission_date", "owner", "country_class", "country_raw", "package", "taxonomy_id", "organism", "host"]
    d = pd.concat([pd.read_parquet(f, columns=cols) for f in sorted(glob.glob(str(A.RUN / "data" / "samples" / "*.parquet")))],
                  ignore_index=True)
    d = d[~A.human_host_metagenome(d)]        # D3
    d["date"] = pd.to_datetime(d.submission_date, errors="coerce")
    d = d.dropna(subset=["date"])
    out = {}
    nocov = d[d.taxonomy_id != "2697049"]
    out["sars_cov_2_share_of_window"] = round(float((d[(d.date >= "2021-06-01") & (d.date < "2025-06-01")].taxonomy_id
                                                     == "2697049").mean()), 4)
    for name, cut in (("cutoff_2023_06_01", A.CUT), ("placebo_2021_06_01", pd.Timestamp("2021-06-01")),
                      ("placebo_2022_06_01", pd.Timestamp("2022-06-01"))):
        r = A.estimate(nocov, cut=cut)
        out[f"rd_without_sars_cov_2_{name}"] = {c: r[c] for c in A.CLASSES}
        out[f"within_owner_{name}"] = within_owner(d, cut)
    json.dump(out, open(TAB / "rd_posthoc.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
