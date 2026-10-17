"""Validation V3 (plan section 6, descriptive): the treatment the authors call best, from the abstract, against the
full-network top-ranked treatment. Sample: 30 networks at random from those whose full fit succeeded (seed 20261019).
Abstracts are retrieved from Europe PMC by title (1 s apart) into data/validation/v3/<record>.json; a sheet for hand
adjudication is written to data/validation/v3_sheet.txt. The adjudication is entered in results/tables/v3_published.csv."""
import json
import random
import re
import time
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "validation" / "v3"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def main():
    fits = {json.loads(l)["record"]: json.loads(l)["fits"][0] for l in open(RUN / "data" / "fits_full.jsonl")}
    ok = sorted(r for r, f in fits.items() if not f.get("error"))
    pick = random.Random(20261019).sample(ok, 30)
    cat = pd.read_csv(RUN / "data" / "raw" / "catalog.csv", sep=";", dtype=str).set_index("Record ID")
    dr = pd.read_csv(RUN / "results" / "tables" / "direction.csv", dtype={"record": str}).set_index("record")
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = []
    for rid in pick:
        f = OUT / f"{rid}.json"
        title = cat.loc[rid, "Title"]
        if not f.exists():
            q = 'TITLE:"' + re.sub(r'["\[\]]', " ", title)[:200] + '"'
            r = requests.get(EPMC, params=dict(query=q, resultType="core", format="json", pageSize=3), timeout=60)
            f.write_text(r.text); time.sleep(1)
        res = json.loads(f.read_text()).get("resultList", {}).get("result", [])
        ab = res[0].get("abstractText", "") if res else ""
        trt = json.load(open(RUN / "data" / "std" / f"{rid}.trt.json"))
        fit = fits[rid]
        order = sorted(zip(fit["trts"], fit["pscore"]), key=lambda x: -x[1])
        sheet.append(f"=== {rid} | {title}\nPO: {cat.loc[rid, 'Primary Outcome']} | {cat.loc[rid, 'Description of the outcome(s)']} | "
                     f"small_values={dr.loc[rid, 'small_values']}\nranking: " +
                     ", ".join(f"{t} {trt.get(str(t), '?')[:25]} {p:.2f}" for t, p in order) +
                     f"\nabstract ({len(res)} hits): {re.sub(r'<[^>]+>', '', ab)}\n")
    (RUN / "data" / "validation" / "v3_sheet.txt").write_text("\n".join(sheet))
    pd.DataFrame({"record": pick}).to_csv(RUN / "data" / "validation" / "v3_sample.csv", index=False)
    print(len(pick), "networks;", sum(1 for s in sheet if "(0 hits)" not in s), "with an abstract hit")


if __name__ == "__main__":
    main()
