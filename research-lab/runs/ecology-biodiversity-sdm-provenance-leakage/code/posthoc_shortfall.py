"""POST HOC (written after the H1 result): matched random removal fell short of C1's count for 13% of presences, so
the random arms removed fewer presences than C1. Removal counts by arm and source database, and the H1 contrast
restricted to species whose mean random removal is at least 90% of their C1 removal.
-> results/tables/posthoc_shortfall.json

D6 (second confirmation pass): n_pres is recorded after rf.py's 10,000-presence cap, so for the 662 capped species the
C1 removal read as zero and they counted as "matched" by construction. The pre_cap block counts removal as the removed
presences (data/work/removals/Ck.parquet) that lie in SAGE's occurrence subsample, which is what rf.py drops before
capping; for every uncapped species it equals the n_pres difference. The after-cap figures are kept, labelled.
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
R = ["C2", "C3", "C4", "C5", "C6"]
d = pd.DataFrame([json.loads(open(f).read()) for f in glob.glob(str(RUN / "data" / "work" / "rf" / "C*.json"))])
n = d.pivot(index="sp", columns="cond", values="n_pres")
rem1, remr = n["C0"] - n["C1"], n["C0"] - n[R].mean(axis=1)
auc = d.pivot(index="sp", columns="cond", values="auroc_src")
did = auc[R].mean(axis=1) - auc["C1"]
rng = np.random.default_rng(20261025)


def boot(x):
    x = x.to_numpy()
    b = [x[rng.integers(len(x), size=len(x))].mean() for _ in range(2000)]
    return [round(float(np.percentile(b, 2.5)), 5), round(float(np.percentile(b, 97.5)), 5)]


ok = remr >= 0.9 * rem1
out = {"species": int(len(did)), "mean_removed_C1": round(float(rem1.mean()), 1),
       "mean_removed_random": round(float(remr.mean()), 1),
       "matched_species": int(ok.sum()), "did_matched": round(float(did[ok].mean()), 5), "ci_matched": boot(did[ok]),
       "did_all": round(float(did.mean()), 5), "by_source_db": {}}
c0 = d[d.cond == "C0"].set_index("sp").auroc_db
for db in sorted({k for x in d.auroc_db for k in (x or {})}):
    sp = c0.map(lambda x: (x or {}).get(db)).dropna().index
    out["by_source_db"][db] = {"species": int(len(sp)), "mean_removed_C1": round(float(rem1.reindex(sp).mean()), 1),
                               "mean_removed_random": round(float(remr.reindex(sp).mean()), 1),
                               "random_to_C1_ratio": round(float(remr.reindex(sp).sum() / max(1, rem1.reindex(sp).sum())), 2)}
out["after_cap_note"] = "mean_removed_*, matched_species and did_matched above use n_pres after the 10,000 cap"
pop = sorted(set(pd.read_csv(T / "population.csv").sp))
sub = np.load(Path("/mnt/sage/bench") / "targets" / "subsample_indices" / "train_indices_10000_1km.npy")
pre = {}
for c in ["C1"] + R:
    r = pd.read_parquet(RUN / "data" / "work" / "removals" / f"{c}.parquet", columns=["sp", "cell"])
    r = r[r.sp.isin(pop)]
    pre[c] = r[np.isin(r.cell.to_numpy(), sub)].groupby("sp").size()
pre = pd.DataFrame(pre).reindex(pop).fillna(0)
p1, pr = pre["C1"], pre[R].mean(axis=1)
okp = (pr >= 0.9 * p1).reindex(did.index).fillna(False)
capped = (n["C0"] >= 10000).reindex(pop)
unc = ~capped
out["pre_cap"] = {"capped_species": int(capped.sum()),
                  "uncapped_species_where_counts_agree": f"{int((rem1.reindex(pop)[unc] == p1[unc]).sum())}/{int(unc.sum())}",
                  "mean_removed_C1": round(float(p1.mean()), 1), "mean_removed_random": round(float(pr.mean()), 1),
                  "pooled_random_to_C1": round(float(pr.sum() / p1.sum()), 3),
                  "matched_species": int(okp.sum()), "matched_with_C1_removal_zero": int((okp & (p1.reindex(did.index) == 0)).sum()),
                  "did_matched": round(float(did[okp].mean()), 5), "ci_matched": boot(did[okp]), "by_source_db": {}}
ratio = pr / p1.replace(0, np.nan)
for db in ["Australia", "Denmark", "TAVA West_Africa", "Ukraine Grassland Database", "Netherlands"]:
    v = d.assign(a=d.auroc_db.map(lambda x: (x or {}).get(db))).pivot(index="sp", columns="cond", values="a")[["C1"] + R].dropna()
    x = v[R].mean(axis=1) - v["C1"]
    ra = ratio.reindex(x.index)
    out["pre_cap"]["by_source_db"][db] = {"species": int(len(x)), "pooled_random_to_C1": round(float(pr.reindex(x.index).sum() / max(1, p1.reindex(x.index).sum())), 3),
                                          "per_species_median_ratio": round(float(ra.median()), 3),
                                          "did": round(float(x.mean()), 5), "ci": boot(x),
                                          "matched_species": int((ra >= 0.9).sum()),
                                          "did_matched": round(float(x[ra >= 0.9].mean()), 5) if (ra >= 0.9).sum() > 1 else None,
                                          "ci_matched": boot(x[ra >= 0.9]) if (ra >= 0.9).sum() > 1 else None}
(T / "posthoc_shortfall.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "by_source_db"}))
