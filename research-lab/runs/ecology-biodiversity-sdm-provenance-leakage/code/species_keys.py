"""Map SAGE's 5,771 species names to GBIF backbone species keys (as SAGE's gbif.py did with name_backbone).

-> data/registry/species_keys.csv: index, name, specieskey (backbone match), in_download_predicate, match_type
Records are later assigned to a SAGE species if their GBIF specieskey equals this key or their GBIF species name
equals the SAGE name.
"""
import csv
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
REG = RUN / "data" / "registry"
KEYS = set(json.loads((REG / "download_meta.json").read_text())["request"]["predicate"]["predicates"][0]["values"])


def one(row):
    name, idx = row
    for _ in range(4):
        try:
            u = "https://api.gbif.org/v1/species/match?kingdom=Plantae&name=" + urllib.parse.quote(name)
            d = json.load(urllib.request.urlopen(u, timeout=60))
            k = d.get("speciesKey")
            return {"index": idx, "name": name, "specieskey": k, "in_download_predicate": str(k) in KEYS,
                    "match_type": d.get("matchType"), "backbone_species": d.get("species")}
        except Exception:
            continue
    return {"index": idx, "name": name, "specieskey": None, "in_download_predicate": False, "match_type": "ERROR",
            "backbone_species": None}


def main():
    rows = [(r["Species Name"], int(r["Index"])) for r in csv.DictReader(open(RUN / "data" / "raw" / "species_names.csv"))]
    with ThreadPoolExecutor(16) as ex:
        out = list(ex.map(one, rows))
    with open(REG / "species_keys.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    n_in = sum(o["in_download_predicate"] for o in out)
    print(len(out), "species;", n_in, "keys in the download predicate;",
          sum(o["specieskey"] is None for o in out), "unmatched;", {t: sum(o["match_type"] == t for o in out)
                                                                     for t in ("EXACT", "FUZZY", "HIGHERRANK", "NONE", "ERROR")})


if __name__ == "__main__":
    main()
