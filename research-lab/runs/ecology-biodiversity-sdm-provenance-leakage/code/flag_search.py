"""Provenance flag search: for each GIVD source database of SAGE evaluation plots, find GBIF datasets in SAGE's download
whose title, description or publisher name that database. Output is reviewed by hand; decisions go to
results/tables/provenance_flags.csv (committed before any overlap is computed).

-> data/registry/flag_search.csv
"""
import json
import re
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
REG = RUN / "data" / "registry"
# search patterns per GIVD source (eval Dataset name -> regex over title / description / publisher); names from GIVD
PAT = {
    "EU-NL-001": r"dutch vegetation database|landelijke vegetatie databank",
    "EU-CZ-001": r"czech national phytosociological|czech vegetation database|\bpladias\b(?!\.sk)",
    "EU-SK-001": r"slovak|central database of phytosociological|\bcdf\b",
    "EU-PL-001": r"polish vegetation database",
    "EU-DE-013": r"vegetweb",
    "EU-DE-014": r"german vegetation reference database|\bgvrd\b",
    "EU-FR-003": r"\bsophy\b",
    "EU-BE-002": r"inboveg",
    "SA-00-002": r"p[aá]ramo",
    "AF-00-001": r"west african vegetation database|\btava\b",
    "AF-BF-001": r"\btava\b|sahel",
    "EU-ES-001": r"\bsivim\b|vegetaci[oó]n ib[eé]rica",
    "NA-US-002": r"vegbank",
    "NA-US-006": r"carolina vegetation survey",
    "AU-AU-002": r"ausplots|\baekos\b|\btern\b.*(plot|vegetation)|vegetation.*\btern\b",
    "EU-GB-001": r"national vegetation classification|\bnvc\b",
    "EU-CH-005": r"swiss forest vegetation|\bwsl\b.*vegetation",
    "EU-00-011": r"basque",
    "EU-AT-001": r"austrian vegetation database|\bvinca\b",
    "EU-00-022": r"european mire|mire vegetation database",
    "EU-00-018": r"nordic vegetation database",
    "EU-SI-001": r"vegetation database of slovenia|slovenian vegetation",
    "EU-IT-001": r"vegitaly",
    "EU-IT-011": r"uniroma|sapienza",
    "EU-HR-002": r"croatian vegetation database",
    "EU-00-019": r"balkan vegetation database",
    "EU-00-013": r"balkan dry grassland|eu-00-013",
    "EU-UA-001": r"ukrainian grassland database|ukraine grassland",
    "EU-LV-001": r"latvian grassland",
    "EU-DK-002": r"novana|naturdatabase",
    "AS-TW-001": r"national vegetation database of taiwan|taiwan vegetation|植群",
    "AS-00-001": r"korea.*(vegetation|forest)",
    "EU-00-017": r"coastal vegetation database",
    "EU-00-016": r"ammophiletea",
    "EU-BG-001": r"bulgarian vegetation database",
    "EU-RU-002": r"volga",
    "EU-RU-011": r"tatarstan",
    "AS-RU-002": r"siberia.*vegetation|vegetation.*siberia",
    "NA-GL-001": r"greenland.*vegetation",
    "00-00-005": r"\bitex\b|international tundra experiment",
    "EU-GR-005": r"natura 2000.*greece|greece.*natura",
    "EU-IT-010": r"ispra",
}


def main():
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", usecols=["GIVD_ID", "Dataset"])
    ev = meta.groupby(["GIVD_ID", "Dataset"]).size().rename("eval_rows").reset_index()
    counts = {r["datasetKey"]: r["numberRecords"] for r in json.loads((REG / "download_datasets.json").read_text())}
    ds = []
    for f in (REG / "datasets").glob("*.json"):
        d = json.loads(f.read_text())
        ds.append((d["key"], d.get("title") or "", d.get("_publisher_title") or "", d.get("description") or "", d.get("type")))
    rows = []
    for givd, pat in PAT.items():
        rx = re.compile(pat, re.I)
        for key, title, pub, desc, typ in ds:
            where = [n for n, t in (("title", title), ("publisher", pub), ("description", desc)) if rx.search(t)]
            if where:
                m = rx.search(title + " " + pub + " " + desc)
                rows.append({"givd": givd, "datasetKey": key, "records_in_download": counts.get(key, 0), "type": typ,
                             "title": title[:110], "publisher": pub[:60], "matched_in": ";".join(where),
                             "match": m.group(0)[:40]})
    out = pd.DataFrame(rows).merge(ev, left_on="givd", right_on="GIVD_ID", how="left").drop(columns="GIVD_ID")
    out = out.sort_values(["givd", "records_in_download"], ascending=[True, False])
    out.to_csv(REG / "flag_search.csv", index=False)
    print(len(out), "hits;", out.givd.nunique(), "sources with hits")


if __name__ == "__main__":
    main()
