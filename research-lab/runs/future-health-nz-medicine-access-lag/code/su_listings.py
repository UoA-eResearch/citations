"""New listings from the Schedule Update PDFs (deviations D4): the detailed "New Listings - effective <date>"
sections, whose chemical names are upper-case headers. Used to fill the community-Schedule XML archive's gap
(June 2024 - December 2025 and January 2018), and kept for validation. Writes data/su_listings.csv
(su_file, effective, chemical)."""
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
HDR = re.compile(r"New Listings\s*[–—-]\s*effective\s+(\d{1,2}\s+\w+\s+\d{4})", re.I)
END = re.compile(r"^(Changes to |Delisted Items|Items to be Delisted|Section H |Index\b|Decisions? |Changes in )", re.I)
CHEM = re.compile(r"^([A-Z][A-Z0-9 ,'()/\-–+]{3,}?)(?:\s+[–-]\s+.*)?$")


def parse(txt):
    out, eff = [], None
    for line in txt.splitlines():
        s = line.strip()
        m = HDR.search(s)
        if m:
            eff = pd.to_datetime(m.group(1), errors="coerce"); continue
        if eff is None:
            continue
        if END.match(s):
            eff = None; continue
        c = CHEM.match(s)
        if c and sum(ch.isupper() for ch in c.group(1)) >= 4 and not re.match(r"^(PCT|S29|HP\d|SA\d|OP|BSF)\b", c.group(1)):
            out.append((eff, c.group(1).strip(" –-")))
    return out


def main():
    rows = []
    for t in sorted((RUN / "data" / "su_text").glob("*.txt")):
        for eff, chem in parse(t.read_text()):
            rows.append(dict(su_file=t.stem, effective=eff.date() if pd.notna(eff) else None, chemical=chem))
    d = pd.DataFrame(rows).drop_duplicates()
    d.to_csv(RUN / "data" / "su_listings.csv", index=False)
    print(len(d), "listing rows from", d.su_file.nunique(), "updates")


if __name__ == "__main__":
    sys.exit(main())
