"""Find the Charlotin AI Hallucination Cases incidents that are in the CourtListener corpus (plan section 4, step 6).

The database records incidents where a court found fabricated citations, mostly in filings by lawyers and
self-represented parties, and in a handful of matters in a judge's own opinion. Each incident's order usually
discusses -- and often quotes -- the fabricated citations. So the incidents present in the corpus serve two
calibration purposes, measured but never used to retune the screen (D2):

  detection recall   of the in-window orders that discuss fabricated citations, how many does the screen flag?
  reliance recall    of the judge-attributed incidents, how many does the screen flag as reliance, not flag?

An incident is matched to a cluster by party names (side-by-side score) and filing date within MAX_DAYS. The
match is written for every incident, with its score and date gap, so the threshold can be audited.

Writes data/screen/charlotin_matched.csv and results/tables/charlotin_coverage.json.
"""
import csv
import json
import pickle
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from namenorm import distinctive, norm_name, party_score  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, IDX, OUT, T = (RUN / "data" / "raw", RUN / "data" / "index", RUN / "data" / "screen",
                    RUN / "results" / "tables")
WIN_FROM, WIN_TO = "2023-01-01", "2026-09-30"
MATCH = 85            # stricter than the screen's 80: a false calibration match would bias recall
MAX_DAYS = 45         # the order addressing the fabrication is usually filed close to the recorded date
# Two independent signals: a lower name score is accepted when the filing date agrees almost exactly. Set after
# auditing borderline matches, before any screen output existed: *Adams v. Board of Trustees* (82.8) and *Bell v.
# City of Clairton* (84.2) were filed the same day as their incidents and are plainly the same cases -- the
# corpus captions carry full first names the database omits.
MATCH_SAME_DAY, SAME_DAY = 75, 3
NON_US = re.compile(
    r"\b(Canada|UK|England|Australia|India|Israel|South Africa|New Zealand|Ireland|Wales|Scotland|Netherlands|"
    r"Spain|Brazil|Argentina|Chubut|Turkey|KKTC|Yarg|Colombia|Mexico|Germany|Italy|France|Trinidad|Philippines|"
    r"Kenya|Nigeria|Singapore|Malaysia|Hong Kong|Ontario|Quebec|British Columbia|Alberta|NSW|Victoria|"
    r"Queensland|FCA|FWC|EWHC|EWCA|UKUT|UKFTT|BCSC|ONSC)\b", re.I)


def to_int(d):
    return int(d.replace("-", "")) if d and len(d) >= 10 else 0


def days_between(a, b):
    try:
        da = date(a // 10000, a // 100 % 100, a % 100)
        db = date(b // 10000, b // 100 % 100, b % 100)
        return abs((da - db).days)
    except ValueError:
        return 10 ** 6


def main():
    OUT.mkdir(parents=True, exist_ok=True); T.mkdir(parents=True, exist_ok=True)
    names = np.load(IDX / "names.npy", allow_pickle=True)
    meta = np.load(IDX / "cluster_meta.npz")
    ids, dates = meta["ids"], meta["dates"]
    tokens = pickle.load(open(IDX / "tokens.pkl", "rb"))
    dropped = set(json.load(open(IDX / "dropped_tokens.json"))["dropped"])

    rows = list(csv.DictReader(open(RAW / "charlotin.csv", encoding="utf-8")))
    inc = [r for r in rows if not NON_US.search(r["Court"] + " " + r.get("State(s)", ""))
           and WIN_FROM <= (r["Date"] or "") <= WIN_TO]

    out = []
    for r in inc:
        cited = norm_name(r["Case Name"])
        want = distinctive(cited, dropped)
        pools = [tokens[t] for t in want if t in tokens]
        best = (0.0, None, None)
        if pools:
            rarest = sorted(pools, key=len)[:3]
            cand = np.unique(np.concatenate([p[:20000] for p in rarest]))
            d0 = to_int(r["Date"])
            for i in cand:
                gap = days_between(int(dates[i]), d0)
                if gap > MAX_DAYS:
                    continue
                s = party_score(fuzz, cited, str(names[i]))
                if s > best[0] or (s == best[0] and best[2] is not None and gap < best[2]):
                    best = (s, int(i), gap)
        s, i, gap = best
        ok = (s >= MATCH) or (s >= MATCH_SAME_DAY and gap is not None and gap <= SAME_DAY)
        out.append({
            "case_name": r["Case Name"], "court": r["Court"], "date": r["Date"], "party": r["Party(ies)"],
            "matched": int(ok), "score": round(s, 1),
            "cluster_id": int(ids[i]) if i is not None and ok else "",
            "cluster_name": str(names[i])[:90] if i is not None else "", "days_apart": gap if gap is not None else "",
        })

    with open(OUT / "charlotin_matched.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    judge = [o for o in out if "judge" in o["party"].lower()]
    summary = {
        "incidents_us_in_window": len(out), "matched_to_a_cluster": sum(o["matched"] for o in out),
        "judge_attributed": len(judge), "judge_attributed_matched": sum(o["matched"] for o in judge),
        "by_party": {}, "match_threshold": MATCH, "max_days": MAX_DAYS,
        "same_day_threshold": MATCH_SAME_DAY, "same_day_window": SAME_DAY,
    }
    for o in out:
        b = summary["by_party"].setdefault(o["party"] or "(blank)", [0, 0])
        b[0] += 1; b[1] += o["matched"]
    json.dump(summary, open(T / "charlotin_coverage.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
