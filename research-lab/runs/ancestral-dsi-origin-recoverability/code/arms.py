"""The three recovery arms of plan section 3, run on the gold records. Writes data/gold/arms.jsonl.

Every arm reads the same evidence text (goldset.py): sample fields, BioProject title and description, and the linked
publication's title, abstract and sampling sentences. Submitter institutions and author affiliations are never read.
Each arm emits a country in the INSDC vocabulary, or none, and a confidence in [0, 1].

  gazetteer   GeoNames place names (population >= 15,000) and country names found in the evidence, weighted by
              source; lat_lon, where present, is reverse-geocoded to the nearest such place within 100 km
  classifier  TF-IDF (1-2 grams) + logistic regression (SGD) trained on tagged samples of the same period
  llm         the locally served open-weight model, asked for the collection country or "unknown"
"""
import glob
import json
import math
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GOLD = RUN / "data" / "gold"
GEO = RUN / "data" / "raw" / "geonames"
SEED = 20261022
EXTRA = {"dr congo": "Democratic Republic of the Congo", "republic of the congo": "Republic of the Congo",
         "palestinian territory": "State of Palestine", "macao": "Macau", "u.s. virgin islands": "Virgin Islands",
         "east timor": "Timor-Leste", "bonaire, saint eustatius and saba": "Bonaire, Sint Eustatius and Saba"}
CITY_STOP = {"Mobile", "Reading", "Split", "Nice", "Bath", "Wells", "Male", "Media", "Marine", "Victoria", "Union",
             "Independence", "Liberty", "Florida", "Columbia", "Georgia", "Jordan", "Chad", "Guinea", "Normal", "Central",
             "Center", "Sale", "Bay", "Laval", "Gap", "Batch", "Control", "March", "May", "Hamilton", "Washington",
             "Lincoln", "Jackson", "Franklin", "Clinton", "Springfield", "Salem", "Albany", "Madison", "Aurora"}
W = {"lat_lon": 5.0, "sampling": 3.0, "abstract": 2.0, "bioproject": 2.0, "sample": 2.0}


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


def insdc(name):
    if not name:
        return None
    n = name.strip()
    return countries.resolve(n) or countries.resolve(EXTRA.get(n.lower(), "")) or None


def evidence(x, parts=False):
    s = {"sample": " ; ".join(str(x.get(f) or "") for f in ("sample_title", "isolation_source", "attributes", "comment")),
         "bioproject": f"{x.get('bioproject_title') or ''} ; {x.get('bioproject_description') or ''}",
         "abstract": " ; ".join(f"{p['title']} {p['abstract']}" for p in x.get("publications", [])),
         "sampling": " ; ".join(p.get("methods_sentences", "") for p in x.get("publications", []))}
    return s if parts else " ; ".join(v for v in s.values() if v.strip())


# ---------------- gazetteer
def load_gazetteer():
    ci = [l.split("\t") for l in open(GEO / "countryInfo.txt", encoding="utf-8") if not l.startswith("#")]
    iso = {r[0]: insdc(r[4]) for r in ci if len(r) > 4}
    names = {}
    for r in ci:
        if len(r) > 4 and iso.get(r[0]):
            names[r[4]] = (iso[r[0]], 1e12)
    for v in countries.VOCAB:
        names.setdefault(v, (v, 1e12))
    lat, lon, cc = [], [], []
    for l in open(GEO / "cities15000.txt", encoding="utf-8"):
        f = l.rstrip("\n").split("\t")
        c = iso.get(f[8])
        if not c:
            continue
        pop = float(f[14] or 0)
        lat.append(float(f[4])); lon.append(float(f[5])); cc.append(c)
        for nm in {f[1], f[2]}:
            if len(nm) >= 4 and nm not in CITY_STOP and (nm not in names or names[nm][1] < pop):
                names[nm] = (c, pop)
    pat = re.compile(r"\b(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")\b")
    return names, pat, np.radians(np.array(lat)), np.radians(np.array(lon)), np.array(cc)


LATLON = re.compile(r"(-?\d+(?:\.\d+)?)\s*([NS])?[\s,]+(-?\d+(?:\.\d+)?)\s*([EW])?", re.I)


def reverse(latlon, g):
    m = LATLON.search(latlon or "")
    if not m:
        return None
    la, lo = float(m.group(1)), float(m.group(3))
    if m.group(2) and m.group(2).upper() == "S":
        la = -abs(la)
    if m.group(4) and m.group(4).upper() == "W":
        lo = -abs(lo)
    if abs(la) > 90 or abs(lo) > 180:
        return None
    _, _, rl, rn, cc = g
    a, b = math.radians(la), math.radians(lo)
    d = 2 * np.arcsin(np.sqrt(np.sin((rl - a) / 2) ** 2 + np.cos(a) * np.cos(rl) * np.sin((rn - b) / 2) ** 2)) * 6371
    i = int(np.argmin(d))
    return cc[i] if d[i] <= 100 else None


