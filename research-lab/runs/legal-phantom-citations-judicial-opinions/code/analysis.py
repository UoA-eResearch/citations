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


def completeness_filter(cands, mis, vols):
    """The preregistered filter (D6), used by prepare() and, for recall, by score(). Returns (kept, drop counts)."""
    # D6: a volume is complete for a candidate if, leaving out that candidate's own opinion's uncovered citations
    # into it, at least 98% of at least 20 citations find their case in the corpus (verdict consistent or
    # name-exists). Resolution alone is not coverage: a citation to a case the corpus lacks still "resolves" by
    # landing inside a neighbouring case's page range.
    uncovered = Counter()
    for c in cands + mis:
        vk = volume_key(c["cite"])
        if vk:
            uncovered[(c["opinion_id"], vk)] += 1

    def complete_for(c, vk):
        n = vols.get(vk + "|n", 0) - uncovered[(c["opinion_id"], vk)]
        return n >= COMPLETE_MIN_CITES and vols.get(vk + "|cov", 0) / n >= COMPLETE_RATE

    kept, drop = [], Counter()
    for c in cands:
        p = period(int(c["date"]))
        if p is None:
            drop["outside both periods"] += 1; continue
        vk = volume_key(c["cite"])
        if vk is None or not complete_for(c, vk):
            drop["incomplete or unassessable reporter-volume"] += 1; continue
        c["period"] = p
        c["type"] = "flag" if FLAG.search(c.get("context", "")) else "reliance"
        kept.append(c)
    return kept, drop


def prepare():
    vols = json.load(open(S / "volumes.json"))["volumes"]
    cands = load_jsonl(S / "candidates.jsonl")
    mis = load_jsonl(S / "misattributions.jsonl")
    kept, drop = completeness_filter(cands, mis, vols)

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


# D9: the judge-attributed incidents matched in the corpus, read: is the document the opinion that relied on the
# fabricated authority, or a reviewing court's opinion about a lower court's order (which is not in the corpus)?
JUDGE_DOC = {10621620: "relying opinion",            # In re CorMedix (D.N.J.), the original opinion
             10620062: "reviewing-court opinion",     # Shahid v. Esaam (Ga. Ct. App.) on a trial court's order
             10853110: "reviewing-court opinion",     # Payne v. State (Ga. Sup. Ct.)
             10865888: "reviewing-court opinion",     # H.C. v. Contreras (Cal. Ct. App. 5th)
             10873094: "reviewing-court opinion"}     # Henry County Schools v. Grant (Ga. Ct. App.)


# D9: flag opinions the name match missed, checked by hand against the database (garbled or "In re" captions)
HAND_DB = {10772904: "Zaykariya v. Freedom Mortgage Corporation (W.D. Okla., 2026-01-09)",
           10808040: "Bolden v. Baltimore Gas & Electric Co (In re: Eric Chibueze Nwaubani) (4th Cir., 2026-03-11)"}


