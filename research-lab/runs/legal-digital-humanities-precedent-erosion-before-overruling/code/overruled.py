"""Treatment assignment (no outcome is computed here).

  overruled.py   data/raw/overruled_wiki.txt (Wikipedia list, CC BY-SA, wikitext) -> pairs (overruled, overruling) with
                 U.S. Reports cites, years and doctrine heading; both sides linked to CourtListener clusters through the
                 citations table (volume, "U.S.", page); SCDB 2026-01 case-centred data adds issue area and the
                 precedentAlteration flag of the overruling decision.
                 -> results/tables/overruled_pairs.csv, results/tables/overruled_coverage.json, coverage.json (G2)

D2 (after review): the U.S.-cite pattern accepts old-reporter parentheticals ("80 U.S. (13 Wall.) 29"); every table row
is counted as parsed or dropped with a reason; SCDB alterations with a blank usCite (2016-2021 terms) are matched to
the list by first-party name and year when counting coverage. The list was taken from Wikipedia after an attempt to
fetch the Constitution Annotated table returned a Cloudflare challenge page (data/raw/conan_overruled.html); the
Wikipedia page is self-tagged as an incomplete list.
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
CITE = re.compile(r"(\d+)\s+U\.\s?S\.\s+(?:\([^)]*\)\s*)?(\d+)")
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
    sys.path.insert(0, str(RUN.parents[1] / "tools"))
    from coverage import Coverage
    cov = Coverage("wiki_rows", T / "coverage.json")
    for i, r in enumerate(rows):
        a, b = CITE.findall(r["overruled_raw"]), CITE.findall(r["overruling_raw"])
        ya, yb = YEAR.findall(r["overruled_raw"]), YEAR.findall(r["overruling_raw"])
        cov.attempt(i)
        if not (a and b and ya and yb):
            cov.drop(i, "no U.S. cite or year in the overruled cell" if not (a and ya) else "no U.S. cite or year in the overruling cell")
            continue
        cov.ok(i)
        # a cell may list several overruled decisions; each is a pair with the overruling decision
        for (v, p), y in zip(a, ya):
            out.append({**{k: r[k] for k in ("section", "subsection", "doctrine")},
                        "overruled_cite": f"{v} U.S. {p}", "overruled_year": int(y),
                        "overruling_cite": f"{b[0][0]} U.S. {b[0][1]}", "overruling_year": int(yb[0])})
    cov.save()
    return pd.DataFrame(out).drop_duplicates(["overruled_cite", "overruling_cite"])


def parse_raw_overruling_text():
    """(overruling cell text, overruling year) for every table row with a year, for name matching."""
    lines = (RAW / "overruled_wiki.txt").read_text().splitlines()
    out, cells = [], []
    for ln in lines + ["|-"]:
        if ln.startswith("|-") or ln.startswith("|}"):
            if len(cells) >= 2 and YEAR.findall(cells[1]):
                out.append((cells[1], int(YEAR.findall(cells[1])[0])))
            cells = []
        elif ln.startswith("|") and not ln.startswith("|+"):
            cells.append(ln[1:].strip())
    return out


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
           "scdb_alterations_not_in_wiki_by_cite": int((~alt.usCite.isin(set(p.overruling_cite))).sum())}
    # D2: SCDB leaves usCite blank for recent terms; match those by first-party name and year instead
    raw = parse_raw_overruling_text()
    def on_list(r):
        if isinstance(r.usCite, str) and r.usCite in set(p.overruling_cite):
            return True
        if isinstance(r.usCite, str) and r.usCite.strip():
            return False
        party = re.sub(r"[^a-z]", "", str(r.caseName).split(" v.")[0].lower())[:12]
        return any(party and party in re.sub(r"[^a-z]", "", t.lower()) and abs(y - int(r.term)) <= 1 for t, y in raw)
    flags = alt.apply(on_list, axis=1)
    cov["scdb_alterations_blank_uscite"] = int((alt.usCite.fillna("").str.strip() == "").sum())
    cov["scdb_alterations_on_list"] = int(flags.sum())
    cov["scdb_alterations_not_on_list"] = int((~flags).sum())
    cov["share_of_scdb_alterations_on_list"] = round(float(flags.mean()), 3)
    (T / "overruled_coverage.json").write_text(json.dumps(cov, indent=1))
    print(json.dumps(cov, indent=1))
    print(p.groupby("section").size())


if __name__ == "__main__":
    main()
