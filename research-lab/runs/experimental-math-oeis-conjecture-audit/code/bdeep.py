"""Direct b-file test on a random sample (D2, after the independent review's finding 5; post hoc, labelled as such).

The plan allowed up to 2,000 b-file fetches; the confirmation step used 13. The rest of that budget goes to a
seeded random sample of entries that have a real b-file (a Git-LFS pointer in oeisdata/files) and at least one
data-consistent C/G/D conjecture that the editors have not flagged [Wrong]. Each such conjecture is run against
up to 1,000 b-file terms, with no LODA involved. This is one source of terms (the b-file), not the plan's two.

  bdeep.py fetch   fetch the sampled b-files (<= 1 request/s; cached in data/bfiles/)
  bdeep.py test    compare every eligible conjecture on the sampled entries -> data/interim/bdeep.parquet
"""
import json
import os
import re
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import parse as P  # noqa: E402
import screen as S  # noqa: E402

INT, BF = RUN / "data" / "interim", RUN / "data" / "bfiles"
SEED, BUDGET, DEPTH, TLIM = 20261107, 2000, 1000, 30
PAUSE = 5.0          # seconds between requests (raised from 1 s after HTTP 429 responses, then to 5 s)
FORMULA_NOTE = re.compile(r"recurrence|g\.\s*f\.|generating function|formula|conjectur|empirical", re.I)


def population():
    C = pd.read_parquet(INT / "conjectures.parquet")
    C = C[(C.status == "parsed") & (C.data_status == "consistent") & C.cls.isin(["C", "G", "D"]) & ~C.flagged_wrong]
    ents = sorted(C.anum.unique())
    has = {a: S.bfile_pointer(a) for a in ents}
    return C, [a for a in ents if has[a] is not None], has


def sample():
    C, ents, has = population()
    used = pd.read_parquet(INT / "confirm.parquet").anum.nunique()   # fetches spent by the confirmation step (13)
    n = min(BUDGET - used, len(ents))
    rng = np.random.default_rng(SEED)
    pick = sorted(rng.choice(ents, size=n, replace=False).tolist())
    return C, ents, pick, used


def fetch():
    C, ents, pick, used = sample()
    print(f"population {len(ents)} entries with a b-file; already fetched {used}; sampling {len(pick)}", flush=True)
    meta = BF / "meta.jsonl"
    done = 0
    for k, a in enumerate(pick, 1):
        f = BF / f"b{a[1:]}.json"
        if f.exists():
            continue
        url = f"https://oeis.org/{a}/b{a[1:]}.txt"
        import urllib.error
        import urllib.request
        try:
            txt, wait = None, 60
            for attempt in range(6):                      # oeis.org answered 429 at 1 request/s: back off and retry
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers=S.UA), timeout=60) as r:
                        txt = r.read().decode("utf-8", "replace")
                    break
                except urllib.error.HTTPError as he:
                    if he.code != 429 or attempt == 5:
                        raise
                    time.sleep(wait); wait *= 2
            out, note = {}, False
            for line in txt.splitlines():
                if line.lstrip().startswith("#"):
                    note = note or bool(FORMULA_NOTE.search(line))
                    continue
                p = line.split("#")[0].split()
                if len(p) >= 2 and p[0].lstrip("-").isdigit() and p[1].lstrip("-").isdigit():
                    out[int(p[0])] = int(p[1])
            f.write_text(json.dumps(out))
            with meta.open("a") as m:
                m.write(json.dumps({"anum": a, "terms": len(out), "comment_mentions_formula": note}) + "\n")
        except Exception as e:
            with meta.open("a") as m:
                m.write(json.dumps({"anum": a, "error": str(e)[:80]}) + "\n")
        done += 1
        if k % 100 == 0:
            print(k, "of", len(pick), flush=True)
        time.sleep(PAUSE)
    print("fetched", done)


def _alarm(signum, frame):
    raise P.Timeout()


def one(row):
    signal.signal(signal.SIGALRM, _alarm)
    a = row["anum"]
    res = {"anum": a, "line_no": row["line_no"], "cls": row["cls"], "nterms": row["nterms"]}
    f = BF / f"b{a[1:]}.json"
    if not f.exists():
        return {**res, "bdeep": "no_bfile_fetched"}
    b = {int(k): v for k, v in json.loads(f.read_text()).items()}
    e = P.read_entry(P.SEQ / a[:4] / f"{a}.seq")
    terms, off = e["terms"], int(row["offset"])
    if not b or any(b.get(off + i, v) != v for i, v in enumerate(terms)):
        return {**res, "bdeep": "bfile_disagrees_with_data"}
    # contiguous b-file terms from the offset
    last = off - 1
    while last + 1 in b:
        last += 1
    upto = min(last - off + 1, DEPTH)
    res["bfile_terms"] = last - off + 1
    if upto <= len(terms):
        return {**res, "bdeep": "bfile_covers_only_data"}
    signal.alarm(TLIM)
    try:
        P.run_gf.shifted = False
        ok, pred, _, _ = (P.run_gf if row["cls"] == "G" else P.run_rec)(json.loads(row["pred"]), terms, off, upto)
    except P.Timeout:
        return {**res, "bdeep": "timeout"}
    except Exception:
        return {**res, "bdeep": "predict_error"}
    finally:
        signal.alarm(0)
    first, checked, bv, pv = None, 0, None, None
    for i in range(len(terms), upto):
        if pred is None or i >= len(pred) or pred[i] is None:
            break
        checked += 1
        if Fraction(b[off + i]) != pred[i]:
            first, bv, pv = off + i, str(b[off + i]), str(pred[i])
            break
    if first is None and checked == 0:
        return {**res, "bdeep": "no_term_beyond_data"}
    return {**res, "bdeep": "contradicted" if first is not None else "agrees", "first_fail": first,
            "fail_beyond_data": (first - off - len(terms) + 1) if first is not None else None,
            "bfile_value": bv, "pred_value": pv, "beyond_data_checked": checked}


def test():
    C, ents, pick, used = sample()
    rows = C[C.anum.isin(pick)].to_dict("records")
    out = []
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "24"))) as ex:
        for k, r in enumerate(ex.map(one, rows, chunksize=8), 1):
            out.append(r)
    d = pd.DataFrame(out)
    meta = pd.read_json(BF / "meta.jsonl", lines=True) if (BF / "meta.jsonl").exists() else pd.DataFrame(columns=["anum"])
    if "comment_mentions_formula" in meta:
        d = d.merge(meta[["anum", "comment_mentions_formula"]].drop_duplicates("anum"), on="anum", how="left")
    d["has_program"] = [S.prog_path(a).exists() for a in d.anum]
    d.to_parquet(INT / "bdeep.parquet", index=False)
    (INT / "bdeep_meta.json").write_text(json.dumps({"population_entries": len(ents), "population_lines": int(C.anum.isin(ents).sum()),
                                                      "sampled_entries": len(pick), "seed": SEED, "depth": DEPTH}))
    print("population entries", len(ents), "sampled", len(pick), "lines", len(d))
    print(d.bdeep.value_counts().to_string())


if __name__ == "__main__":
    {"fetch": fetch, "test": test}[sys.argv[1]]()
