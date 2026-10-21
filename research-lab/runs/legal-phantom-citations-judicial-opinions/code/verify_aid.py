"""Reading aid for manual verification (plan section 4, step 7); decides nothing.

For every row of the verification sheets, adds the case name the index holds at the cited reporter-volume-page (and
at the nearest pages either side), and the sentence around the citation. Writes data/screen/aid_<sheet>.jsonl.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse as P  # noqa: E402

S = P.OUT
SHEETS = ["verify_screened_reliance.csv", "verify_screened_flag.csv", "verify_placebo_reliance.csv",
          "verify_placebo_flag.csv", "verify_misattributions_sample.csv"]
CITE = re.compile(r"^(\d+)\s+(.+?)\s+(\d+)$")


def near(rep, vol, page):
    i = P.G["keymap"].get((P.norm_reporter(rep), vol))
    if i is None:
        return []
    a, b = P.G["offs"][i], P.G["offs"][i + 1]
    pg = P.G["pages"][a:b]
    import numpy as np
    j = int(np.searchsorted(pg, page, side="right")) - 1
    out = []
    for k in (j - 1, j, j + 1):
        if 0 <= k < len(pg):
            r = P.row_of(int(P.G["clusters"][a + k]))
            out.append((int(pg[k]), P.name_at(r)[:80] if r is not None else "?"))
    return out


def main():
    P.init()
    for sh in SHEETS:
        p = S / sh
        if not p.exists():
            continue
        rows = list(csv.DictReader(open(p)))
        with open(S / f"aid_{sh.replace('.csv', '.jsonl')}", "w") as fh:
            for k, r in enumerate(rows):
                m = CITE.match((r.get("cite") or "").strip())
                nb = near(m.group(2), int(m.group(1)), int(m.group(3))) if m else []
                ctx = r.get("context") or ""
                c = r.get("cite") or ""
                pos = ctx.find(c.split()[0] + " " + c.split()[1]) if len(c.split()) > 1 else -1
                pos = pos if pos >= 0 else len(ctx) // 2
                snippet = " ".join(ctx[max(0, pos - 230): pos + 120].split())
                fh.write(json.dumps({"k": k, "opinion_id": r.get("opinion_id"), "date": r.get("date"), "cite": c,
                                     "cited_name": r.get("cited_name"), "best_name": r.get("best_name"),
                                     "near": nb, "snippet": snippet}) + "\n")
        print(sh, len(rows), flush=True)


if __name__ == "__main__":
    main()
