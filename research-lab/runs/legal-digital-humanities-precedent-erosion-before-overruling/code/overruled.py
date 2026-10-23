"""Treatment assignment (no outcome is computed here).

  overruled.py   data/raw/overruled_wiki.txt (Wikipedia list, CC BY-SA, wikitext) -> pairs (overruled, overruling) with
                 U.S. Reports cites, years and doctrine heading; both sides linked to CourtListener clusters through the
                 citations table (volume, "U.S.", page); SCDB 2026-01 case-centred data adds issue area and the
                 precedentAlteration flag of the overruling decision.
                 -> results/tables/overruled_pairs.csv, results/tables/overruled_coverage.json
"""
import csv
import io
import json
import re
import sys
from pathlib import Path

import indexed_bzip2 as ibz2
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
CL = RUN / "data" / "cl_raw"
T = RUN / "results" / "tables"
CITE = re.compile(r"(\d+)\s+U\.\s?S\.\s+(\d+)")
YEAR = re.compile(r"\((\d{4})\)")
NAME = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]|''([^']+)''")
csv.field_size_limit(sys.maxsize)


def parse():
    lines = (RAW / "overruled_wiki.txt").read_text().splitlines()
    rows, h2, h3, sub, cells = [], "", "", "", []
    for ln in lines + ["|-"]:
        if ln.startswith("==") and not ln.startswith("==="):
            h2 = ln.strip("= ")
        elif ln.startswith("==="):
            h3 = ln.strip("= ")
        elif ln.startswith(";"):
            sub = ln[1:].strip()
        elif ln.startswith("|-") or ln.startswith("|}"):
            if len(cells) >= 2:
                rows.append({"section": h2, "subsection": h3, "doctrine": sub, "overruled_raw": cells[0], "overruling_raw": cells[1]})
            cells = []
        elif ln.startswith("|") and not ln.startswith("|+"):
            cells.append(ln[1:].strip())
    out = []
    for r in rows:
        a, b = CITE.findall(r["overruled_raw"]), CITE.findall(r["overruling_raw"])
        ya, yb = YEAR.findall(r["overruled_raw"]), YEAR.findall(r["overruling_raw"])
        if not (a and b and ya and yb):
            continue
        # a cell may list several overruled decisions; each is a pair with the overruling decision
        for (v, p), y in zip(a, ya):
            out.append({**{k: r[k] for k in ("section", "subsection", "doctrine")},
                        "overruled_cite": f"{v} U.S. {p}", "overruled_year": int(y),
                        "overruling_cite": f"{b[0][0]} U.S. {b[0][1]}", "overruling_year": int(yb[0])})
    return pd.DataFrame(out).drop_duplicates(["overruled_cite", "overruling_cite"])


def us_cite_map():
    f = ibz2.open(str(CL / "citations.csv.bz2"), parallelization=4)
    r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline=""), escapechar="\\", doublequote=False)
    head = next(r)
    iv, ir, ip, ic = (head.index(k) for k in ("volume", "reporter", "page", "cluster_id"))
    m = {}
    for row in r:
        if len(row) == len(head) and row[ir] == "U.S.":
            m.setdefault(f"{row[iv]} U.S. {row[ip]}", set()).add(int(row[ic]))
    return m


def main():
    p = parse()
    m = us_cite_map()
    for side in ("overruled", "overruling"):
        p[f"{side}_clusters"] = p[f"{side}_cite"].map(lambda c: ";".join(map(str, sorted(m.get(c, [])))))
    sc = pd.read_csv(next((RAW / "scdb").glob("*.csv")), encoding="latin-1", low_memory=False)
    sc = sc[["caseId", "usCite", "term", "issueArea", "precedentAlteration", "caseName", "dateDecision"]]
    p = p.merge(sc.rename(columns={c: f"overruled_scdb_{c}" for c in sc.columns}), left_on="overruled_cite",
                right_on="overruled_scdb_usCite", how="left")
    p = p.merge(sc.rename(columns={c: f"overruling_scdb_{c}" for c in sc.columns}), left_on="overruling_cite",
                right_on="overruling_scdb_usCite", how="left")
    p.to_csv(T / "overruled_pairs.csv", index=False)
    alt = sc[(sc.precedentAlteration == 1) & sc.term.between(1960, 2024)]
    cov = {"pairs": int(len(p)), "overruled_linked_to_one_cluster": int((p.overruled_clusters.str.count(";") == 0).sum() - (p.overruled_clusters == "").sum()),
           "overruled_unlinked": int((p.overruled_clusters == "").sum()), "overruling_unlinked": int((p.overruling_clusters == "").sum()),
           "overruled_multi_cluster": int((p.overruled_clusters.str.count(";") > 0).sum()),
           "overruling_1960_2024": int(p.overruling_year.between(1960, 2024).sum()),
           "overruling_with_scdb_precedentAlteration_1": int((p.overruling_scdb_precedentAlteration == 1).sum()),
           "scdb_precedentAlteration_1960_2024": int(len(alt)),
           "scdb_alterations_not_in_wiki": int((~alt.usCite.isin(set(p.overruling_cite))).sum())}
    (T / "overruled_coverage.json").write_text(json.dumps(cov, indent=1))
    print(json.dumps(cov, indent=1))
    print(p.groupby("section").size())


if __name__ == "__main__":
    main()