def flag_vs_database(flag_ops, ver):
    """Screened-period opinions with a court-flagged phantom, against the AI Hallucination Cases database:
    matched by cluster (charlotin_matched.csv), or by a date-free name match (party_score >= 85) to any in-window
    US incident -- a second order in the same case, or a date outside the matcher's window, is the same case."""
    import numpy as np
    from rapidfuzz import fuzz
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from match_charlotin import NON_US, WIN_FROM, WIN_TO, MATCH
    from namenorm import norm_name, party_score
    idx = RUN / "data" / "index"
    names = np.load(idx / "names.npy", allow_pickle=True)
    ids = np.load(idx / "cluster_meta.npz")["ids"]
    pos = {int(c): i for i, c in enumerate(ids)}
    clusters = sorted({int(v["cluster_id"]) for v in ver if v["opinion_id"] in flag_ops})
    db = [r for r in csv.DictReader(open(RUN / "data" / "raw" / "charlotin.csv", encoding="utf-8"))
          if not NON_US.search(r["Court"] + " " + r.get("State(s)", "")) and WIN_FROM <= (r["Date"] or "") <= WIN_TO]
    db_names = [norm_name(r["Case Name"]) for r in db]
    matched_clusters = {int(r["cluster_id"]) for r in csv.DictReader(open(S / "charlotin_matched.csv"))
                        if r["matched"] == "1"}
    rows = []
    for c in clusters:
        nm = norm_name(str(names[pos[c]])) if c in pos else ""
        best = max(((party_score(fuzz, d, nm), i) for i, d in enumerate(db_names)), default=(0, None))
        rows.append({"cluster_id": c, "name": nm[:80], "by_cluster": c in matched_clusters,
                     "by_name": best[0] >= MATCH, "best_score": round(best[0], 1),
                     "best_case": db[best[1]]["Case Name"][:80] if best[1] is not None else ""})
    with open(S / "flag_vs_database.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    inn = [r for r in rows if r["by_cluster"] or r["by_name"]]
    hand = {c: HAND_DB[c] for c in (r["cluster_id"] for r in rows if not (r["by_cluster"] or r["by_name"])) if c in HAND_DB}
    return {"flag_opinions": len(flag_ops), "clusters": len(clusters), "in_database_by_cluster":
            sum(r["by_cluster"] for r in rows), "in_database_by_cluster_or_name": len(inn),
            "found_by_hand": hand, "in_database_total": len(inn) + len(hand),
            "not_in_database": len(rows) - len(inn) - len(hand), "us_incidents_in_window": len(db),
            "note": "automatic: cluster match or a date-free caption match at the matcher's threshold; the rest "
                    "checked by hand against the database"}


def reporter_table(cands, kept):
    """Candidates and survivors of the completeness filter by reporter, screened and placebo periods (D9)."""
    allc, keep = Counter(), Counter()
    for c in cands:
        if period(int(c["date"])) is None:
            continue
        vk = volume_key(c["cite"])
        allc[vk.split("|")[0] if vk else "(unparsed)"] += 1
    for c in kept:
        vk = volume_key(c["cite"])
        keep[vk.split("|")[0] if vk else "(unparsed)"] += 1
    top = [r for r, _ in allc.most_common(25)] + [r for r, _ in keep.most_common(10) if r not in dict(allc.most_common(25))]
    return {"total_candidates": sum(allc.values()), "kept": sum(keep.values()),
            "by_reporter": {r: {"candidates": allc[r], "kept": keep[r]} for r in top}}


def score():
    ops = list(csv.DictReader(open(S / "opinions.tsv"), delimiter="\t"))
    n_op = Counter(period(int(o["date"])) for o in ops if int(o["n_full"]) >= 0)
    prep = json.load(open(T / "prepare_summary.json"))
    ver = list(csv.DictReader(open(S / "verified.csv")))
    # a verified phantom is a citation hand-checked as findable nowhere -- not in the corpus, not by external lookup
    # D9: "phantom" on a reliance sheet is a judge's reliance; "phantom-flag" is a court's own flag on either sheet;
    # "phantom-party-asserted" (only a party says the case does not exist) is reported apart and counted in neither
    phantom_ops = defaultdict(set)
    party_asserted = defaultdict(set)
    for v in ver:
        if v["verdict"] == "phantom" and v["type"] == "reliance":
            phantom_ops[(v["period"], "reliance")].add(v["opinion_id"])
        elif v["verdict"] == "phantom-flag" or (v["verdict"] == "phantom" and v["type"] == "flag"):
            phantom_ops[(v["period"], "flag")].add(v["opinion_id"])
        elif v["verdict"] == "phantom-party-asserted":
            party_asserted[v["period"]].add(v["opinion_id"])
    party_asserted = {p: set(o) - phantom_ops[(p, "flag")] for p, o in party_asserted.items()}

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

    out["flag_opinions_party_asserted_only"] = {p: len(o) for p, o in party_asserted.items()}
    k1 = out["screened_reliance"]["estimate"]
    sr = out["screened_reliance"]
    if sr["sampled"]:
        # D9: a sampled sheet decides the rule only if its interval lies within one band
        lo1, hi1 = sr["ci"]
        v1 = "Supported" if lo1 >= H1_SUPPORT else "Refuted" if hi1 < H1_REFUTE else "Inconclusive"
        rule = (f"sampled sheet (D9): Supported if the 95% lower bound >= {H1_SUPPORT}, Refuted if the upper bound "
                f"< {H1_REFUTE}, otherwise Inconclusive; the plan's rule ({'>='} {H1_SUPPORT} / < {H1_REFUTE}) was "
                f"written for a full count")
    else:
        v1 = "Supported" if k1 >= H1_SUPPORT else "Refuted" if k1 < H1_REFUTE else "Inconclusive"
        rule = f">= {H1_SUPPORT} Supported, < {H1_REFUTE} Refuted"
    out["H1"] = {"count": k1, "verdict": v1, "rule": rule,
                 "point_estimate_band": "Supported" if k1 >= H1_SUPPORT else "Refuted" if k1 < H1_REFUTE else
                 "Inconclusive"}
    r_s = out["screened_reliance"]["per_10k_opinions"]
    r_p = out["placebo_reliance"]["per_10k_opinions"]
    ratio = r_p / r_s if r_s else None
    out["H2"] = {"placebo_rate": r_p, "screened_rate": r_s, "ratio": ratio,
                 "verdict": "not scorable" if ratio is None else "Supported" if ratio <= H2_SUPPORT else
                 "Refuted" if ratio > H2_REFUTE else "Inconclusive"}

    # recall, from the calibration set (D4, D9): per distinct cluster, before the completeness filter (any candidate
    # in the order) and after it (a candidate that survives the filter -- the recall that governs the verified counts)
    cands = load_jsonl(S / "candidates.jsonl")
    kept, _ = completeness_filter([dict(c) for c in cands], load_jsonl(S / "misattributions.jsonl"),
                                  json.load(open(S / "volumes.json"))["volumes"])
    pre, post = defaultdict(set), defaultdict(set)
    for c in cands:
        pre[int(c["cluster_id"])].add("flag" if FLAG.search(c.get("context", "")) else "reliance")
    for c in kept:
        post[int(c["cluster_id"])].add(c["type"])
    cal_rows = [r for r in csv.DictReader(open(S / "charlotin_matched.csv")) if r["matched"] == "1"]
    cal = sorted({int(r["cluster_id"]) for r in cal_rows})
    rd = {"incident_rows_matched": len(cal_rows), "orders": len(cal)}
    for name, f in (("pre_filter", pre), ("post_filter", post)):
        k = sum(c in f for c in cal)
        lo, hi = wilson(k, len(cal))
        rd[name] = {"flagged": k, "recall": round(k / max(1, len(cal)), 4), "ci": [round(lo, 4), round(hi, 4)]}
    rd["note"] = ("'flagged' means any candidate in the order, not necessarily the fabricated citation; the "
                  "pre-filter figure is an upper bound on detecting the fabricated citations")
    out["recall_detection"] = rd
    # judge-attributed incidents: which matched document is the relying opinion (read, D9)
    judge_rows = [r for r in cal_rows if "judge" in r["party"].lower()]
    docs = {int(r["cluster_id"]): {"case": r["case_name"], "court": r["court"],
                                   "document": JUDGE_DOC.get(int(r["cluster_id"]), "unclassified"),
                                   "pre_filter": sorted(pre.get(int(r["cluster_id"]), [])),
                                   "post_filter": sorted(post.get(int(r["cluster_id"]), []))} for r in judge_rows}
    relying = [c for c, d in docs.items() if d["document"] == "relying opinion"]
    out["recall_reliance"] = {
        "judge_attributed_in_window": sum("judge" in r["party"].lower() for r in csv.DictReader(open(S / "charlotin_matched.csv"))),
        "judge_attributed_matched": len(docs), "documents": docs,
        "relying_opinions_in_corpus": len(relying),
        "relying_flagged_as_reliance_pre_filter": sum("reliance" in pre.get(c, set()) for c in relying),
        "relying_flagged_as_reliance_post_filter": sum("reliance" in post.get(c, set()) for c in relying)}
    rec = rd["post_filter"]["recall"]
    out["recall_corrected_screened_reliance"] = {
        "post_filter_recall": rec,
        "estimate": round(k1 / rec, 1) if rec else None,
        "upper_bound": round(sr.get("ci", [0, k1])[1] / rec, 0) if rec else None,
        "note": "the sample's 95% upper bound divided by the post-filter detection recall"}
    # flag opinions against the database (D9): by cluster, and by a date-free name match at the matcher's threshold
    out["flag_vs_database"] = flag_vs_database(phantom_ops[("screened", "flag")], ver)
    out["reporters"] = reporter_table(cands, kept)

    # capture-recapture (Chapman): source 1 the screen's verified reliance opinions, source 2 the database's
    # judge-attributed incidents found in the corpus. With counts this small it is a rough guide at best.
    screen_ids = {v["cluster_id"] for v in ver if v["verdict"] == "phantom" and v["type"] == "reliance"
                  and v["period"] == "screened"}
    db_ids = {str(c) for c in docs}
    n1, n2, m = len(screen_ids), len(db_ids), len(screen_ids & db_ids)
    out["capture_recapture"] = {"screen": n1, "database": n2, "both": m,
                                "chapman_N": round((n1 + 1) * (n2 + 1) / (m + 1) - 1, 1),
                                "note": "uninformative: no verified reliance and no overlap (D9)"}
    json.dump(out, open(T / "primary.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"prepare": prepare, "score": score}[sys.argv[1]]()
