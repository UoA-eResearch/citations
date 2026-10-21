"""Plan section 4: both limbs broken down by the country's CBD Party and Nagoya Party status (at the 1 June 2023
cutoff) and World Bank income group. Descriptive only.

Sources (data/raw/groups/): the CBD's country API (treaty XXVII-8 is the Convention, XXVII-8-b the Nagoya Protocol;
party dates), and the World Bank country API (current income level). INSDC names are mapped to ISO codes through
GeoNames countryInfo. Oceans and seas fall in the group "not a country"; dependent territories and others absent from
the CBD's state list (Taiwan, Hong Kong, Puerto Rico, Greenland, Antarctica...) in "territory or other", since
whether a sovereign's ratification extends to them varies.

  decomposition.py limb1   usable samples before and after the cutoff (donut excluded), shares by group
  decomposition.py limb2   gold countries by group, and each arm's correct recoveries by group
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
TAB = RUN / "results" / "tables"
CUT = "2023-06-01"


def groups():
    iso = {}
    for l in open(RAW / "geonames" / "countryInfo.txt", encoding="utf-8"):
        if l.startswith("#"):
            continue
        f = l.split("\t")
        c = countries.resolve(f[4]) if len(f) > 4 else None
        if c:
            iso.setdefault(c, f[0])
    cbd = {c["code"]: c["treaties"] for c in json.load(open(RAW / "groups" / "cbd_countries.json"))}
    wb = {c["iso2Code"]: c["incomeLevel"]["value"] for c in json.load(open(RAW / "groups" / "wb_countries.json"))[1]
          if c["region"]["value"] != "Aggregates"}

    def party(t, k):
        p = (t or {}).get(k, {}).get("party")
        return bool(p) and p <= CUT

    out = {}
    for c in countries.VOCAB:
        i = iso.get(c)
        if not i:
            out[c] = {"iso2": None, "cbd": "not a country", "nagoya": "not a country", "income": "not a country"}
            continue
        t = cbd.get(i)
        if t is None:       # dependent territories and others outside the CBD's state list; treaty coverage varies
            cb = ng = "territory or other"
        else:
            cb, ng = ("Party" if party(t, "XXVII8") else "not a Party"), ("Party" if party(t, "XXVII8b") else "not a Party")
        out[c] = {"iso2": i, "cbd": cb, "nagoya": ng, "income": wb.get(i, "not classified") or "not classified"}
    return out


def share_table(series, G):
    n = len(series)
    res = {}
    for dim in ("cbd", "nagoya", "income"):
        c = Counter(G.get(x, {}).get(dim, "unmapped") for x in series)
        res[dim] = {k: {"n": v, "share": round(v / n, 4)} for k, v in sorted(c.items())}
    return res


def limb1():
    G = groups()
    cols = ["submission_date", "country_class", "country_resolved", "organism", "host"]
    parts = []
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        d = pd.read_parquet(f, columns=cols)
        d = d[(d.country_class == "usable") & (d.submission_date >= "2021-06-01") & (d.submission_date < "2025-06-01")]
        d = d[~(d.organism.str.contains("metagenome", case=False, na=False)
                & d.host.str.contains(r"homo sapiens|\bhuman\b", case=False, na=False))]
        parts.append(d[["submission_date", "country_resolved"]])
    d = pd.concat(parts, ignore_index=True)
    pre = d[d.submission_date < "2023-05-01"].country_resolved
    post = d[d.submission_date >= "2023-07-01"].country_resolved
    out = {"groups_as_of": CUT, "pre": {"n": len(pre), **share_table(pre, G)},
           "post": {"n": len(post), **share_table(post, G)},
           "unmapped_names": sorted({x for x in d.country_resolved.unique() if x not in G})[:20]}
    json.dump(out, open(TAB / "decomposition_limb1.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("pre", "post")}, indent=1)[:4000])


def limb2():
    G = groups()
    rows = pd.read_csv(TAB / "limb2_rows.csv", keep_default_na=False)
    prim = json.load(open(TAB / "limb2_primary.json"))
    det = rows[rows.gold != "not determinable"]
    out = {"gold_countries": share_table(det.gold.tolist(), G), "arms": {}}
    for arm in ("gazetteer", "classifier", "llm"):
        t = prim["arms"][arm]["tuning"]["threshold"]
        if t is None:
            out["arms"][arm] = None
            continue
        conf = pd.to_numeric(det[f"{arm}_conf"], errors="coerce").fillna(0)
        hit = det[(det[arm] == det.gold) & (conf >= t)]
        res = {}
        for dim in ("cbd", "nagoya", "income"):
            tot = Counter(G.get(x, {}).get(dim, "unmapped") for x in det.gold)
            ok = Counter(G.get(x, {}).get(dim, "unmapped") for x in hit.gold)
            res[dim] = {k: {"determinable": v, "recovered": ok.get(k, 0)} for k, v in sorted(tot.items())}
        out["arms"][arm] = res
    json.dump(out, open(TAB / "decomposition_limb2.json", "w"), indent=1)
    print(json.dumps(out, indent=1)[:4000])


if __name__ == "__main__":
    {"limb1": limb1, "limb2": limb2}[sys.argv[1]]()
