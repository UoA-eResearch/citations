"""Turn the screen's output into verification sheets, then verified counts into verdicts (plan sections 2 and 4).

  prepare   after parse.py: apply the preregistered completeness filter, split screened from placebo period,
            classify each phantom candidate as reliance or flag from its context, and write the sheets for
            manual verification. If a sheet is too large to verify exhaustively, a seeded random sample of fixed
            size is drawn (plan §5.2), the rule fixed here before any candidate is seen.
  score     after manual verification (data/screen/verified.csv): verified counts, rates per 10,000 opinions
            with Wilson intervals, the H1 and H2 verdicts, recall from the Charlotin calibration set, a
            recall-corrected estimate and a two-source capture-recapture estimate.

Usage:  analysis.py prepare   |   analysis.py score
"""
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
S, T = RUN / "data" / "screen", RUN / "results" / "tables"

SCREENED = (20230101, 20260930)
PLACEBO = (20190101, 20221231)
COMPLETE_RATE = 0.98          # plan §1: a reporter-volume is complete if at least 98% of citations into it resolve
COMPLETE_MIN_CITES = 20       # fewer citations than this cannot estimate a 98% rate; set before any output (D5)
VERIFY_ALL_UP_TO = 300        # verify every opinion on a sheet up to this many; otherwise a seeded sample of this size
SEED = 20261021
H1_SUPPORT, H1_REFUTE = 20, 10
H2_SUPPORT, H2_REFUTE = 0.25, 0.5

# Context that marks a court discussing somebody else's bad citation (flag) rather than relying on it.
FLAG = re.compile(
    r"fictitious|fictional|non-?existent|does not exist|do not exist|did not exist|no such case|fabricat|"
    r"hallucinat|artificial intelligence|\bA\.?I\.?\b|chat ?gpt|generative|large language model|\bLLM\b|"
    r"sanction|show cause|could not (?:locate|find)|unable to (?:locate|find)|cannot be (?:located|found)|"
    r"bogus|\bfake\b|not a real case|misrepresent", re.I)


def period(d):
    if SCREENED[0] <= d <= SCREENED[1]:
        return "screened"
    if PLACEBO[0] <= d <= PLACEBO[1]:
        return "placebo"
    return None


def norm_reporter(r):
    return "".join(ch for ch in r.lower() if ch.isalnum())


def volume_key(cite):
    """'925 F.3d 1339' -> 'f3d|925'."""
    parts = cite.split()
    if len(parts) < 3:
        return None
    try:
        vol = int(parts[0])
    except ValueError:
        return None
    return f"{norm_reporter(' '.join(parts[1:-1]))}|{vol}"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def load_jsonl(p):
    return [json.loads(x) for x in open(p)] if p.exists() else []


