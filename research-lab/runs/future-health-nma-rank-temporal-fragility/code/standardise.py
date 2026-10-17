"""Standardise every verified nmadb dataset into one schema (plan section 4).

Reads data/raw/catalog.csv and data/raw/datasets/<record>.xlsx. Writes:
  data/std/<record>.csv     long: study, label, year, t, r, n | y, sd, n | r, n, time   iv: study, label, year, t1, t2, TE, seTE
  data/std/<record>.trt.json treatment number -> name, from the sheet's "Treatments" side table (for validation V3)
  data/std_summary.csv      one row per record: format, type, measure, direction, counts, year coverage, parse issues
Inverse-variance ratio measures are analysed on the log scale. Which sheets give them on the natural scale is
adjudicated (D2, NATURAL below): an all-positive column is not evidence, because a network where every comparison
favours one side has all-positive log ratios. For natural-scale sheets the effect is logged and seTE is taken from the
95% CI on the log scale (CI columns, or a text CI column "a-b"), else by the delta method (se / effect)."""
import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
OUT = RUN / "data" / "std"
SM = {"odds ratio": "OR", "risk ratio": "RR", "hazard ratio": "HR", "rate ratio": "IRR", "risk difference": "RD",
      "mean difference": "MD", "standardized mean difference": "SMD"}
RATIO = {"OR", "RR", "HR", "IRR"}
YEAR_COLS = ["study year", "year", "studyyear", "pub. year", "publication year", "pub year"]
LABEL_COLS = ["study name", "study (name)", "study", "studyid", "study id", "author"]
# D1: with no year column, a year written in the study label ("Smolen, 2008", "Black et al. (2007)") is used
LABEL_YEAR = re.compile(r"(?:^|[\s,.(\[])((?:19[5-9]|20[0-2])\d)[a-z]?(?=[\s,)\].;]|$)")
# D2: contrast-level ratio sheets on the natural scale (checked against their CIs: asymmetric on the linear scale);
# every other iv ratio sheet is already on the log scale (501244 and 501378 have all-positive log ratios)
NATURAL = {"479688", "479757", "480486", "501200"}


def num(s):
    return pd.to_numeric(s, errors="coerce")


def year_of(v):
    if pd.isna(v):
        return np.nan
    m = re.search(r"(19[5-9]\d|20[0-2]\d)", str(v))
    return float(m.group(1)) if m else np.nan


def treatments(raw):
    """Find the 'Treatments' side table: marker cell, numbers in the next column, names in the one after."""
    g = raw.copy()
    g.columns = range(g.shape[1])
    hdr = [str(c).strip().lower() for c in raw.columns]
    out = {}
    hits = [(None, j) for j, h in enumerate(hdr) if h == "treatments"]
    for j in range(g.shape[1]):
        for i, v in g[j].items():
            if isinstance(v, str) and v.strip().lower() == "treatments":
                hits.append((i, j))
    for i, j in hits:
        if j + 2 >= g.shape[1]:
            continue
        start = 0 if i is None else i
        for k in range(start, len(g)):
            a, b = num(pd.Series([g.iat[k, j + 1]])).iat[0], g.iat[k, j + 2]
            if pd.isna(a):
                if k > start:
                    break
                continue
            out[int(a)] = str(b).strip()
        if out:
            break
    return out


