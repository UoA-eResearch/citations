"""Registrations and renewal status (plan section 1). Reads no Open Library data.

A-class entries of the NYPL Catalog of Copyright Entries XML, 1923-1930: registration number, first author name, title,
registration date (regDate, else copyDate, else the volume year). A registration is renewed if a renewal's original
registration number equals it, the renewal's original date is within one year of the registration date, and the
titles match (rapidfuzz token_set_ratio >= 60). Expiry for renewed books: 1 January of (registration year + 96).
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
    ren["oreg"] = ren.oreg.fillna("").str.replace(" ", "").str.upper()
    ren = ren[ren.oreg.str.startswith("A")]
    ren["oyear"] = pd.to_numeric(ren.odat.str[:4], errors="coerce")
    m = r.merge(ren[["oreg", "oyear", "title", "id", "rdat"]].rename(columns={"title": "ren_title", "id": "ren_id"}),
                left_on="regnum", right_on="oreg", how="left")
    m["year_ok"] = (m.oyear - m.reg_year).abs() <= 1
    m["title_sim"] = [fuzz.token_set_ratio(norm(a), norm(b)) if isinstance(b, str) else 0 for a, b in zip(m.title, m.ren_title)]
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