def prepare():
    vols = json.load(open(S / "volumes.json"))["volumes"]
    complete = {}
    for k, n in vols.items():
        if k.endswith("|n"):
            base = k[:-2]
            res = vols.get(base + "|res", 0)
            complete[base] = n >= COMPLETE_MIN_CITES and res / n >= COMPLETE_RATE
    cands = load_jsonl(S / "candidates.jsonl")
    mis = load_jsonl(S / "misattributions.jsonl")

    kept, drop = [], Counter()
    for c in cands:
        p = period(int(c["date"]))
        if p is None:
            drop["outside both periods"] += 1; continue
        vk = volume_key(c["cite"])
        if vk is None or not complete.get(vk, False):
            drop["incomplete or unassessable reporter-volume"] += 1; continue
        c["period"] = p
        c["type"] = "flag" if FLAG.search(c.get("context", "")) else "reliance"
        kept.append(c)

    # one sheet per (period, type); the unit of H1 is the distinct opinion
    sheets = defaultdict(lambda: defaultdict(list))
    for c in kept:
        sheets[(c["period"], c["type"])][c["opinion_id"]].append(c)
    rng = random.Random(SEED)
    summary = {"candidates_from_screen": len(cands), "dropped": dict(drop), "kept": len(kept),
               "misattributions_from_screen": len(mis), "sheets": {}}
    for (p, t), by_op in sorted(sheets.items()):
        ops = sorted(by_op)
        sampled = len(ops) > VERIFY_ALL_UP_TO
        chosen = sorted(rng.sample(ops, VERIFY_ALL_UP_TO)) if sampled else ops
        name = f"verify_{p}_{t}.csv"
        with open(S / name, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["opinion_id", "cluster_id", "date", "court", "cite", "cited_name", "best_name",
                        "best_name_score", "absent_tokens", "context", "verdict", "notes"])
            for o in chosen:
                for c in by_op[o]:
                    w.writerow([o, c["cluster_id"], c["date"], c["court"], c["cite"], c["cited_name"],
                                c.get("best_name"), c.get("best_name_score"), ";".join(c.get("absent_tokens", [])),
                                " ".join((c.get("context") or "").split()), "", ""])
        summary["sheets"][name] = {"opinions": len(ops), "candidates": sum(len(v) for v in by_op.values()),
                                   "sampled": sampled, "opinions_on_sheet": len(chosen)}
    # misattributions: a fixed seeded sample for verification, reported separately, never counted toward H1
    mis_in = [m for m in mis if period(int(m["date"])) == "screened"]
    pick = rng.sample(mis_in, min(100, len(mis_in)))
    with open(S / "verify_misattributions_sample.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["opinion_id", "date", "court", "cite", "cited_name", "resolved_name", "name_found_as",
                    "context", "verdict", "notes"])
        for m in pick:
            w.writerow([m["opinion_id"], m["date"], m["court"], m["cite"], m["cited_name"], m.get("resolved_name"),
                        m.get("best_name"), " ".join((m.get("context") or "").split()), "", ""])
    summary["misattributions_screened_period"] = len(mis_in)
    summary["misattributions_sampled_for_verification"] = len(pick)
    T.mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(T / "prepare_summary.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


def score():
    ops = list(csv.DictReader(open(S / "opinions.tsv"), delimiter="\t"))
    n_op = Counter(period(int(o["date"])) for o in ops if int(o["n_full"]) >= 0)
    prep = json.load(open(T / "prepare_summary.json"))
    ver = list(csv.DictReader(open(S / "verified.csv")))
    # a verified phantom is a citation hand-checked as findable nowhere -- not in the corpus, not by external lookup
    phantom_ops = defaultdict(set)
    for v in ver:
        if v["verdict"] == "phantom":
            phantom_ops[(v["period"], v["type"])].add(v["opinion_id"])

    def est(p, t):
        sheet = prep["sheets"].get(f"verify_{p}_{t}.csv", {"opinions": 0, "opinions_on_sheet": 0, "sampled": False})
        k = len(phantom_ops[(p, t)])
        if not sheet["sampled"]:
            return {"verified": k, "estimate": k, "sampled": False}
        frac = k / max(1, sheet["opinions_on_sheet"])
        lo, hi = wilson(k, sheet["opinions_on_sheet"])
        return {"verified": k, "estimate": round(frac * sheet["opinions"], 1), "sampled": True,
                "ci": [round(lo * sheet["opinions"], 1), round(hi * sheet["opinions"], 1)]}

    out = {"opinions_screened": dict(n_op)}
    for p in ("screened", "placebo"):
        for t in ("reliance", "flag"):
            e = est(p, t)
            n = n_op.get(p, 0)
            lo, hi = wilson(round(e["estimate"]), n)
            e["per_10k_opinions"] = round(1e4 * e["estimate"] / max(1, n), 3)
            e["per_10k_ci"] = [round(1e4 * lo, 3), round(1e4 * hi, 3)]
            out[f"{p}_{t}"] = e

    k1 = out["screened_reliance"]["estimate"]
    out["H1"] = {"count": k1, "verdict": "Supported" if k1 >= H1_SUPPORT else
                 "Refuted" if k1 < H1_REFUTE else "Inconclusive",
                 "rule": f">= {H1_SUPPORT} Supported, < {H1_REFUTE} Refuted"}
    r_s = out["screened_reliance"]["per_10k_opinions"]
    r_p = out["placebo_reliance"]["per_10k_opinions"]
    ratio = r_p / r_s if r_s else None
    out["H2"] = {"placebo_rate": r_p, "screened_rate": r_s, "ratio": ratio,
                 "verdict": "not scorable" if ratio is None else "Supported" if ratio <= H2_SUPPORT else
                 "Refuted" if ratio > H2_REFUTE else "Inconclusive"}

    # recall, from the calibration set (D4): did the screen flag any phantom candidate in each matched order?
    flagged = defaultdict(set)
    for c in load_jsonl(S / "candidates.jsonl"):
        flagged[int(c["cluster_id"])].add(c.get("type") or ("flag" if FLAG.search(c.get("context", "")) else
                                                             "reliance"))
    cal = [r for r in csv.DictReader(open(S / "charlotin_matched.csv")) if r["matched"] == "1"]
    det = [r for r in cal if int(r["cluster_id"]) in flagged]
    lo, hi = wilson(len(det), len(cal))
    out["recall_detection"] = {"orders": len(cal), "flagged": len(det), "recall": round(len(det) / max(1, len(cal)), 3),
                               "ci": [round(lo, 3), round(hi, 3)]}
    judge = [r for r in cal if "judge" in r["party"].lower()]
    jrel = [r for r in judge if "reliance" in flagged.get(int(r["cluster_id"]), set())]
    out["recall_reliance"] = {"judge_attributed_in_corpus": len(judge), "flagged_as_reliance": len(jrel)}
    rec = out["recall_detection"]["recall"]
    if rec:
        out["recall_corrected_screened_reliance"] = round(k1 / rec, 1)

    # capture-recapture (Chapman): source 1 the screen's verified reliance opinions, source 2 the database's
    # judge-attributed incidents found in the corpus. With counts this small it is a rough guide at best.
    screen_ids = {v["cluster_id"] for v in ver if v["verdict"] == "phantom" and v["type"] == "reliance"
                  and v["period"] == "screened"}
    db_ids = {r["cluster_id"] for r in judge}
    n1, n2, m = len(screen_ids), len(db_ids), len(screen_ids & db_ids)
    out["capture_recapture"] = {"screen": n1, "database": n2, "both": m,
                                "chapman_N": round((n1 + 1) * (n2 + 1) / (m + 1) - 1, 1)}
    json.dump(out, open(T / "primary.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"prepare": prepare, "score": score}[sys.argv[1]]()