def parse(rid, meta):
    raw = pd.read_excel(RAW / "datasets" / f"{rid}.xlsx")
    lc = {str(c).strip().lower(): c for c in raw.columns}
    issues = []
    fmt, typ, sm = meta["Format"], meta["Type of Outcome\xa0"].lower(), SM.get(meta["Effect Measure"], "other")
    ycol = next((lc[c] for c in YEAR_COLS if c in lc), None)
    lcol = next((lc[c] for c in LABEL_COLS if c in lc), None)
    if "id" not in lc:
        raise ValueError("no id column")
    d = pd.DataFrame({"study": num(raw[lc["id"]])})
    d["label"] = raw[lcol] if lcol is not None else ""
    d["year"] = raw[ycol].map(year_of) if ycol is not None else np.nan
    if ycol is None:
        issues.append("no year column")
        if lcol is not None:
            ly = raw[lcol].map(lambda v: float(LABEL_YEAR.findall(str(v))[-1]) if isinstance(v, str) and LABEL_YEAR.findall(v) else np.nan)
            if ly.notna().any():
                d["year"] = ly
                issues.append("year from study label (D1)")
    if fmt in ("long", "wide"):
        d["t"] = num(raw[lc["t"]])
        need = {"binary": ["r", "n"], "continuous": ["y", "sd", "n"], "rate": ["r", "n", "time"]}.get(typ)
        if need is None:
            raise ValueError(f"long format with outcome type {typ}")
        for k in need:
            if k not in lc:
                raise ValueError(f"missing column {k}")
            d[k] = num(raw[lc[k]])
        d = d[d.study.notna() & d.t.notna()].copy()
        d = d.dropna(subset=need, how="all")
        if typ == "binary" and ((d.r > d.n) | (d.n <= 0)).any():
            issues.append("r > n or n <= 0 in some arm")
    else:
        d["t1"], d["t2"] = num(raw[lc["t1"]]), num(raw[lc["t2"]])
        d["TE"], d["seTE"] = num(raw[lc["effect"]]), num(raw[lc["se"]])
        cil = num(raw[lc["cil"]]) if "cil" in lc else None
        cih = num(raw[lc["cih"]]) if "cih" in lc else None
        keep = d.study.notna() & d.t1.notna() & d.t2.notna() & d.TE.notna()
        if sm in RATIO and rid in NATURAL:
            issues.append("iv ratio on natural scale: logged")
            te = d.TE.copy()
            d["TE"] = np.log(te)
            txt = next((raw[c] for c in raw.columns if re.search(r"95\s*%\s*ci", str(c), re.I)), None)
            if cil is not None and cih is not None and (cil[keep] > 0).all() and (cih[keep] > 0).all():
                d["seTE"] = (np.log(cih) - np.log(cil)) / (2 * 1.959964)
            elif txt is not None:
                b = txt.astype(str).str.extract(r"([\d.]+)\s*-\s*([\d.]+)").astype(float)
                d["seTE"] = (np.log(b[1]) - np.log(b[0])) / (2 * 1.959964)
                issues.append("seTE from text CI")
            else:
                d["seTE"] = d.seTE / te
                issues.append("seTE by delta method")
        d = d[keep].copy()
    # a study's year sits on its first row only: carry it within the study id
    d["year"] = d.groupby("study").year.transform(lambda s: s.ffill().bfill())
    d["label"] = d.groupby("study").label.transform(lambda s: s.ffill().bfill())
    return d, treatments(raw), issues


def main():
    cat = pd.read_csv(RAW / "catalog.csv", sep=";", dtype=str)
    cat = cat[cat.Verified.str.lower() == "true"].set_index("Record ID")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for rid, meta in cat.iterrows():
        r = dict(record=rid, format=meta["Format"], type=meta["Type of Outcome\xa0"], measure=SM.get(meta["Effect Measure"], "other"),
                 direction=meta["Harmful/Beneficial Outcome"], cat_studies=meta["Number of Studies  "], cat_trts=meta["Number of Treatments"])
        try:
            d, trt, issues = parse(rid, meta)
        except Exception as e:  # noqa: BLE001
            r.update(parsed=False, reason=f"{type(e).__name__}: {str(e)[:100]}")
            rows.append(r); continue
        d.to_csv(OUT / f"{rid}.csv", index=False)
        json.dump(trt, open(OUT / f"{rid}.trt.json", "w"))
        st = d.groupby("study").year.first()
        tr = set(d.t.dropna().astype(int)) if "t" in d else set(d.t1.astype(int)) | set(d.t2.astype(int))
        r.update(parsed=True, reason="", n_studies=int(st.size), n_trts=len(tr), n_rows=len(d),
                 year_share=float(st.notna().mean()), year_min=st.min(), year_max=st.max(),
                 multiarm=int((d.groupby("study").size() > (2 if "t" in d else 1)).sum()), n_trt_names=len(trt), issues="; ".join(issues))
        rows.append(r)
    s = pd.DataFrame(rows)
    s.to_csv(RUN / "data" / "std_summary.csv", index=False)
    print(len(s), "records;", int(s.parsed.sum()), "parsed")
    print(s[~s.parsed].reason.value_counts().to_string())
    print(s.issues.fillna("").str.split("; ").explode().value_counts().to_string())


if __name__ == "__main__":
    sys.exit(main())
