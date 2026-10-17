"""Holdout construction: recompute T10 tranche independently for every network; median share; undated never withheld;
random holdouts same size and dated-only; new entrants."""
import json, math, pandas as pd, numpy as np
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
hold = pd.read_csv(f"{RUN}/data/holdouts.csv", dtype={"record": str}).set_index("record")
jobs = {j["record"]: j for j in json.load(open(f"{RUN}/data/jobs.json"))}
nr = pd.read_csv(f"{RUN}/results/tables/network_results.csv", dtype={"record": str})
prim = set(nr[nr.included & (nr.set == "primary")].record)
rows = []; bad = []
for rec, j in jobs.items():
    d = pd.read_csv(f"{RUN}/data/std/{rec}.csv", dtype={"study": str})
    yr = d.groupby("study").year.first()
    dated = yr.dropna()
    k = len(yr); kd = len(dated)
    # my own T10: smallest set of whole latest years with >= ceil(0.10*kd) dated studies
    target = max(1, math.ceil(0.10 * kd))
    years = sorted(dated.unique(), reverse=True)
    held = []; yrs = []
    for y in years:
        held += dated[dated == y].index.tolist(); yrs.append(int(y))
        if len(held) >= target: break
    F = {f["name"]: f for f in j["fits"]}
    pre_T10 = set(F["T10"]["studies"]); allst = set(F["full"]["studies"])
    withheld = allst - pre_T10
    undated = set(yr[yr.isna()].index)
    # random holdouts
    rsizes = {len(allst - set(F[n]["studies"])) for n in F if n.startswith("R")}
    r_undated_withheld = sum(1 for n in F if n.startswith("R") and (allst - set(F[n]["studies"])) & undated)
    rows.append(dict(record=rec, primary=rec in prim, k=k, k_dated=kd, undated=len(undated), target=target,
                     my_T10_n=len(held), file_T10_n=hold.loc[rec, "T10_n"], my_years=",".join(map(str, sorted(yrs))), file_years=hold.loc[rec, "T10_years"],
                     match_set=set(held) == withheld, undated_withheld=len(withheld & undated),
                     share=len(withheld) / k, random_sizes=",".join(map(str, sorted(rsizes))), n_random=sum(1 for n in F if n.startswith("R")),
                     random_withholding_undated=r_undated_withheld,
                     S2_is_latest_year=set(allst - set(F["S2"]["studies"])) == set(dated[dated == dated.max()].index)))
df = pd.DataFrame(rows)
df.to_csv(f"{RUN}/review/reviewer_checks/holdout_recompute.csv", index=False)
print("networks:", len(df), "; T10 set matches my recomputation:", df.match_set.sum())
print("undated studies withheld in T10 (networks):", (df.undated_withheld > 0).sum())
print("random holdouts withholding undated (networks):", (df.random_withholding_undated > 0).sum())
print("random holdout size == T10 size (networks):", (df.random_sizes == df.file_T10_n.astype(str)).sum())
print("S2 == latest year:", df.S2_is_latest_year.sum())
p = df[df.primary]
print("primary n:", len(p), "median T10 share:", p.share.median(), " mean:", p.share.mean(), " max:", p.share.max(), " >0.5:", (p.share > 0.5).sum())
print("share quantiles:", p.share.quantile([.1, .25, .5, .75, .9]).round(3).to_dict())
print("networks with undated studies (primary):", (p.undated > 0).sum(), " total undated studies:", p.undated.sum())
print(df[~df.match_set].to_string())
# Hand-recompute table for 10 networks
import random
sample = random.Random(7).sample(sorted(p.record), 10)
print("\n10 networks hand-recomputed (shown):")
print(df[df.record.isin(sample)][["record", "k", "k_dated", "target", "my_T10_n", "file_T10_n", "my_years", "file_years", "match_set", "share"]].to_string())
