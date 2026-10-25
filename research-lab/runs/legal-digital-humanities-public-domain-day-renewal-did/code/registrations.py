"""Registrations and renewal status (plan section 1). Reads no Open Library data.

A-class entries of the NYPL Catalog of Copyright Entries XML, 1923-1930: registration number, first author name, title,
registration date (regDate, else copyDate, else the volume year). A registration is renewed if a renewal's original
registration number equals it, the renewal's original date is within one year of the registration date, and the
titles match (rapidfuzz token_set_ratio >= 60). Expiry for renewed books: 1 January of (registration year + 96).
D2 (after review): the renewal TSVs have two schemas (author/title/rdat and auth/titl/dreg), now coalesced; renewal
rows with an empty title field (1,405 date-matched rows for 1923-1930 registrations) fall back to the entry's full
text; and the title score is the better of the raw renewal title and the renewal title with the author's name tokens
removed (renewal entries are often prefixed "SURNAME, GIVEN.").
Writes data/registrations.parquet and results/tables/registrations_summary.json.
"""
import glob
import json
import re
from pathlib import Path

import pandas as pd
from lxml import etree
from rapidfuzz import fuzz

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
WORD = re.compile(r"[a-z0-9]+")


def norm(s):
    return " ".join(WORD.findall((s or "").lower()))


def text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def registrations():
    rows = []
    for y in range(1923, 1931):
        for f in sorted(glob.glob(str(RAW / "cce-registrations" / "xml" / str(y) / "*.xml"))):
            for _, el in etree.iterparse(f, tag="copyrightEntry", recover=True, huge_tree=True):
                rn = (el.get("regnum") or "").replace(" ", "").upper()
                if rn.startswith("A"):
                    an = el.find(".//authorName")
                    t = el.find("title")
                    d = el.find(".//regDate")
                    d = d if d is not None else el.find(".//copyDate")
                    date = (d.get("date") if d is not None else None) or f"{y}-01-01"
                    rows.append({"regnum": rn, "entry_id": el.get("id"), "vol_year": y, "author": text(an),
                                 "title": text(t), "reg_date": date[:10]})
                el.clear()
    r = pd.DataFrame(rows)
    r["reg_year"] = pd.to_numeric(r.reg_date.str[:4], errors="coerce").fillna(r.vol_year).astype(int)
    return r


def main():
    r = registrations()
    ren = pd.concat([pd.read_csv(f, sep="\t", dtype=str) for f in glob.glob(str(RAW / "cce-renewals" / "data" / "*.tsv"))],
                    ignore_index=True)
    for a, b in (("title", "titl"), ("author", "auth"), ("rdat", "dreg")):      # D2: two TSV schemas
        ren[a] = ren[a].fillna(ren[b]) if a in ren else ren[b]
    ren["title"] = ren.title.fillna(ren.full_text)          # D2: rows with an empty title field keep it in full_text
    ren["oreg"] = ren.oreg.fillna("").str.replace(" ", "").str.upper()
    ren = ren[ren.oreg.str.startswith("A")]
    ren["oyear"] = pd.to_numeric(ren.odat.str[:4], errors="coerce")
    m = r.merge(ren[["oreg", "oyear", "title", "author", "id", "rdat"]].rename(
        columns={"title": "ren_title", "author": "ren_author", "id": "ren_id"}), left_on="regnum", right_on="oreg", how="left")
    m["year_ok"] = (m.oyear - m.reg_year).abs() <= 1

    def sim(t, rt, a1, a2):
        if not isinstance(rt, str):
            return 0
        s1 = fuzz.token_set_ratio(norm(t), norm(rt))
        names = set(norm(a1).split()) | set(norm(a2 if isinstance(a2, str) else "").split())
        stripped = " ".join(w for w in norm(rt).split() if w not in names)          # D2: drop author-name tokens
        return max(s1, fuzz.token_set_ratio(norm(t), stripped) if stripped else 0)
    m["title_sim"] = [sim(t, rt, a1, a2) for t, rt, a1, a2 in zip(m.title, m.ren_title, m.author, m.ren_author)]
    m["ren_ok"] = m.year_ok & (m.title_sim >= 60)
    g = m.groupby("entry_id").agg(renewed=("ren_ok", "max"), any_number_match=("oreg", lambda s: s.notna().any()),
                                  ren_id=("ren_id", lambda s: ";".join(sorted({x for x in s.dropna()}))))
    r = r.merge(g, left_on="entry_id", right_index=True, how="left")
    r["renewed"] = r.renewed.fillna(False).astype(bool)
    r["pd_year"] = r.reg_year + 96
    r.to_parquet(RUN / "data" / "registrations.parquet", index=False)
    summ = {"registrations": int(len(r)), "by_year": r.groupby("reg_year").agg(n=("entry_id", "size"), renewed=("renewed", "sum")).astype(int).to_dict(orient="index"),
            "number_matched_but_rejected": int((r.any_number_match & ~r.renewed).sum())}
    json.dump(summ, open(RUN / "results" / "tables" / "registrations_summary.json", "w"), indent=1, default=str)
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
