"""Step 0: read the SRA3 SciVal Topic / Topic Cluster list (Research Services for the Research and Innovation Office).

The workbook has two sheets, "SRA3_Topics" and "SRA3_Topic Clusters". Each row is a SciVal Topic
or Topic Cluster from the core dataset of UoA's highest-performing T/TCs for 2020-2024, with:
  col B "Included in dataset": Research Services' relevance call for this SRA (y / n / ?)
  col C "Narrative team comments": the SRA narrative team (SME) correction, where given
The final status is the SME call where one was given, otherwise the Research Services call.

Usage: parse_scival.py <workbook.xlsx>   -> data/scival_sra3.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

import openpyxl

OUT = Path(__file__).resolve().parents[1] / "data" / "scival_sra3.json"
SHEETS = {"SRA3_Topics": "topic", "SRA3_Topic Clusters": "cluster"}


def norm_flag(v):
    s = ("" if v is None else str(v)).strip().lower()
    return s if s in ("y", "n", "?") else ("" if not s else "other:" + s)


def main(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    rows = []
    for sheet, kind in SHEETS.items():
        ws = wb[sheet]
        header = [c.value for c in ws[1]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            name = (r[0] or "").strip() if isinstance(r[0], str) else r[0]
            if not name:
                if any(v not in (None, "") for v in r):
                    raise SystemExit(f"row with values but no name in {sheet}: {r}")
                continue
            rs, sme = norm_flag(r[1]), norm_flag(r[2] if len(r) > 2 else None)
            if rs.startswith("other") or sme.startswith("other"):
                raise SystemExit(f"unexpected flag in {sheet}: {r}")
            final = sme or rs
            rows.append(dict(kind=kind, name=name, rs=rs, sme=sme, final=final, sheet=sheet))
        print(f"{sheet}: header={header}")
    names = Counter((r["kind"], r["name"]) for r in rows)
    dups = [k for k, c in names.items() if c > 1]
    for kind in ("topic", "cluster"):
        sub = [r for r in rows if r["kind"] == kind]
        print(f"{kind}: {len(sub)} rows; RS {dict(Counter(r['rs'] for r in sub))}; "
              f"SME {dict(Counter(r['sme'] or '-' for r in sub))}; final {dict(Counter(r['final'] for r in sub))}")
        changed = [r for r in sub if r["sme"] and r["sme"] != r["rs"]]
        print(f"  SME changed {len(changed)}: " + "; ".join(f"{r['name']} ({r['rs']}->{r['sme']})" for r in changed))
    print("duplicates:", dups)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main(sys.argv[1])
