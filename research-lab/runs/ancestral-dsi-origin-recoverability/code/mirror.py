"""Mirror agreement (plan section 5): 10,000 random window samples cross-checked against the ENA portal's country.

Run after limb 1 and limb 2 (logged in D7 as late but preregistered). Descriptive; no decision rule.
"""
import glob
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED, N = 20261022, 10_000


def window_samples():
    parts = []
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        d = pd.read_parquet(f, columns=["accession", "submission_date", "organism", "host", "country_raw",
                                        "country_class", "country_resolved"])
        d = d[(d.submission_date >= "2021-06-01") & (d.submission_date <= "2025-05-31")]
        d = d[~(d.organism.str.contains("metagenome", case=False, na=False)
                & d.host.str.contains(r"homo sapiens|\bhuman\b", case=False, na=False))]
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def ena(accs):
    body = urllib.parse.urlencode({"result": "sample", "includeAccessions": ",".join(accs),
                                   "fields": "sample_accession,country", "format": "tsv"}).encode()
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://www.ebi.ac.uk/ena/portal/api/search", data=body),
                                        timeout=120) as r:
                lines = r.read().decode().splitlines()
            return dict(l.split("\t", 1) if "\t" in l else (l, "") for l in lines[1:])
        except Exception:
            time.sleep(5 * (k + 1))
    raise RuntimeError("ENA unreachable")


def main():
    d = window_samples().sample(n=N, random_state=SEED).reset_index(drop=True)
    got = {}
    for i in range(0, N, 500):
        got.update(ena(d.accession.iloc[i:i + 500].tolist()))
        time.sleep(1)
    d["in_ena"] = d.accession.isin(got)
    d["ena_country"] = d.accession.map(got).fillna("")
    cls = [countries.classify(x if x else None) for x in d.ena_country]
    d["ena_class"] = [c[0] for c in cls]
    d["ena_resolved"] = [c[1] if len(c) > 1 else None for c in cls]
    f = d[d.in_ena]
    both = f[(f.country_class == "usable") & (f.ena_class == "usable")]
    out = {"sampled": N, "found_in_ena": int(d.in_ena.sum()),
           "biosample_class_counts": f.country_class.value_counts().to_dict(),
           "ena_class_counts": f.ena_class.value_counts().to_dict(),
           "usable_agreement": round(float(((f.country_class == "usable") == (f.ena_class == "usable")).mean()), 4),
           "usable_in_biosample_not_ena": int(((f.country_class == "usable") & (f.ena_class != "usable")).sum()),
           "usable_in_ena_not_biosample": int(((f.country_class != "usable") & (f.ena_class == "usable")).sum()),
           "both_usable": len(both),
           "same_country_when_both_usable": round(float((both.country_resolved == both.ena_resolved).mean()), 4)}
    d.to_csv(TAB / "mirror_sample.csv", index=False)
    json.dump(out, open(TAB / "mirror_agreement.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
