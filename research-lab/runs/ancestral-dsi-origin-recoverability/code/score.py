"""Limb 2 scoring (plan section 3). Written before pass 2, before any arm was run.

  score.py agree   Cohen's kappa between the two blind passes (reported before any arm is scored), and the pass-3
                   sheet of the records they disagree on, in a new shuffled order with neutral ids (P3-xxx).
  score.py score   Final labels; each arm's threshold on the tuning split; H2 on the test split; secondaries.

Labels are INSDC country or ocean names, "inapplicable" (lab lineage, cell line, model organism, experimental
cultivar or animal), "not stated" (a natural sample whose origin the evidence does not give), or "excluded".
Both "inapplicable" and "not stated" are "not determinable" for scoring (deviations D2).

Exclusions are decided by code, not by the labels: metagenomes from a human host (care filter, D3), and records
whose own country field now resolves under the corrected classifier (D4), since they are no longer untagged. The
labels' own "excluded" marks are cross-checked against the first rule.

Pass 3 is blind to the two earlier labels and follows the plan's fixed rule: a country only where the evidence gives
an explicit sampling-site statement; otherwise not determinable (inapplicable or not stated).
"""
import glob
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GOLD = RUN / "data" / "gold"
TAB = RUN / "results" / "tables"
SEED = 20261022
ND = "not determinable"
ARMS = ["gazetteer", "classifier", "llm"]
WINDOW = ("2023-06-01", "2025-05-31")


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0, round(po, 4)


def scoring(label):
    if label in ("inapplicable", "not stated"):
        return ND
    return None if label == "excluded" else label


def coarse(label):
    return label if label in ("inapplicable", "not stated", "excluded") else "country"


def records():
    return {x["record"]: x for x in (json.loads(l) for l in open(GOLD / "records.jsonl"))}


def exclusion(x):
    if "metagenome" in (x["organism"] or "").lower() and re.search(r"\bhost\s*=\s*(homo sapiens|human)\b",
                                                                     x["attributes"] or "", re.I):
        return "human-host metagenome (D3)"
    raw = x["country_raw"] if isinstance(x["country_raw"], str) else None
    if countries.classify(raw)[0] == "usable":
        return "own country field resolves after D4"
    return None


def canon(label):
    """D5: a country label is mapped to its INSDC spelling through the arms' own resolver, so that a straight or a
    curly apostrophe, or an accent, is not scored as a disagreement; a label outside the vocabulary is an error."""
    if label in ("inapplicable", "not stated", "excluded"):
        return label
    c = countries.resolve(label)
    assert c, f"label {label!r} is not an INSDC name"
    return c


def labels(k):
    key = pd.read_csv(GOLD / f"pass{k}_key.csv").set_index("sheet_id").record
    lab = pd.read_csv(GOLD / f"pass{k}_labels.csv", keep_default_na=False)
    assert lab.sheet_id.is_unique and set(lab.sheet_id) <= set(key.index), f"pass {k}: bad sheet ids"
    return dict(zip(lab.sheet_id.map(key), lab.label.str.strip().map(canon)))


def agree():
    R = records()
    l1, l2 = labels(1), labels(2)
    ids = sorted(R)
    assert set(l1) == set(ids) == set(l2), "both passes must label all 500 records"
    keep = [i for i in ids if not exclusion(R[i])]
    out = {"records": len(ids), "excluded_by_code": {i: exclusion(R[i]) for i in ids if exclusion(R[i])},
           "excluded_label_vs_code": {"pass1": sorted(i for i in ids if l1[i] == "excluded"),
                                      "pass2": sorted(i for i in ids if l2[i] == "excluded")},
           "scored_records": len(keep)}
    a, b = [l1[i] for i in keep], [l2[i] for i in keep]
    out["kappa_full"], out["raw_agreement_full"] = kappa(a, b)
    out["kappa_scoring"], out["raw_agreement_scoring"] = kappa([scoring(x) for x in a], [scoring(x) for x in b])
    out["kappa_coarse"], out["raw_agreement_coarse"] = kappa([coarse(x) for x in a], [coarse(x) for x in b])
    out["pass1_counts"] = Counter(coarse(x) for x in a)
    out["pass2_counts"] = Counter(coarse(x) for x in b)
    dis = [i for i in keep if l1[i] != l2[i]]
    out["disagreements"] = len(dis)
    out["disagreements_scoring"] = sum(scoring(l1[i]) != scoring(l2[i]) for i in dis)
    out["disagreement_kinds"] = Counter(f"{coarse(l1[i])} / {coarse(l2[i])}" for i in dis)
    json.dump(out, open(TAB / "gold_agreement.json", "w"), indent=1)
    order = dis[:]
    random.Random(SEED + 3).shuffle(order)
    pd.DataFrame({"sheet_id": [f"P3-{j:03d}" for j in range(len(order))], "record": order}) \
        .to_csv(GOLD / "pass3_key.csv", index=False)
    src = open(GOLD / "pass1.md").read()
    k1 = pd.read_csv(GOLD / "pass1_key.csv").set_index("record").sheet_id
    blocks = {m.group(1): m.group(2) for m in re.finditer(r"(?ms)^## (P1-\d{3})\n(.*?)(?=^## |\Z)", src)}
    with open(GOLD / "pass3.md", "w") as fh:
        for j, rec in enumerate(order):
            fh.write(f"## P3-{j:03d}\n{blocks[k1[rec]]}")
    print(json.dumps({k: v for k, v in out.items() if k != "excluded_by_code"}, indent=1, default=str))


