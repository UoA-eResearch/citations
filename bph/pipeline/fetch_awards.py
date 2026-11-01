"""Step 2: fetch public grant/award records led from the University of Auckland (OpenAlex awards).

Two routes, merged by award id:
  1. awards whose institution_awarded is UoA (covers HRC, Marsden, MBIE and many overseas funders)
  2. HRC awards whose lead investigator's recorded affiliation names the University of Auckland or
     Auckland UniServices (HRC records do not always carry institution_awarded)
These are public funder records (HRC research repository, Marsden lists, MBIE "who got funded",
etc.) as collected by OpenAlex. They are not the University's internal grant system.

Writes <WORK>/awards_raw.jsonl.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oa  # noqa: E402

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
UOA = "I154130895"
HRC = "F4320334749"
UOA_NAME = re.compile(r"\b(the )?university of auckland\b|auckland uniservices", re.I)


def main():
    out = {}
    for a in oa.paginate("/awards", {"filter": f"institution_awarded.id:{UOA}"}):
        a["_route"] = "institution_awarded"
        out[oa.short(a["id"])] = a
    n1 = len(out)
    n2 = 0
    for a in oa.paginate("/awards", {"filter": f"funder.id:{HRC}"}):
        aid = oa.short(a["id"])
        aff = (((a.get("lead_investigator") or {}).get("affiliation") or {}).get("name") or "")
        if aid not in out and UOA_NAME.search(aff) and not re.search(r"technology", aff, re.I):
            a["_route"] = "hrc_lead_affiliation"
            out[aid] = a
            n2 += 1
    with open(WORK / "awards_raw.jsonl", "w") as f:
        for a in out.values():
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    print(f"{n1} via institution_awarded + {n2} HRC via lead affiliation = {len(out)} awards; spent {oa.spent()}")


if __name__ == "__main__":
    main()
