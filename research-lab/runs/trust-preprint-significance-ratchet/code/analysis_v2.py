"""Exploratory v2 analysis (deviations D3.2). Reads data/aligned_v2/ (pipeline_v2.py) and, if present, the v2 blind
validation (results/tables/alignment_validation_v2.csv). Never the preregistered test; reported as exploratory.

  strict crossing  an aligned crossing with (a) both sides in the abstract or results text (no tables, no legends);
                   (b) an exact tuple match or masked sentence cosine >= 0.80; (c) the same number of statistics in
                   both sentences and the same rank; (d) no significance-star definitions in either sentence.
  estimate         share crossing up among strict crossings in the v1 population, paper bootstrap (2,000); when
                   n < 30 the exact Clopper-Pearson interval is also given and the wider interval is read.
  decision         v2 precision among strict crossings >= 0.90 -> the estimate is reported and read against the
                   plan's thresholds; otherwise only validated-correct crossings are reported, by direction.
"""
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import boot_share  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
AL, TAB = RUN / "data" / "aligned_v2", RUN / "results" / "tables"
TEXT = {"abstract", "result"}
STAR = re.compile(r"\*+\s*[:=]?\s*[pP]\s*(?:<=|≤|<|>|≥|>=)|[pP]\s*(?:<=|≤|<)\s*0?\.\d+\s*[:=]?\s*\(?\*")
CROSS = ("crossing_up", "crossing_down")


def strict(r):
    a, b = r["pre"], r["pub"]
    return (a["section"] in TEXT and b["section"] in TEXT
            and (r["how"] == "exact" or r["sim"] >= 0.80)
            and a["n_in_sent"] == b["n_in_sent"] and a["rank"] == b["rank"]
            and not STAR.search(a["sentence"]) and not STAR.search(b["sentence"]))


def clopper(k, n):
    if n == 0:
        return None, None
    lo = 0.0 if k == 0 else float(st.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(st.beta.ppf(0.975, k + 1, n - k))
    return lo, hi


def estimate(rows):
    df = pd.DataFrame(dict(pair=[r["pair"] for r in rows], up=[r["cls"] == "crossing_up" for r in rows]))
    est, lo, hi = boot_share(df)
    out = dict(n=int(len(df)), n_papers=int(df.pair.nunique()) if len(df) else 0, n_up=int(df.up.sum()) if len(df) else 0,
               share_up=est, boot_ci=[lo, hi])
    if 0 < len(df) < 30:
        clo, chi = clopper(int(df.up.sum()), len(df))
        out["exact_ci"] = [clo, chi]
        lo, hi = min(lo, clo), max(hi, chi)
    out["ci_read"] = [lo, hi]
    if est is None:
        out["reading"] = "not estimable"
    elif est >= 0.67 and lo > 0.50:
        out["reading"] = "ratchet-like"
    elif hi < 0.67:
        out["reading"] = "against a 2:1 ratchet"
    else:
        out["reading"] = "inconclusive"
    return out


def direction_of(stat_str):
    """'p < 0.05' / 't = 0.003' as written by the validation display -> significance at 0.05."""
    from extract import significance
    _, c, p = stat_str.split(" ", 2)
    return significance(c, float(p))


def validated_directions():
    """Direction of every crossing a blind validation judged correct (v1 and v2 samples)."""
    out = []
    for tag, sample, key, val in (("v1", "sample.jsonl", "key.csv", "alignment_validation.csv"),
                                  ("v2", "sample_v2.jsonl", "key_v2.csv", "alignment_validation_v2.csv")):
        V = RUN / "data" / "validation"
        if not (TAB / val).exists():
            continue
        s = {json.loads(l)["id"]: json.loads(l) for l in open(V / sample)}
        v = pd.read_csv(TAB / val)
        for _, r in v[(v.stratum == "crossing") & (v.correct == 1)].iterrows():
            x = s[r.id]
            pre, pub = (x["stat_1"], x["stat_2"]) if int(r.pre_is) == 1 else (x["stat_2"], x["stat_1"])
            a, b = direction_of(pre), direction_of(pub)
            out.append(dict(sample=tag, id=r.id, pair=r.pair, up=(a is False and b is True), down=(a is True and b is False)))
    return pd.DataFrame(out)


def main():
    rows = [json.loads(l) for l in gzip.open(AL / "statistics.jsonl.gz", "rt")]
    pairs = pd.DataFrame([json.loads(l) for l in open(AL / "pairs.jsonl")])
    v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
    al = [r for r in rows if r["status"] == "aligned"]
    st_all = [r for r in al if strict(r)]
    out = dict(n_statistics=len(rows), n_aligned=len(al), n_strict_eligible=len(st_all),
               class_counts_all=pd.Series([r["cls"] for r in al]).value_counts().to_dict(),
               class_counts_strict=pd.Series([r["cls"] for r in st_all]).value_counts().to_dict())
    det = [r for r in st_all if r["pair"] in v1 and r["cls"] != "undetermined"]
    sc_v1 = [r for r in st_all if r["pair"] in v1 and r["cls"] in CROSS]
    out["strict_v1"] = estimate(sc_v1)
    out["strict_v1"]["per_1000_determined"] = 1000 * len(sc_v1) / max(1, len(det))
    out["strict_all_versions"] = estimate([r for r in st_all if r["cls"] in CROSS])
    out["strict_v1_exact_tuples"] = estimate([r for r in sc_v1 if r["how"] == "exact"])
    out["all_crossings_v1_unreliable"] = estimate([r for r in al if r["pair"] in v1 and r["cls"] in CROSS])
    val = TAB / "alignment_validation_v2.csv"
    if val.exists():
        v = pd.read_csv(val)
        prec = float(v[v.stratum == "crossing"].correct.mean())
        out["validation_v2"] = dict(precision_crossings=prec, n_crossings=int((v.stratum == "crossing").sum()),
                                    precision_other=float(v[v.stratum != "crossing"].correct.mean()))
        out["decision"] = "estimate reported" if prec >= 0.90 else "only validated-correct crossings reported"
    vd = validated_directions()
    if len(vd):
        out["validated_correct_crossings"] = {t: dict(n=int(len(g)), up=int(g.up.sum()), down=int(g.down.sum()),
                                                      exact_ci_up=list(clopper(int(g.up.sum()), int(g.up.sum() + g.down.sum()))))
                                              for t, g in vd.groupby("sample")}
    rv1 = [r for r in rows if r["pair"] in v1]
    dropped = [r["pre"]["sig"] for r in rv1 if r["status"] == "dropped" and r["pre"]["sig"] is not None]
    added = [r["pub"]["sig"] for r in rv1 if r["status"] == "added" and r["pub"]["sig"] is not None]
    out["S1_v2"] = dict(n_dropped=len(dropped), share_sig_dropped=float(np.mean(dropped)) if dropped else None,
                        n_added=len(added), share_sig_added=float(np.mean(added)) if added else None)
    json.dump(out, open(TAB / "exploratory_v2.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