def gazetteer(x, g):
    names, pat = g[0], g[1]
    score = defaultdict(float)
    r = reverse(x.get("lat_lon"), g)
    if r:
        score[r] += W["lat_lon"]
    for src, txt in evidence(x, parts=True).items():
        for m in pat.finditer(txt or ""):
            score[names[m.group(1)][0]] += W[src]
    if not score:
        return None, 0.0
    c, s = max(score.items(), key=lambda kv: kv[1])
    return c, s / sum(score.values())


# ---------------- classifier
def classifier_predictions(recs):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    cols = ["submission_date", "country_class", "country_resolved", "bioprojects", "title", "isolation_source",
            "attributes_text", "comment"]
    d = read_parts(cols)
    d = d[(d.submission_date >= "2023-06-01") & (d.submission_date <= "2025-05-31") & (d.country_class == "usable")]
    d = d.sample(n=min(200_000, len(d)), random_state=SEED)
    bp = pd.read_parquet(RUN / "data" / "bioprojects.parquet").set_index("accession")
    b1 = d.bioprojects.fillna("").str.split(";").str[0]
    bpt = b1.map(lambda a: f"{bp.at[a, 'title']} ; {bp.at[a, 'description']}" if a in bp.index else "")
    text = (d.title.fillna("") + " ; " + d.isolation_source.fillna("") + " ; " + d.attributes_text.fillna("") + " ; "
            + d.comment.fillna("") + " ; " + bpt)
    keep = d.country_resolved.map(d.country_resolved.value_counts()) >= 100
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=300_000, sublinear_tf=True)
    X = vec.fit_transform(text[keep])
    clf = SGDClassifier(loss="log_loss", alpha=1e-6, max_iter=20, random_state=SEED, n_jobs=8)
    clf.fit(X, d.country_resolved[keep])
    P = clf.predict_proba(vec.transform([evidence(x) for x in recs]))
    top = P.argmax(axis=1)
    return [(clf.classes_[t], float(P[i, t])) for i, t in enumerate(top)], {"train_rows": int(keep.sum()),
                                                                           "classes": int(len(clf.classes_))}


# ---------------- llm
PROMPT = """You are given metadata about one biological sample from a sequence archive. Name the country (or ocean
or sea) where the sample was physically collected. Use only what the evidence states or clearly implies about the
collection site; do not infer it from where the researchers work. If the evidence does not say, answer "unknown".
Reply with JSON only: {"country": "<name or unknown>", "probability": <your probability that the answer is right,
0 to 1>}

Evidence:
"""


def llm(x, model):
    body = {"model": model, "temperature": 0, "max_tokens": 16384,   # D6: the model reasons before answering
            "messages": [{"role": "user", "content": PROMPT + evidence(x)[:6000]}]}
    req = urllib.request.Request("http://localhost:8000/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            out = json.loads(r.read())["choices"][0]["message"]["content"] or ""
    except Exception as e:
        return None, 0.0, f"error: {e!r}"
    m = re.findall(r"\{[^{}]*\"country\"[^{}]*\}", out)
    if not m:
        return None, 0.0, out[-200:]
    try:
        j = json.loads(m[-1])
    except Exception:
        return None, 0.0, out[-200:]
    c = str(j.get("country", "")).strip()
    if not c or c.lower() == "unknown":
        return None, 0.0, ""
    try:
        p = float(j.get("probability", 0))
    except Exception:
        p = 0.0
    return insdc(c.split(":")[0]), max(0.0, min(1.0, p)), ""


def main():
    recs = [json.loads(l) for l in open(GOLD / "records.jsonl")]
    g = load_gazetteer()
    gz = [gazetteer(x, g) for x in recs]
    cl, info = classifier_predictions(recs)
    model = json.loads(urllib.request.urlopen("http://localhost:8000/v1/models", timeout=30).read())["data"][0]["id"]
    from concurrent.futures import ThreadPoolExecutor   # D6: 8 requests at a time; temperature 0 throughout
    with ThreadPoolExecutor(8) as ex:
        lm = list(ex.map(lambda x: llm(x, model), recs))
    out = []
    for x, a, b, (c, p, note) in zip(recs, gz, cl, lm):
        out.append({"record": x["record"], "gazetteer": a[0], "gazetteer_conf": round(a[1], 4),
                    "classifier": b[0], "classifier_conf": round(b[1], 4), "llm": c, "llm_conf": round(p, 4),
                    "llm_note": note})
    with open(GOLD / "arms.jsonl", "w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    json.dump({"classifier": info, "llm_model": model}, open(RUN / "results" / "tables" / "arms_info.json", "w"), indent=1)
    print(len(out), "records scored by three arms", info, model)


if __name__ == "__main__":
    main()
