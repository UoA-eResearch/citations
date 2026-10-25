"""POST HOC (D2, after independent review). Not confirmatory; reported beside the preregistered result.

1. Coverage-break fix at its source: all stacks with district-court (FD) citers removed ("noFD").
2. Era splits: overruling years 1960-1989 and 1990-2013 in the pre-2019 sample, and the same eras plus 2014-2024
   without FD citers.
3. Weighting: per-stack D(-1) (each stack fitted alone), the share of pre-period treated citations carried by the
   most-cited stacks, and the pooled pre-2019 D(-1) without the 1, 3, 5 and 10 most-cited stacks.
4. Chevron by citing-court type (federal courts of appeals only; all courts except district courts), with its
   matching balance.
5. The calendar-year cut: the pre-2019 sample (overrulings to 2013) with and without years after 2018.
-> results/tables/posthoc_d2.json, results/tables/posthoc_d2_yearcut.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event as E  # noqa: E402
import secondary as S  # noqa: E402

T = E.T
VARIANTS = ["noFD", "pre2019_era1960_89", "pre2019_era1990_2013", "noFD_era1960_89", "noFD_era1990_2013", "noFD_recent"]


def summary(o):
    keep = ("treated", "balance", "D", "pre_share", "boot_ok", "D5_ci", "Dm1_ci", "pre_share_ci", "H1")
    o = {k: o[k] for k in keep if k in o}
    o["balance"] = {k: v for k, v in o["balance"].items() if k != "per_stack_smd"}
    return o


def weighting():
    o, d, stacks = E.run("pre2019", boot=False)
    rows = []
    for st in stacks:
        s = st["stack"]
        x = d[d["stack"] == s]
        pre = float(x[(x.treated == 1) & (x.ev < 0)].y.sum())
        try:
            dm1 = E.stats(E.fit(x))[0].get(-1, np.nan)
        except Exception:
            dm1 = np.nan
        rows.append({"stack": s, "cite": st["treated"]["cite"], "T0": st["treated"]["T0"], "pre_citations": pre,
                     "Dm1": float(dm1)})
    w = pd.DataFrame(rows).sort_values("pre_citations", ascending=False)
    w["weight_share"] = w.pre_citations / w.pre_citations.sum()
    out = {"stacks": int(len(w)), "share_Dm1_negative": round(float((w.Dm1.dropna() < 0).mean()), 3),
           "median_Dm1": round(float(w.Dm1.median()), 3), "top5_weight_share": round(float(w.weight_share.head(5).sum()), 3),
           "top5": w.head(5)[["cite", "T0", "pre_citations", "Dm1", "weight_share"]].round(3).to_dict("records"),
           "pooled_Dm1_all": round(float(o["D"][-1]), 4)}
    for k in (1, 3, 5, 10):
        keep_ids = set(w["stack"].iloc[k:])
        out[f"pooled_Dm1_without_top{k}"] = round(float(E.stats(E.fit(d[d["stack"].isin(keep_ids)]))[0][-1]), 4)
    return out, w


def yearcut():
    cites, cl, wide, listed, treated, _ = E.build("pre2019")
    stacks, _ = E.match(cl, wide, listed, treated)
    d = E.long_panel(stacks, wide, cites)
    a, b = E.stats(E.fit(d))[0], E.stats(E.fit(d[d.year <= 2018]))[0]
    out = {"T0_le_2013_all_years": {"Dm1": round(a[-1], 4), "D5": round(a[5], 4)},
           "T0_le_2013_years_le_2018": {"Dm1": round(b[-1], 4), "D5": round(b[5], 4)}}
    (T / "posthoc_d2_yearcut.json").write_text(json.dumps(out, indent=1))
    return out


def chevron():
    out = {}
    for v in ("appellate", "noFD"):
        cites, cl, wide, listed, _, _ = E.build(v)
        out[v] = S.one_case(111221, 2024, 1984, "467 U.S. 837", cites, cl, wide, listed)
    return out


def main():
    cache = T / "posthoc_d2_variants.json"                        # finished variants survive a later failure
    res = json.loads(cache.read_text()) if cache.exists() else {}
    for v in VARIANTS:
        if v in res:
            continue
        o, _, _ = E.run(v)
        res[v] = summary(o)
        cache.write_text(json.dumps(res, indent=1, default=str))
        print(v, res[v]["D"].get(-1), res[v].get("Dm1_ci"), res[v]["D"].get(5), res[v].get("D5_ci"), flush=True)
    res["weighting_pre2019"], w = weighting()
    w.to_csv(T / "posthoc_d2_per_stack.csv", index=False)
    res["chevron_by_court"] = chevron()
    res["yearcut"] = yearcut()
    (T / "posthoc_d2.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "chevron_by_court"}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
