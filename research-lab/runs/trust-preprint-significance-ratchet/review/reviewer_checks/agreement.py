"""Agreement and Cohen's kappa between the reviewer's and the agent's adjudications; sensitivity of the verified
shares to the reviewer's disagreements; writes the combined re-adjudication table."""
import json
import pandas as pd
from pathlib import Path
from scipy import stats as st
H = Path(__file__).resolve().parent
RUN = H.parents[1]
def kappa(a, b):
    a, b = pd.Series(a), pd.Series(b)
    po = (a == b).mean(); pe = sum(((a == k).mean()) * ((b == k).mean()) for k in (0, 1))
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")
def clopper(k, n):
    lo = 0.0 if k == 0 else st.beta.ppf(0.025, k, n - k + 1); hi = 1.0 if k == n else st.beta.ppf(0.975, k + 1, n - k)
    return round(lo, 3), round(hi, 3)
v1 = pd.read_csv(H / "readjudication_v1.csv"); v2 = pd.read_csv(H / "readjudication_v2.csv")
k1 = pd.read_csv(RUN / "results/tables/alignment_validation.csv").set_index("id"); k2 = pd.read_csv(RUN / "results/tables/alignment_validation_v2.csv").set_index("id")
assert (v1.agent.values == k1.loc[v1.id, "correct"].values).all() and (v2.agent.values == k2.loc[v2.id, "correct"].values).all(), "agent column mismatch"
v1["sample"] = "v1"; v2["sample"] = "v2"
v1["stratum"] = k1.loc[v1.id, "stratum"].values; v2["stratum"] = k2.loc[v2.id, "stratum"].values
v1["pair"] = k1.loc[v1.id, "pair"].values; v2["pair"] = k2.loc[v2.id, "pair"].values
for name, d in (("v1 (60)", v1), ("v1 crossings judged correct by agent (12)", v1[(v1.stratum == "crossing") & (v1.agent == 1)]),
                ("v1 other 48", v1[~((v1.stratum == "crossing") & (v1.agent == 1))]), ("v2 (64 strict crossings)", v2), ("all (124)", pd.concat([v1, v2]))):
    n = len(d); ag = int((d.reviewer == d.agent).sum())
    print(f"{name:45s} n={n:3d} agree={ag:3d} ({ag/n:.3f}) kappa={kappa(d.reviewer, d.agent):.3f} reviewer correct={int(d.reviewer.sum())} agent correct={int(d.agent.sum())}")
dis = pd.concat([v1, v2]); dis = dis[dis.reviewer != dis.agent]
print("\ndisagreements:\n", dis[["sample", "id", "reviewer", "agent", "reviewer_note"]].to_string(index=False))
# sensitivity of the verified shares
vc = pd.read_csv(RUN / "results/tables/verified_crossings.csv")
def share(df, label):
    k, n = int(df.up.sum()), len(df); print(f"  {label:70s} {k}/{n} = {k/n:.3f} exact {clopper(k, n)}")
print("\nverified-crossing shares:")
share(vc[vc["sample"] == "v2"], "v2 census as reported (42)")
share(vc[(vc["sample"] == "v2") & ~vc.id.isin(["w053", "w057"])], "v2 census minus reviewer's disagreements (w053, w057)")
share(vc, "combined as reported (52)")
drop = ["w053", "w057", "v136"]
share(vc[~vc.id.isin(drop)], "combined minus reviewer's disagreements")
share(vc[~vc.id.isin(drop + ["v182", "w024", "w090"])], "... also minus star-legend typo (v182) and permuted pair (w024, w090)")
share(vc[~vc.id.isin(drop + ["v182", "w024", "w090"]) & ~vc.kind.isin(["correction or typo"])], "... also minus corrections/typos (changed results only)")
share(vc[vc.kind.isin(["data changed", "re-analysis"])], "data changed or re-analysed (as in the report)")
# version population of the combined set
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned/pairs.jsonl")]).set_index("preprint_doi")
vc["version_used"] = vc.pair.map(pairs.version_used)
print("\ncombined 52 by version_used:", vc.version_used.fillna("unknown").astype(str).value_counts().to_dict())
print("duplicate underlying results in the 52: w049/w094 (same comparison, abstract and results of one paper); w024/w090 (one sentence, permuted values)")
out = pd.concat([v1, v2])[["sample", "id", "stratum", "pair", "reviewer", "agent", "reviewer_note"]].rename(columns={"reviewer": "reviewer_judgement", "agent": "agent_judgement"})
out.to_csv(H / "readjudication_table.csv", index=False); print("\nwrote", H / "readjudication_table.csv", len(out), "rows")
