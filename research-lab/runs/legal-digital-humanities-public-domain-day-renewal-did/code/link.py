"""Link registrations to Open Library works, then collect those works' editions (plan section 1).

  link.py works      candidate works by blocking (first two significant title tokens) + title token_set_ratio >= 90
                     -> data/candidates.parquet
  link.py authors    author names for the candidates' author keys -> data/author_names.parquet
  link.py resolve    author surname present, first publish year <= reg year + 1 (or missing), unique best match
                     -> data/links.parquet
  link.py editions   editions of linked works: publish year, publishers, record created -> data/editions.parquet
"""
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

RUN = Path(__file__).resolve().parents[1]
DATA, RAW = RUN / "data", RUN / "data" / "raw"
WORD = re.compile(r"[a-z0-9]+")
ARTICLES = {"the", "a", "an"}
YEAR = re.compile(r"(1[5-9]\d\d|20[0-2]\d)")
WORKKEY = re.compile(r'"(/works/OL\d+W)"')


def norm(s):
    return " ".join(WORD.findall((s or "").lower()))


def key(title):
    toks = [t for t in norm(title).split() if t not in ARTICLES]
    return " ".join(toks[:2]) if toks else ""


def surname(author):
    """CCE names are 'Surname, Given' (surname = last token before the comma) or 'Given Surname' (last token)."""
    a = (author or "").strip()
    t = norm(a.split(",")[0] if "," in a else a).split()
    return t[-1] if t else ""


def works():
    r = pd.read_parquet(DATA / "registrations.parquet")
    r["k"] = r.title.map(key)
    r["tn"] = r.title.map(norm)
    idx = defaultdict(list)
    for i, (k, tn) in enumerate(zip(r.k, r.tn)):
        if k:
            idx[k].append(i)
    rows, n = [], 0
    with gzip.open(RAW / "ol_dump_works_latest.txt.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            n += 1
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5 or parts[0] != "/type/work":
                continue
            j = json.loads(parts[4])
            t = j.get("title", "")
            k = key(t)
            if k not in idx:
                continue
            tn = norm(t + " " + (j.get("subtitle") or ""))
            for i in idx[k]:
                s = fuzz.token_set_ratio(r.tn.iat[i], tn)
                if s >= 90:
                    fp = j.get("first_publish_date") or ""
                    m = YEAR.search(fp)
                    rows.append({"entry_id": r.entry_id.iat[i], "work": parts[1], "title_sim": s,
                                 "work_title": t[:200], "first_year": int(m.group(1)) if m else None,
                                 "author_keys": ";".join(a.get("author", {}).get("key", "") for a in j.get("authors", [])
                                                         if isinstance(a, dict) and isinstance(a.get("author"), dict))})
            if n % 5_000_000 == 0:
                print(n, "works lines;", len(rows), "candidates", flush=True)
    pd.DataFrame(rows).to_parquet(DATA / "candidates.parquet", index=False)
    print("works lines", n, "candidates", len(rows), flush=True)


def authors():
    c = pd.read_parquet(DATA / "candidates.parquet")
    want = {k for ks in c.author_keys.dropna() for k in ks.split(";") if k}
    rows = []
    with gzip.open(RAW / "ol_dump_authors_latest.txt.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5 and parts[1] in want:
                j = json.loads(parts[4])
                rows.append({"author_key": parts[1], "name": j.get("name", ""), "personal_name": j.get("personal_name", "")})
    pd.DataFrame(rows).to_parquet(DATA / "author_names.parquet", index=False)
    print("authors wanted", len(want), "found", len(rows), flush=True)


def resolve():
    r = pd.read_parquet(DATA / "registrations.parquet").set_index("entry_id")
    c = pd.read_parquet(DATA / "candidates.parquet")
    an = pd.read_parquet(DATA / "author_names.parquet").set_index("author_key")
    names = {k: norm(f"{a} {b}") for k, a, b in zip(an.index, an.name, an.personal_name)}
    c["surname"] = c.entry_id.map(r.author.map(surname))
    c["reg_year"] = c.entry_id.map(r.reg_year)
    c["author_ok"] = [bool(sn) and any(sn in names.get(k, "").split() for k in (ks or "").split(";"))
                      for sn, ks in zip(c.surname, c.author_keys)]
    c["date_ok"] = c.first_year.isna() | (c.first_year <= c.reg_year + 1)
    ok = c[c.author_ok & c.date_ok].copy()
    best = ok.groupby("entry_id").title_sim.transform("max")
    ok = ok[ok.title_sim == best]
    nwork = ok.groupby("entry_id").work.transform("nunique")
    links = ok[nwork == 1].drop_duplicates("entry_id")
    # a work claimed by two registrations is ambiguous too
    links = links[links.groupby("work").entry_id.transform("nunique") == 1]
    links[["entry_id", "work", "title_sim", "work_title", "first_year"]].to_parquet(DATA / "links.parquet", index=False)
    rr = r.loc[links.entry_id]
    summ = {"candidates": int(len(c)), "author_ok": int(c.author_ok.sum()), "linked_registrations": int(len(links)),
            "linked_by_renewal": rr.renewed.value_counts().to_dict(), "dropped_ambiguous": int((nwork > 1).groupby(ok.entry_id).any().sum())}
    # D2: among registrations with at least one candidate passing the surname and date rules, the share dropped as
    # equal-best ambiguous and the share linked, by renewal status
    has_ok = pd.DataFrame({"entry_id": ok.entry_id.unique()})
    has_ok["renewed"] = has_ok.entry_id.map(r.renewed)
    amb = set(ok.entry_id[nwork > 1])
    has_ok["ambiguous"] = has_ok.entry_id.isin(amb)
    has_ok["linked"] = has_ok.entry_id.isin(set(links.entry_id))
    summ["among_registrations_with_a_passing_candidate"] = {
        ("renewed" if k else "never_renewed"): {"n": int(len(g)), "dropped_ambiguous": round(float(g.ambiguous.mean()), 3),
                                                  "linked": round(float(g.linked.mean()), 3)} for k, g in has_ok.groupby("renewed")}
    json.dump(summ, open(RUN / "results" / "tables" / "linkage_summary.json", "w"), indent=1, default=str)
    print(summ, flush=True)


def editions():
    links = pd.read_parquet(DATA / "links.parquet")
    want = set(links.work)
    rows, n = [], 0
    with gzip.open(RAW / "ol_dump_editions_latest.txt.gz", "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            n += 1
            # parse JSON only for lines that name a linked work (a regex pre-filter; the JSON check below decides)
            if not any(m.group(1) in want for m in WORKKEY.finditer(line)):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            j = json.loads(parts[4])
            ws = [w.get("key") for w in j.get("works", []) if isinstance(w, dict)]
            hit = [w for w in ws if w in want]
            if not hit:
                continue
            m = YEAR.search(j.get("publish_date") or "")
            created = (j.get("created") or {}).get("value", "") if isinstance(j.get("created"), dict) else ""
            rows.append({"work": hit[0], "edition": parts[1], "pub_year": int(m.group(1)) if m else None,
                         "publishers": "; ".join(j.get("publishers", []))[:200], "created": created[:10],
                         "isbn": bool(j.get("isbn_10") or j.get("isbn_13"))})

    pd.DataFrame(rows).to_parquet(DATA / "editions.parquet", index=False)
    print("edition lines", n, "kept", len(rows), flush=True)


if __name__ == "__main__":
    {"works": works, "authors": authors, "resolve": resolve, "editions": editions}[sys.argv[1]]()
