"""PHARMAC listings from the monthly XML archives (plan D2). For every community Schedule and HML edition, every
Chemical (with its section and its formulation names) is recorded. Writes data/pharmac_listings.csv
(edition, source, section, chemical, formulations)."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
X = RUN / "data" / "raw" / "pharmac" / "xml"
NS = "{http://schedule.pharmac.govt.nz/2006/07/Schedule#}"


def edition(path):
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", path.name)
    return f"{m.group(1)}-{m.group(2)}-01"


def parse(path, source):
    root = ET.parse(path).getroot()
    out = []
    for sec in root.iter(NS + "Section"):
        sid = sec.get("ID")
        for ch in sec.iter(NS + "Chemical"):
            name = ch.findtext(NS + "Name") or ""
            forms = [f.findtext(NS + "Name") or "" for f in ch.iter(NS + "Formulation")]
            out.append(dict(edition=edition(path), source=source, section=sid, chemical=name.strip(),
                            formulations=" || ".join(x.strip() for x in forms)[:2000]))
    return out


def main(paths=None):
    rows = []
    for source in ("schedule", "HML"):
        for p in sorted((X / source).glob("*.xml")) if paths is None else [Path(x) for x in paths if source in x]:
            rows += parse(p, source)
    d = pd.DataFrame(rows).drop_duplicates()
    d.to_csv(RUN / "data" / "pharmac_listings.csv", index=False)
    print(len(d), "rows;", d.groupby("source").edition.nunique().to_dict(), d.section.value_counts().to_dict())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
