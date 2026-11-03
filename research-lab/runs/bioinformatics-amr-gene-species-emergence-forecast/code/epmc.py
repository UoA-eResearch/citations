"""Literature check (plan section 2; run in D3): the 20 highest-ranked true emergences under the preregistered model
(preregistered seed and hyperparameters), each searched in Europe PMC for publications before 2023 that mention the
gene symbol and the species. A hit counts as foreseeable from the literature. Descriptive only.

  epmc.py -> results/tables/epmc.csv
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402
import d3_fixes as F  # noqa: E402

tr, te = pd.read_parquet(A.D / "task_train.parquet"), pd.read_parquet(A.D / "task_test.parquet")
te = te.assign(p=F.fit(tr, te, A.FULL, A.SEED))
te["rank"] = te.p.rank(ascending=False, method="min").astype(int)
hits = te[te.y == 1].nsmallest(20, "p" if False else "rank")
rows = []
for r in hits.itertuples():
    q = f'"{r.gene}" AND "{r.species}" AND FIRST_PDATE:[1900-01-01 TO 2022-12-31]'
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": q, "format": "json", "pageSize": 1})
    n = json.loads(urllib.request.urlopen(url, timeout=60).read()).get("hitCount", 0)
    rows.append((r.gene, r.species, int(r.rank), int(n)))
    time.sleep(1)
o = pd.DataFrame(rows, columns=["gene", "species", "model_rank", "europepmc_hits_before_2023"])
o.to_csv(A.T / "epmc.csv", index=False)
print(o.to_string(index=False)); print("with a prior report:", int((o.europepmc_hits_before_2023 > 0).sum()), "of", len(o))
