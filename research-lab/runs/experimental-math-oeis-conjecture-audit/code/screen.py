"""LODA screening and b-file confirmation (plan section 3).

  screen.py screen    run LODA for every data-consistent parsed conjecture with a program -> data/interim/screen.parquet
  screen.py confirm   fetch b-files for screened disagreements (<= 1 request/s, <= 2,000) -> data/interim/confirm.parquet

D2 (after the independent review): only data_status == "consistent" lines are screened (>= 5 data terms checked);
"agree" needs at least one term beyond the data; the LODA and predicted values at a disagreement are stored; each
entry is marked with whether it has a real b-file (Git-LFS pointer in oeisdata/files, which LODA programs are
validated against); a LODA program whose formula comment is the same recurrence is flagged (tautological agreement).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import parse as P  # noqa: E402

RAW, INT = RUN / "data" / "raw", RUN / "data" / "interim"
LODA = RAW / "loda"
PROGS = RAW / "loda-programs" / "oeis"
HOME = RUN / "data" / "loda-home"
UA = {"User-Agent": "research-lab OEIS conjecture audit (open-data research; github.com/UoA-eResearch/citations); max 1 req/s"}


def prog_path(anum):
    return PROGS / anum[1:4] / f"{anum}.asm"


def loda_terms(anum, n):
    env = dict(os.environ, LODA_HOME=str(HOME), HOME=str(HOME))
    try:
        r = subprocess.run([str(LODA), "eval", str(prog_path(anum)), "-t", str(n), "-b", "-z", "20", "-l", "error"],
                           capture_output=True, timeout=40, env=env)
    except subprocess.TimeoutExpired:
        return None
    out = {}
    for line in r.stdout.decode().splitlines():
        p = line.split()
        if len(p) == 2 and p[0].lstrip("-").isdigit() and p[1].lstrip("-").isdigit():
            out[int(p[0])] = int(p[1])
    return out or None


def predict(row, terms, upto):
    p = json.loads(row["pred"])
    return (P.run_gf if row["cls"] == "G" else P.run_rec)(p, terms, row["offset"], upto)[:3]


def bfile_pointer(anum):
    """Size in bytes of the entry's real b-file (Git-LFS pointer), or None if the entry has no b-file."""
    f = RAW / "oeisdata" / "files" / anum[:4] / f"b{anum[1:]}.txt"
    if not f.exists():
        return None
    for line in f.read_text(errors="replace").splitlines():
        if line.startswith("size "):
            return int(line.split()[1])
    return None


def _norm(pred):
    """Relation normalised by the leading coefficient of lead(n): {lag: coeffs}, const, lead."""
    lead = [Fraction(x) for x in pred["lead"]]
    z = lead[-1]
    f = lambda cs: tuple(Fraction(x) / z for x in cs)  # noqa: E731
    return (tuple(sorted((k, f(c)) for k, c in pred["lags"])), f(pred["const"]), f(pred["lead"]))


def loda_same_recurrence(anum, pred_json):
    """True if the LODA program's '; Formula:' comment states the conjecture's own recurrence."""
    try:
        txt = prog_path(anum).read_text(errors="replace")
    except OSError:
        return False
    line = next((ln for ln in txt.splitlines() if ln.startswith("; Formula:")), None)
    if not line:
        return False
    target = _norm(json.loads(pred_json))
    for seg in line[len("; Formula:"):].split(", "):
        if "a(n" not in seg.replace(" ", "") or "=" not in seg:
            continue
        try:
            r = P.parse_rec(seg)
        except Exception:
            continue
        if r and r[0] in ("C", "D") and _norm(r[1]) == target:
            return True
    return False


