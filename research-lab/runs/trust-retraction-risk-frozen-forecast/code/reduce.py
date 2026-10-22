"""Merge pass-1 outputs into global lookups (plan section 3). Writes data/lookup/*.npy and data/lookup/rates.parquet.

  works     wid (sorted), year, src, host, ret     (duplicate ids: the copy from the latest partition wins)
  authors   aid (sorted), first year
  aret      (aid, ret_year) pairs, sorted
  rates     prior retraction rate and article counts per (kind, entity, Y) for every Y used by the study:
            rate = retracted articles from Y-3..Y-1 with a retraction year <= Y-1, over articles from Y-3..Y-1
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
P1, OUT = RUN / "data" / "pass1", RUN / "data" / "lookup"
YEARS = [2015, 2016, 2017, 2018, 2019, 2021, 2022, 2025, 2026]


KIND = {"S": 0, "H": 1, "I": 2}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(P1 / "*.npz")), key=lambda f: Path(f).stem.split("_", 1)[1])   # by partition date
    log = {}
    # works: one pass, then sort; the copy from the latest partition wins
    W = {k: [] for k in ("wid", "year", "src", "host", "ret", "order")}
    for i, f in enumerate(files):
        z = np.load(f)
        for k in ("wid", "year", "src", "host", "ret"):
            W[k].append(z[k])
        W["order"].append(np.full(len(z["wid"]), i, dtype=np.int16))
    W = {k: np.concatenate(v) for k, v in W.items()}
    o = np.lexsort((W["order"], W["wid"]))
    del W["order"]
    wid = W["wid"][o]
    last = np.r_[wid[1:] != wid[:-1], True]
    keep = o[last]
    del o, wid
    log.update({"rows": int(len(last)), "unique_works": int(last.sum()), "duplicates_dropped": int((~last).sum())})
    for k in ("wid", "year", "src", "host", "ret"):
        np.save(OUT / f"w_{k}.npy", W[k][keep])
    del W, keep, last
    # authors' first year
    a, y = [], []
    for f in files:
        z = np.load(f)
        a.append(z["af_a"]); y.append(z["af_y"])
    a, y = np.concatenate(a), np.concatenate(y)
    o = np.lexsort((y, a))
    a, y = a[o], y[o]
    first = np.r_[True, a[1:] != a[:-1]]
    np.save(OUT / "a_id.npy", a[first]); np.save(OUT / "a_first.npy", y[first].astype(np.int16))
    log["authors"] = int(first.sum())
    del a, y, o, first
    # authorships of retracted works
    a, r = [], []
    for f in files:
        z = np.load(f)
        a.append(z["ar_a"]); r.append(z["ar_r"])
    ar = pd.DataFrame({"a": np.concatenate(a), "r": np.concatenate(r)}).sort_values(["a", "r"])
    np.save(OUT / "ar_a.npy", ar.a.values); np.save(OUT / "ar_r.npy", ar.r.values.astype(np.int16))
    log["retracted_authorships"] = int(len(ar))
    # entity counts, aggregated in batches
    parts, batch = [], []
    for i, f in enumerate(files):
        z = np.load(f)
        batch.append(pd.DataFrame({"k": np.array([KIND[c] for c in z["ent_k"]], dtype=np.int8) if len(z["ent_k"]) else
                                   np.array([], dtype=np.int8), "e": z["ent_e"], "y": z["ent_y"], "r": z["ent_r"],
                                   "n": z["ent_n"]}))
        if len(batch) == 200 or i == len(files) - 1:
            parts.append(pd.concat(batch).groupby(["k", "e", "y", "r"]).n.sum().reset_index())
            batch = []
    ent = pd.concat(parts).groupby(["k", "e", "y", "r"]).n.sum().reset_index()
    del parts
    rows = []
    for Y in YEARS:
        w = ent[(ent.y >= Y - 3) & (ent.y <= Y - 1)]
        tot = w.groupby(["k", "e"]).n.sum()
        bad = w[(w.r > 0) & (w.r <= Y - 1)].groupby(["k", "e"]).n.sum()
        n1 = ent[ent.y == Y - 1].groupby(["k", "e"]).n.sum()
        n3 = ent[ent.y == Y - 3].groupby(["k", "e"]).n.sum()
        r = pd.DataFrame({"tot": tot}).join(bad.rename("bad")).join(n1.rename("n1")).join(n3.rename("n3")).fillna(0)
        r["Y"] = Y
        rows.append(r.reset_index())
    rates = pd.concat(rows)
    rates["k"] = rates.k.map({v: c for c, v in KIND.items()})
    rates["rate"] = rates.bad / rates.tot.clip(lower=1)
    rates.to_parquet(OUT / "rates.parquet", index=False)
    log["rate_rows"] = int(len(rates))
    json.dump(log, open(RUN / "results" / "tables" / "reduce_log.json", "w"), indent=1)
    print(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