# D10: final labels that broke the plan's rule (an explicit sampling-site statement; institutions are not evidence)
D10_NOT_STATED = {"R240": "US state code in collected_by only", "R241": "US state code in collected_by only",
                  "R242": "US state code in collected_by only", "R243": "US state code in collected_by only",
                  "R244": "US state code in collected_by only", "R475": "US state code in collected_by only",
                  "R477": "provincial CDC named as collector", "R054": "diet experiment at a research facility",
                  "R461": "USDA germplasm accession's grow-out site"}
APPLY_D10 = "--pre-d10" not in sys.argv


def final_labels():
    R = records()
    l1, l2 = labels(1), labels(2)
    p3 = labels(3) if (GOLD / "pass3_labels.csv").exists() else {}
    fin = {}
    for i in R:
        if exclusion(R[i]):
            continue
        if l1[i] == l2[i]:
            fin[i] = l1[i]
        else:
            assert i in p3, f"{i}: disagreement without a pass-3 label"
            fin[i] = p3[i]
    if APPLY_D10:
        for i in D10_NOT_STATED:
            if i in fin:
                fin[i] = "not stated"
    return R, fin


def tune(rows, arm):
    """Lowest confidence threshold giving at least 90% precision on the tuning rows."""
    cands = sorted({r[f"{arm}_conf"] for r in rows if r[arm]})
    for t in cands:
        made = [r for r in rows if r[arm] and r[f"{arm}_conf"] >= t]
        ok = sum(r[arm] == r["gold"] for r in made)
        if ok / len(made) >= 0.90:
            return {"threshold": t, "tune_predictions": len(made), "tune_correct": ok,
                    "tune_precision": round(ok / len(made), 4)}
    return {"threshold": None}


def evaluate(rows, arm, t):
    made = [r for r in rows if t is not None and r[arm] and r[f"{arm}_conf"] >= t]
    ok = sum(r[arm] == r["gold"] for r in made)
    det = [r for r in rows if r["gold"] != ND]
    return {"n": len(rows), "predictions": len(made), "correct": ok,
            "recovery": round(ok / len(rows), 4), "recovery_ci": wilson(ok, len(rows)),
            "precision": round(ok / len(made), 4) if made else None, "precision_ci": wilson(ok, len(made)),
            "determinable": len(det), "recall_of_determinable": round(ok / len(det), 4) if det else None,
            "recall_ci": wilson(ok, len(det))}


def population():
    """Untagged non-human samples in the gold window, by publication stratum (current classifier and care filter)."""
    import pyarrow.parquet as pq
    bp = pd.read_parquet(RUN / "data" / "bioprojects.parquet")
    with_pub = set(bp.accession[bp.pubmed_ids.fillna("").astype(bool)])
    n = Counter()
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        cols = [c for c in ("submission_date", "country_class", "organism", "host", "bioprojects")
                if c in pq.read_schema(f).names]
        d = pd.read_parquet(f, columns=cols)
        d = d[(d.submission_date >= WINDOW[0]) & (d.submission_date <= WINDOW[1]) & (d.country_class != "usable")]
        if "host" in d:
            d = d[~(d.organism.str.contains("metagenome", case=False, na=False)
                    & d.host.str.contains(r"homo sapiens|\bhuman\b", case=False, na=False))]
        hp = d.bioprojects.fillna("").str.split(";").str[0].isin(with_pub)
        n[True] += int(hp.sum())
        n[False] += int((~hp).sum())
    return n


def project(rows, pop, hit):
    """Stratified projection: sum over strata of N_h * p_h, with the within-stratum binomial variance."""
    tot, var, per = 0.0, 0.0, {}
    for h in (True, False):
        s = [r for r in rows if r["has_pub"] == h]
        if not s:
            continue
        p = sum(hit(r) for r in s) / len(s)
        tot += pop[h] * p
        var += pop[h] ** 2 * p * (1 - p) / len(s)
        per["with_publication" if h else "without_publication"] = {"n_gold": len(s), "share": round(p, 4)}
    N = pop[True] + pop[False]
    se = math.sqrt(var)
    return {"samples": round(tot), "ci": [round(max(0, tot - 1.96 * se)), round(tot + 1.96 * se)],
            "share_of_untagged": round(tot / N, 4), "share_ci": [round(max(0, tot - 1.96 * se) / N, 4),
                                                                  round((tot + 1.96 * se) / N, 4)], "strata": per}


