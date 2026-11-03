"""TIC v8.2 identifiers for sample binaries with P_orb < 12 d (plan section 1).

A DR3 source is matched only if it has exactly one DR2 neighbour in gaiadr3.dr2_neighbourhood and that DR2 source
has exactly one TIC row that is not flagged as a duplicate or artefact.

  tic_match.py -> data/tic.parquet, results/tables/coverage.json (section "tic_match")
"""
import sys
import time
from pathlib import Path

import pandas as pd
from astroquery.mast import Catalogs

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402
BATCH = 400


def main():
    s = pd.read_parquet(D / "sample.parquet")
    s = s[s.period < 12]
    nb = pd.read_parquet(D / "gaia_dr2_neighbours.parquet")
    nb = nb[nb.dr3_source_id.isin(s.source_id)]
    k = nb.groupby("dr3_source_id").size()
    one = nb[nb.dr3_source_id.isin(k[k == 1].index)]
    ids = sorted(set(one.dr2_source_id.astype("int64")))
    out_f = D / "tic_raw.parquet"
    got = [pd.read_parquet(out_f)] if out_f.exists() else []
    done = set(got[0].GAIA.astype("int64")) if got else set()
    todo = [i for i in ids if i not in done]
    for b in range(0, len(todo), BATCH):
        chunk = [str(i) for i in todo[b:b + BATCH]]
        for attempt in range(5):
            try:
                t = Catalogs.query_criteria(catalog="Tic", GAIA=chunk).to_pandas(); break
            except Exception as e:
                print("retry", b, attempt, str(e)[:80], flush=True); time.sleep(30 * (attempt + 1))
        got.append(t[["ID", "GAIA", "Tmag", "disposition", "ra", "dec"]].astype({"GAIA": "int64"}))
        if (b // BATCH) % 10 == 0:
            pd.concat(got).to_parquet(out_f); print(b + len(chunk), "of", len(todo), flush=True)
    raw = pd.concat(got).drop_duplicates() if got else pd.DataFrame(columns=["ID", "GAIA", "Tmag", "disposition"])
    raw.to_parquet(out_f)
    ok = raw[~raw.disposition.fillna("").str.upper().isin(["DUPLICATE", "ARTIFACT"])]
    per = ok.groupby("GAIA").size()
    ok = ok[ok.GAIA.isin(per[per == 1].index)]
    m = one.merge(ok, left_on="dr2_source_id", right_on="GAIA").rename(columns={"ID": "tic", "dr3_source_id": "source_id"})
    m = m[["source_id", "dr2_source_id", "tic", "Tmag"]].astype({"tic": "int64"})
    m.to_parquet(D / "tic.parquet")
    c = Coverage("tic_match", T / "coverage.json")
    c.add_counts(ok=len(m), drops={"no or several DR2 neighbours": len(s) - len(one),
                                   "DR2 source without a unique clean TIC row": len(one) - len(m)})
    c.save()
    print(len(m), "of", len(s), "matched")


if __name__ == "__main__":
    main()
