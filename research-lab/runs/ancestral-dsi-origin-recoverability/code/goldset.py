"""Draw the 500-record gold set and assemble its evidence (plan section 3).

Sampling: untagged (placeholder, malformed or absent) non-human samples submitted 2023-06-01 to 2025-05-31; half
from samples whose BioProject links a publication, half from the rest, proportional by package within each half;
seed 20261022. A random 200 are the tuning split and 300 the test split.

Evidence per record (the same text the recovery arms read): organism, package, sample title, isolation source,
lat_lon, other attributes, description comment, BioProject title and description, and for a linked publication its
title, abstract and the full-text sentences that mention sampling or collection (Europe PMC, open access only).
Submitter institutions and author affiliations are never part of the evidence; the BioSample owner and the
BioProject submitter are kept apart, in owners.csv, for the asymmetric-error analysis only.

Writes data/gold/records.jsonl, data/gold/owners.csv, and two adjudication sheets, data/gold/pass1.md and pass2.md,
each in its own shuffled order with its own neutral ids; the keys (pass1_key.csv, pass2_key.csv) are kept apart.
"""
import glob
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
GOLD = RUN / "data" / "gold"
SEED, N, N_TUNE = 20261022, 500, 200
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
SITE = re.compile(r"\b(sampl\w*|collect\w*|isolat\w*|site|located|location|region|province|district|county|"
                  r"village|lake|river|forest|farm|hospital|coast|island|sea|ocean|latitude|longitude|°\s*[NSEW])\b", re.I)


def read_parts(cols):
    """Read the sample parts; evidence columns exist only in parts holding samples from the evidence window."""
    import pyarrow.parquet as pq
    out = []
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        have = [c for c in cols if c in pq.read_schema(f).names]
        x = pd.read_parquet(f, columns=have)
        for c in cols:
            if c not in x:
                x[c] = None
        out.append(x[cols])
    return pd.concat(out, ignore_index=True)


def get_json(url):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(3 * (t + 1))
    return None


def get_text(url):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(3 * (t + 1))
    return None


def publication(pmid):
    q = urllib.parse.quote(f"EXT_ID:{pmid} AND SRC:MED")
    j = get_json(f"{EPMC}/search?query={q}&resultType=core&format=json")
    if not j or not j.get("resultList", {}).get("result"):
        return None
    r = j["resultList"]["result"][0]
    out = {"pmid": pmid, "title": r.get("title", ""), "abstract": re.sub(r"<[^>]+>", " ", r.get("abstractText", ""))[:2500],
           "methods_sentences": ""}
    pmcid = r.get("pmcid")
    if pmcid and r.get("isOpenAccess") == "Y":
        x = get_text(f"{EPMC}/{pmcid}/fullTextXML")
        if x:
            body = re.sub(r"<ref-list.*?</ref-list>|<aff.*?</aff>|<contrib-group.*?</contrib-group>", " ", x, flags=re.S)
            t = " ".join(re.sub(r"<[^>]+>", " ", body).split())
            sents = [s for s in re.split(r"(?<=[.;])\s+", t) if SITE.search(s) and 30 < len(s) < 400]
            out["methods_sentences"] = " | ".join(sents[:12])[:2500]
    time.sleep(0.4)
    return out


def main():
    GOLD.mkdir(parents=True, exist_ok=True)
    cols = ["accession", "submission_date", "country_class", "country_raw", "organism", "package", "owner", "host",
            "bioprojects", "title", "isolation_source", "lat_lon", "attributes_text", "comment"]
    d = read_parts(cols)
    d = d[(d.submission_date >= "2023-06-01") & (d.submission_date <= "2025-05-31") & (d.country_class != "usable")]
    bp = pd.read_parquet(RUN / "data" / "bioprojects.parquet").set_index("accession")
    d["bp1"] = d.bioprojects.fillna("").str.split(";").str[0]
    d["has_pub"] = d.bp1.map(lambda a: bool(a) and a in bp.index and bool(bp.at[a, "pubmed_ids"]))
    rng = random.Random(SEED)
    picks = []
    for flag in (True, False):
        pool = d[d.has_pub == flag]
        alloc = (pool.package.value_counts(normalize=True) * (N // 2)).round().astype(int)
        while alloc.sum() > N // 2:
            alloc[alloc.idxmax()] -= 1
        while alloc.sum() < N // 2:
            alloc[alloc.idxmax()] += 1
        for pkg, k in alloc.items():
            if k > 0:
                sub = pool[pool.package == pkg]
                picks += [r for _, r in sub.sample(n=min(k, len(sub)), random_state=rng.randrange(2**31)).iterrows()]
    g = pd.DataFrame(picks).reset_index(drop=True)
    split = ["tune"] * N_TUNE + ["test"] * (len(g) - N_TUNE)
    rng.shuffle(split)
    g["split"] = split
    recs, owners = [], []
    for i, r in g.iterrows():
        a = r.bp1
        proj = bp.loc[a] if a and a in bp.index else None
        pubs = []
        if proj is not None and proj.pubmed_ids:
            for pmid in proj.pubmed_ids.split(";")[:2]:
                p = publication(pmid)
                if p:
                    pubs.append(p)
        recs.append({"record": f"R{i:03d}", "accession": r.accession, "split": r.split, "has_pub": bool(r.has_pub),
                     "country_raw": r.country_raw, "country_class": r.country_class, "organism": r.organism,
                     "package": r.package, "sample_title": r.title, "isolation_source": r.isolation_source,
                     "lat_lon": r.lat_lon, "attributes": r.attributes_text, "comment": r.comment,
                     "bioproject": a, "bioproject_title": proj.title if proj is not None else "",
                     "bioproject_description": proj.description if proj is not None else "", "publications": pubs})
        owners.append({"record": f"R{i:03d}", "biosample_owner": r.owner,
                       "bioproject_submitter": proj.submitter_org if proj is not None else ""})
        if i % 50 == 0:
            print(i, "records assembled", flush=True)
    with open(GOLD / "records.jsonl", "w") as fh:
        for x in recs:
            fh.write(json.dumps(x) + "\n")
    pd.DataFrame(owners).to_csv(GOLD / "owners.csv", index=False)
    for k, seed in ((1, SEED + 1), (2, SEED + 2)):
        order = list(range(len(recs)))
        random.Random(seed).shuffle(order)
        pd.DataFrame({"sheet_id": [f"P{k}-{j:03d}" for j in range(len(order))],
                      "record": [recs[i]["record"] for i in order]}).to_csv(GOLD / f"pass{k}_key.csv", index=False)
        with open(GOLD / f"pass{k}.md", "w") as fh:     # neutral ids only; the key is kept apart
            for j, idx in enumerate(order):
                x = recs[idx]
                fh.write(f"## P{k}-{j:03d}\n")
                for f in ("organism", "package", "sample_title", "isolation_source", "lat_lon", "attributes", "comment",
                          "country_raw", "bioproject_title", "bioproject_description"):
                    if x.get(f):
                        fh.write(f"- {f}: {x[f]}\n")
                for p in x["publications"]:
                    fh.write(f"- publication {p['pmid']}: {p['title']}\n  abstract: {p['abstract']}\n")
                    if p["methods_sentences"]:
                        fh.write(f"  sampling sentences: {p['methods_sentences']}\n")
                fh.write("\n")
    print(len(recs), "records;", sum(r["has_pub"] for r in recs), "with a linked publication;",
          sum(bool(r["publications"]) for r in recs), "with publication text retrieved")


if __name__ == "__main__":
    main()
