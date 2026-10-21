"""One pass over the NCBI BioSample dump (plan sections 1-2): drop human samples, classify the country field, and
write a compact per-sample table.

  data/samples/part_NNN.parquet   one row per non-human BioSample submitted from 2019-01-01
  results/tables/parse_log.json   counts read, dropped as human, kept, and by class

Columns: accession, submission_date, publication_date, taxonomy_id, organism, package, owner, country_raw,
country_class (usable/placeholder/malformed/absent), country_resolved, host, bioprojects, and, for samples
submitted 2021-06-01 to 2025-05-31 only, the evidence text used by limb 2 (title, isolation_source, lat_lon,
other attribute values, description comment; each truncated).
"""
import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
DUMP = RUN / "data" / "raw" / "ncbi" / "biosample_set.xml.gz"
OUT = RUN / "data" / "samples"
TAB = RUN / "results" / "tables"
KEEP_FROM = "2019-01-01"
EVIDENCE = ("2021-06-01", "2025-05-31")
CHUNK = 1_000_000
HUMAN_TAXA = {"9606"}
HUMAN_WORD = re.compile(r"\bhomo sapiens\b|\bhuman\b", re.I)


def is_human(taxid, organism, package):
    return taxid in HUMAN_TAXA or bool(HUMAN_WORD.search(organism or "")) or bool(HUMAN_WORD.search(package or ""))


def text(el, path):
    x = el.find(path)
    return (x.text or "").strip() if x is not None and x.text else ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = {"read": 0, "human_dropped": 0, "before_2019": 0, "kept": 0}
    rows, part = [], 0
    with gzip.open(DUMP, "rb") as fh:
        for _, el in etree.iterparse(fh, events=("end",), tag="BioSample", huge_tree=True):
            log["read"] += 1
            sub = (el.get("submission_date") or "")[:10]
            org = el.find("Description/Organism")
            taxid = org.get("taxonomy_id") if org is not None else ""
            organism = (org.get("taxonomy_name") if org is not None else "") or text(el, "Description/Organism/OrganismName")
            package = text(el, "Package")
            if is_human(taxid, organism, package):
                log["human_dropped"] += 1
            elif sub < KEEP_FROM:
                log["before_2019"] += 1
            else:
                attrs = {}
                for a in el.iterfind("Attributes/Attribute"):
                    k = (a.get("harmonized_name") or a.get("attribute_name") or "").lower()
                    if k and k not in attrs:
                        attrs[k] = (a.text or "").strip()
                raw = attrs.get("geo_loc_name", attrs.get("country"))
                cls, resolved = countries.classify(raw)
                bp = [l.get("label") or l.text for l in el.iterfind("Links/Link") if l.get("target") == "bioproject"]
                r = {"accession": el.get("accession"), "submission_date": sub,
                     "publication_date": (el.get("publication_date") or "")[:10], "taxonomy_id": taxid,
                     "organism": organism[:120], "package": package, "owner": text(el, "Owner/Name")[:160],
                     "country_raw": (raw or "")[:120] if raw is not None else None, "country_class": cls,
                     "country_resolved": resolved, "host": attrs.get("host", "")[:80],
                     "bioprojects": ";".join(b for b in bp if b)[:200]}
                if EVIDENCE[0] <= sub <= EVIDENCE[1]:
                    other = "; ".join(f"{k}={v}" for k, v in attrs.items()
                                      if k not in ("geo_loc_name", "country") and v)[:600]
                    r.update(title=text(el, "Description/Title")[:200],
                             isolation_source=attrs.get("isolation_source", "")[:200],
                             lat_lon=attrs.get("lat_lon", "")[:60], attributes_text=other,
                             comment=" ".join(p.text or "" for p in el.iterfind("Description/Comment/Paragraph"))[:400])
                rows.append(r)
                log["kept"] += 1
                log.setdefault("class_" + cls, 0)
                log["class_" + cls] += 1
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
            if len(rows) >= CHUNK:
                pd.DataFrame(rows).to_parquet(OUT / f"part_{part:03d}.parquet", index=False)
                rows, part = [], part + 1
                print(json.dumps(log), flush=True)
    if rows:
        pd.DataFrame(rows).to_parquet(OUT / f"part_{part:03d}.parquet", index=False)
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(log, open(TAB / "parse_log.json", "w"), indent=1)
    print(json.dumps(log), flush=True)


if __name__ == "__main__":
    main()
