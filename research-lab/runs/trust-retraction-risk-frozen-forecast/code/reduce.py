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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(P1 / "*.npz")), key=lambda f: Path(f).stem.split("_", 1)[1])   # by partition date
    W = {k: [] for k in ("wid", "year", "src", "host", "ret", "order")}
    AF_a, AF_y, AR_a, AR_r, ENT = [], [], [], [], []
    for i, f in enumerate(files):
        z = np.load(f)
        for k in ("wid", "year", "src", "host", "ret"):
            W[k].append(z[k])
        W["order"].append(np.full(len(z["wid"]), i, dtype=np.int32))
        AF_a.append(z["af_a"]); AF_y.append(z["af_y"]); AR_a.append(z["ar_a"]); AR_r.append(z["ar_r"])
        ENT.append(pd.DataFrame({"k": z["ent_k"], "e": z["ent_e"], "y": z["ent_y"], "r": z["ent_r"], "n": z["ent_n"]}))
    W = {k: np.concatenate(v) for k, v in W.items()}
    o = np.lexsort((W["order"], W["wid"]))
    wid = W["wid"][o]
    last = np.r_[wid[1:] != wid[:-1], True]                      # keep the latest partition's copy
    keep = o[last]
    log = {"rows": int(len(wid)), "unique_works": int(last.sum()), "duplicates_dropped": int((~last).sum())}
    for k in ("wid", "year", "src", "host", "ret"):
        np.save(OUT / f"w_{k}.npy", W[k][keep])
    del W
    af = pd.DataFrame({"a": np.concatenate(AF_a), "y": np.concatenate(AF_y)}).groupby("a").y.min()
    np.save(OUT / "a_id.npy", af.index.values); np.save(OUT / "a_first.npy", af.values.astype(np.int16))
    ar = pd.DataFrame({"a": np.concatenate(AR_a), "r": np.concatenate(AR_r)}).sort_values(["a", "r"])
    np.save(OUT / "ar_a.npy", ar.a.values); np.save(OUT / "ar_r.npy", ar.r.values.astype(np.int16))
    log.update({"authors": int(len(af)), "retracted_authorships": int(len(ar))})
    ent = pd.concat(ENT).groupby(["k", "e", "y", "r"]).n.sum().reset_index()
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
    rates["rate"] = rates.bad / rates.tot.clip(lower=1)
    rates.to_parquet(OUT / "rates.parquet", index=False)
    log["rate_rows"] = int(len(rates))
    json.dump(log, open(RUN / "results" / "tables" / "reduce_log.json", "w"), indent=1)
    print(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
