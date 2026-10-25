"""GBIF registry metadata for every dataset in SAGE's download (provenance audit, step 1).

  registry.py fetch      -> data/registry/datasets/<key>.json (type, title, description, publisher, citation, ...)
  registry.py candidates -> data/registry/candidates.csv: datasets whose metadata mention a GIVD code or name of a
                            vegetation-plot database that supplies SAGE evaluation plots, or plot/relevé vocabulary
"""
import csv
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
REG = RUN / "data" / "registry"
DS = REG / "datasets"
DS.mkdir(parents=True, exist_ok=True)


def fetch_one(key):
    out = DS / f"{key}.json"
    if out.exists():
        return
    for _ in range(4):
        try:
            d = json.load(urllib.request.urlopen(f"https://api.gbif.org/v1/dataset/{key}", timeout=60))
            try:
                org = json.load(urllib.request.urlopen(f"https://api.gbif.org/v1/organization/{d['publishingOrganizationKey']}",
                                                      timeout=60))
                d["_publisher_title"] = org.get("title")
            except Exception:
                d["_publisher_title"] = None
            out.write_text(json.dumps(d))
            return
        except Exception:
            continue


def fetch():
    """Page through the dataset search API (title, description, publisher, type, keywords; 1,000 per page) by
    publishing country, keep datasets in SAGE's download, and fall back to per-dataset fetches for any missing."""
    keys = {r["datasetKey"] for r in json.loads((REG / "download_datasets.json").read_text())}
    countries = json.load(urllib.request.urlopen("https://api.gbif.org/v1/enumeration/country", timeout=60))
    got = 0
    for c in [x["iso2"] for x in countries] + [None]:
        off = 0
        while True:
            u = f"https://api.gbif.org/v1/dataset/search?limit=1000&offset={off}" + (f"&publishingCountry={c}" if c else "")
            d = json.load(urllib.request.urlopen(u, timeout=120))
            for r in d["results"]:
                if r["key"] in keys and not (DS / f"{r['key']}.json").exists():
                    r["_publisher_title"] = r.get("publishingOrganizationTitle")
                    (DS / f"{r['key']}.json").write_text(json.dumps(r)); got += 1
            off += 1000
            if d.get("endOfRecords") or off >= d["count"] or not c:
                break
    missing = [k for k in keys if not (DS / f"{k}.json").exists()]
    print("search pages gave", got, "; missing", len(missing), flush=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(fetch_one, missing))
    print(len(list(DS.glob("*.json"))), "of", len(keys))


def candidates():
    counts = {r["datasetKey"]: r["numberRecords"] for r in json.loads((REG / "download_datasets.json").read_text())}
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", usecols=["GIVD_ID", "Dataset", "Country"])
    givd = meta.groupby(["GIVD_ID", "Dataset"]).size().reset_index(name="eval_rows")
    codes = set(givd["GIVD_ID"])
    vocab = re.compile(r"relev|vegetation[- ]plot|vegetation database|phytosocio|vegetationsaufnahm|sigmatis|turboveg|"
                       r"\bgivd\b|splot|\beva\b|european vegetation archive", re.I)
    rows = []
    for f in DS.glob("*.json"):
        d = json.loads(f.read_text())
        text = " ".join(str(d.get(k) or "") for k in ("title", "description", "_publisher_title", "keywords"))
        text += " " + json.dumps(d.get("citation") or {}) + " " + json.dumps(d.get("bibliographicCitations") or [])
        hit_codes = sorted(c for c in codes if c in text)
        if hit_codes or vocab.search(text) or d.get("type") == "SAMPLING_EVENT" and re.search(r"vegetat|plot", text, re.I):
            rows.append({"datasetKey": d["key"], "records_in_download": counts.get(d["key"], 0), "type": d.get("type"),
                         "title": d.get("title"), "publisher": d.get("_publisher_title"),
                         "givd_codes_in_metadata": ";".join(hit_codes),
                         "vocab": ";".join(sorted({m.group(0).lower() for m in vocab.finditer(text)}))})
    c = pd.DataFrame(rows).sort_values("records_in_download", ascending=False)
    c.to_csv(REG / "candidates.csv", index=False)
    givd.to_csv(REG / "eval_givd_sources.csv", index=False)
    print(len(c), "candidates;", (c["givd_codes_in_metadata"] != "").sum(), "mention a GIVD code")


if __name__ == "__main__":
    {"fetch": fetch, "candidates": candidates}[sys.argv[1]]()
