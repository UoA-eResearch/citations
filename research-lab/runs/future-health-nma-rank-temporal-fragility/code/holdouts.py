"""Build the holdout fits for every standardised network (plan section 4) and write the R job file.

Usage: venv/bin/python code/holdouts.py [full_only]
  full_only: one fit per network (the full network), for inclusion rule 4 and validation, before any holdout exists.
Writes data/jobs[_full].json and data/holdouts.csv (one row per network: dated studies, tranche years and sizes)."""
import json
import math
import random
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
STD = RUN / "data" / "std"
N_RANDOM = 200


def kind(row):
    if row.format == "iv":
        return "iv"
    return "long_" + row.type.lower()


def newest(st, frac):
    """Smallest set of whole latest years holding at least ceil(frac * k) dated studies."""
    dated = st.dropna()
    target = max(1, math.ceil(frac * len(dated)))
    out = []
    for y in sorted(dated.unique(), reverse=True):
        out += dated[dated == y].index.tolist()
        if len(out) >= target:
            break
    return out


def oldest(st, frac):
    dated = st.dropna()
    target = max(1, math.ceil(frac * len(dated)))
    keep = []
    for y in sorted(dated.unique()):
        keep += dated[dated == y].index.tolist()
        if len(keep) >= target:
            break
    return [s for s in dated.index if s not in set(keep)]


def main():
    full_only = len(sys.argv) > 1 and sys.argv[1] == "full_only"
    s = pd.read_csv(RUN / "data" / "std_summary.csv", dtype={"record": str})
    s = s[s.parsed & (s.measure != "other") & (s.n_trts >= 3) & (s.n_studies >= 10) & (s.year_share >= 0.90)]
    jobs, rows = [], []
    for r in s.itertuples():
        d = pd.read_csv(STD / f"{r.record}.csv", dtype={"study": str})
        st = d.groupby("study").year.first()
        allst = st.index.tolist()
        small = "good" if r.direction == "Harmful" else "bad"
        fits = [dict(name="full", studies=allst, detail=True)]
        row = dict(record=r.record, k=len(allst), k_dated=int(st.notna().sum()))
        if not full_only:
            hold = {"T10": newest(st, 0.10), "S1": newest(st, 0.25), "S3": oldest(st, 0.50)}
            hold["S2"] = st[st == st.max()].index.tolist()
            for name, h in hold.items():
                fits.append(dict(name=name, studies=[x for x in allst if x not in set(h)], detail=True))
                row[f"{name}_n"] = len(h)
            row["T10_years"] = ",".join(str(int(y)) for y in sorted(st[hold["T10"]].unique()))
            row["T10_share"] = len(hold["T10"]) / len(allst)
            rnd = random.Random(int(r.record))
            dated = st.dropna().index.tolist()
            for i in range(N_RANDOM):
                h = set(rnd.sample(dated, len(hold["T10"])))
                fits.append(dict(name=f"R{i:03d}", studies=[x for x in allst if x not in h], detail=False))
        jobs.append(dict(record=r.record, path=str(STD / f"{r.record}.csv"), kind=kind(r), measure=r.measure,
                         small_values=small, seed=int(r.record) % 100000, fits=fits))
        rows.append(row)
    tag = "_full" if full_only else ""
    json.dump(jobs, open(RUN / "data" / f"jobs{tag}.json", "w"))
    pd.DataFrame(rows).to_csv(RUN / "data" / f"holdouts{tag}.csv", index=False)
    print(len(jobs), "networks;", sum(len(j["fits"]) for j in jobs), "fits")


if __name__ == "__main__":
    sys.exit(main())