def one(row):
    e = P.read_entry(P.SEQ / row["anum"][:4] / f"{row['anum']}.seq")
    terms, off = e["terms"], row["offset"]
    res = {"anum": row["anum"], "line_no": row["line_no"], "cls": row["cls"], "has_program": prog_path(row["anum"]).exists(),
           "bfile_bytes": bfile_pointer(row["anum"])}
    if not res["has_program"]:
        return {**res, "screen": "no_program"}
    T = min(2 * len(terms), 1000)
    lt = loda_terms(row["anum"], T)
    if lt is None:
        return {**res, "screen": "loda_failed"}
    if any(lt.get(off + i) != v for i, v in enumerate(terms) if off + i in lt) or len(lt) <= len(terms):
        return {**res, "screen": "loda_mismatch_or_short", "loda_n": len(lt)}
    ok, pred, _ = predict(row, terms, T)
    if not ok or pred is None:
        return {**res, "screen": "predict_failed"}
    first, lv, pv, checked = None, None, None, 0
    for i in range(len(terms), len(pred)):
        n = off + i
        if n not in lt or pred[i] is None:
            break
        checked += 1
        if Fraction(lt[n]) != pred[i]:
            first, lv, pv = n, str(lt[n]), str(pred[i])
            break
    if first is None and checked == 0:
        return {**res, "screen": "no_term_beyond_data", "nterms": len(terms), "loda_n": len(lt)}
    taut = row["cls"] in ("C", "D") and loda_same_recurrence(row["anum"], row["pred"])
    return {**res, "screen": "disagree" if first is not None else "agree", "first_disagree": first,
            "loda_value": lv, "pred_value": pv, "beyond_data_checked": checked, "nterms": len(terms),
            "loda_n": len(lt), "loda_same_recurrence": taut}


def screen():
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "programs").mkdir(exist_ok=True)
    link = HOME / "programs" / "oeis"
    if not link.exists():
        link.symlink_to(PROGS)
    C = pd.read_parquet(INT / "conjectures.parquet")
    C = C[(C.status == "parsed") & (C.data_status == "consistent")]
    rows = C.to_dict("records")
    out = []
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "12"))) as ex:
        for k, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if k % 2000 == 0:
                print(k, "of", len(rows), flush=True)
    d = pd.DataFrame(out)
    d.to_parquet(INT / "screen.parquet", index=False)
    print(d.screen.value_counts().to_string())


def bfile(anum):
    url = f"https://oeis.org/{anum}/b{anum[1:]}.txt"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            txt = r.read().decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)[:80]
    out = {}
    for line in txt.splitlines():
        p = line.split("#")[0].split()
        if len(p) >= 2 and p[0].lstrip("-").isdigit() and p[1].lstrip("-").isdigit():
            out[int(p[0])] = int(p[1])
    return out, None


def confirm():
    S = pd.read_parquet(INT / "screen.parquet")
    C = pd.read_parquet(INT / "conjectures.parquet").set_index(["anum", "line_no"])
    D = S[S.screen == "disagree"].head(2000)
    (RUN / "data" / "bfiles").mkdir(exist_ok=True)
    cache, rows = {}, []
    for r in D.itertuples():
        if r.anum not in cache:
            f = RUN / "data" / "bfiles" / f"b{r.anum[1:]}.json"
            if f.exists():
                cache[r.anum] = ({int(k): v for k, v in json.loads(f.read_text()).items()}, None)   # D2: JSON keys are strings
            else:
                b, err = bfile(r.anum)
                cache[r.anum] = (b, err)
                if b:
                    f.write_text(json.dumps(b))
                time.sleep(1.0)
        b, err = cache[r.anum]
        row = C.loc[(r.anum, r.line_no)]
        e = P.read_entry(P.SEQ / r.anum[:4] / f"{r.anum}.seq")
        off, terms = int(row["offset"]), e["terms"]
        res = {"anum": r.anum, "line_no": r.line_no, "cls": r.cls, "first_disagree": r.first_disagree, "bfile_error": err}
        if not b:
            rows.append({**res, "confirm": "no_bfile"}); continue
        if any(b.get(off + i, v) != v for i, v in enumerate(terms)):
            rows.append({**res, "confirm": "bfile_disagrees_with_data"}); continue
        upto = min(max(b) - off + 1, 5000)
        ok, pred, _ = predict(row.to_dict() | {"offset": off}, terms, upto)
        if pred is None:
            rows.append({**res, "confirm": "predict_failed"}); continue
        first = None
        for i in range(len(terms), len(pred)):
            n = off + i
            if n not in b or pred[i] is None:
                break
            if Fraction(b[n]) != pred[i]:
                first = n
                break
        if first is None:
            rows.append({**res, "confirm": "bfile_agrees_with_conjecture" if (off + len(pred) - 1) >= r.first_disagree else "bfile_too_short",
                         "bfile_max": max(b)}); continue
        rows.append({**res, "confirm": "confirmed" if first <= r.first_disagree else "bfile_fails_later_than_loda",
                     "bfile_first_fail": first, "bfile_max": max(b)})
    d = pd.DataFrame(rows)
    d.to_parquet(INT / "confirm.parquet", index=False)
    print(d.confirm.value_counts().to_string())


if __name__ == "__main__":
    {"screen": screen, "confirm": confirm}[sys.argv[1]]()