def calibration(rows, arm):
    made = [r for r in rows if r[arm]]
    if not made:
        return {}
    conf = np.array([r[f"{arm}_conf"] for r in made])
    ok = np.array([r[arm] == r["gold"] for r in made], dtype=float)
    bins = []
    for lo, hi in ((0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, .9), (.9, 1.0001)):
        m = (conf >= lo) & (conf < hi)
        if m.any():
            bins.append({"bin": [lo, min(hi, 1.0)], "n": int(m.sum()), "mean_conf": round(float(conf[m].mean()), 3),
                         "accuracy": round(float(ok[m].mean()), 3)})
    return {"predictions": len(made), "brier": round(float(((conf - ok) ** 2).mean()), 4), "bins": bins}


def asymmetric(rows, arm, t, oc):
    """Share of an arm's errors that name the submitter's country (BioSample owner, else BioProject submitter)."""
    err = [r for r in rows if r[arm] and (t is None or r[f"{arm}_conf"] >= t) and r[arm] != r["gold"]]
    known = [r for r in err if oc.get(r["record"])]
    hit = sum(r[arm] == oc[r["record"]] for r in known)
    return {"errors": len(err), "errors_with_submitter_country": len(known), "naming_submitter_country": hit,
            "share": round(hit / len(known), 4) if known else None, "share_ci": wilson(hit, len(known)),
            "errors_on_not_determinable": sum(r["gold"] == ND for r in err)}


def score():
    R, fin = final_labels()
    arms = {x["record"]: x for x in (json.loads(l) for l in open(GOLD / "arms.jsonl"))}
    rows = []
    for i, lab in fin.items():
        a = arms[i]
        rows.append({"record": i, "split": R[i]["split"], "has_pub": R[i]["has_pub"], "label": lab,
                     "gold": scoring(lab), **{k: a[k] for k in a if k.split("_")[0] in ARMS and k != "llm_note"}})
    tune_rows = [r for r in rows if r["split"] == "tune"]
    test_rows = [r for r in rows if r["split"] == "test"]
    out = {"scored": len(rows), "tune": len(tune_rows), "test": len(test_rows),
           "labels": {s: dict(Counter(coarse(r["label"]) for r in rows if s == "all" or r["split"] == s))
                      for s in ("all", "tune", "test")},
           "labels_by_stratum": {("with_publication" if h else "without_publication"):
                                 dict(Counter(coarse(r["label"]) for r in rows if r["has_pub"] == h)) for h in (True, False)},
           "gold_countries": dict(Counter(r["gold"] for r in rows if r["gold"] != ND).most_common()),
           "arms": {}}
    for arm in ARMS:
        th = tune(tune_rows, arm)
        out["arms"][arm] = {"tuning": th, "test": evaluate(test_rows, arm, th["threshold"]),
                            "test_any_confidence": evaluate(test_rows, arm, 0.0)}
    ok = [a for a, v in out["arms"].items() if v["tuning"]["threshold"] is not None
          and v["test"]["recovery"] >= 0.40 and (v["test"]["precision"] or 0) >= 0.90
          and v["test"]["precision_ci"][0] >= 0.85]
    refuted = all(v["test"]["recovery_ci"][1] < 0.40 for v in out["arms"].values())
    out["H2"] = "Supported" if ok else "Refuted" if refuted else "Inconclusive"
    out["H2_arms_meeting_rule"] = ok
    json.dump(out, open(TAB / "limb2_primary.json", "w"), indent=1, default=str)
    sec = {}
    pop = population()
    sec["population_untagged"] = {"with_publication": pop[True], "without_publication": pop[False]}
    sec["projection_label_shares"] = {c: project(test_rows + tune_rows, pop, lambda r, c=c: coarse(r["label"]) == c)
                                      for c in ("inapplicable", "not stated", "country")}
    sec["projection_recoverable_test"] = {a: project(test_rows, pop, lambda r, a=a, t=out["arms"][a]["tuning"]["threshold"]:
                                                     t is not None and bool(r[a]) and r[f"{a}_conf"] >= t
                                                     and r[a] == r["gold"]) for a in ARMS}
    sec["calibration"] = {a: calibration(rows, a) for a in ARMS}
    oc_path = GOLD / "owner_countries.csv"
    if oc_path.exists():
        oc = pd.read_csv(oc_path, keep_default_na=False)
        oc = {r.record: (r.owner_country or r.submitter_country or None) for r in oc.itertuples()}
        sec["asymmetric_error"] = {a: {"test_at_threshold": asymmetric(test_rows, a, out["arms"][a]["tuning"]["threshold"], oc),
                                       "all_records_any_confidence": asymmetric(rows, a, None, oc)} for a in ARMS}
        sec["gold_country_equals_submitter_country"] = {
            "determinable": sum(r["gold"] != ND for r in rows),
            "same": sum(r["gold"] != ND and oc.get(r["record"]) == r["gold"] for r in rows),
            "submitter_country_known": sum(r["gold"] != ND and bool(oc.get(r["record"])) for r in rows)}
    json.dump(sec, open(TAB / "limb2_secondary.json", "w"), indent=1, default=str)
    pd.DataFrame(rows).to_csv(TAB / "limb2_rows.csv", index=False)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"agree": agree, "score": score}[sys.argv[1]]()
