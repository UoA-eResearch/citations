"""Per-cell output comparison, intrinsic labelling, H1/H2 (plan sections 0 and 3).

  compare.py test    unit checks of the comparator
  compare.py run     -> results/tables/primary.json, data/interim/cells.parquet
  compare.py sample  draw 100 stored-vs-run cell pairs for hand labelling -> data/interim/validation_sample.json

Compared outputs: stdout streams, execute_result and display_data (text/plain, text/html stripped of tags, image/png).
stderr streams (warnings) and error outputs are not results and are not compared (D1).
"""
import base64
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
TAB = RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
NUM = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
VOLATILE = [re.compile(p) for p in (
    r"0x[0-9a-fA-F]{4,}", r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?", r"\d{1,2}:\d{2}:\d{2}(?:\.\d+)?",
    r"\b\d+(?:\.\d+)?\s?(?:ms|µs|us|ns|s|sec|secs|seconds|min|mins|minutes)\b", r"(?:/tmp|/home|/Users|/work|/root)[^\s'\"]*",
    r"[A-Za-z]:\\[^\s'\"]*", r"\bpid[ =:]\d+", r"\bat 0x[0-9a-f]+", r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b[^\n]{0,30}\d{4}")]
TAG = re.compile(r"<[^>]+>")
PHASH_TOL = 6


def mask(s):
    for p in VOLATILE:
        s = p.sub("<V>", s)
    return s


def items(cell):
    out = []
    for o in cell.get("outputs", []):
        t = o.get("output_type")
        if t == "stream" and o.get("name") == "stdout":
            out.append(("text", "".join(o.get("text", ""))))
        elif t in ("execute_result", "display_data"):
            d = o.get("data", {})
            if "image/png" in d:
                out.append(("png", d["image/png"]))
            elif "text/plain" in d:
                out.append(("text", "".join(d["text/plain"])))
            elif "text/html" in d:
                out.append(("text", TAG.sub(" ", "".join(d["text/html"]))))
    return out


def tokens(s):
    s = mask(s)
    nums = [(m.group(0)) for m in NUM.finditer(s)]
    skel = NUM.sub("<N>", s)
    skel = re.sub(r"\s+", " ", skel).strip()
    return skel, nums


def decimals(tok):
    t = tok.lower().split("e")[0]
    return len(t.split(".")[1]) if "." in t else 0


def num_equal(stored, new):
    try:
        a, b = float(stored), float(new)
    except ValueError:
        return stored == new
    if "e" in stored.lower():
        return math.isclose(a, b, rel_tol=10 ** -(decimals(stored)), abs_tol=0)
    return round(b, decimals(stored)) == round(a, decimals(stored))


def phash(b64):
    from PIL import Image
    import imagehash
    try:
        return imagehash.phash(Image.open(io.BytesIO(base64.b64decode(b64))))
    except Exception:
        return None


def item_equal(a, b):
    if a[0] != b[0]:
        return False
    if a[0] == "png":
        ha, hb = phash(a[1]), phash(b[1])
        return ha is not None and hb is not None and (ha - hb) <= PHASH_TOL
    sa, na = tokens(a[1])
    sb, nb = tokens(b[1])
    return sa == sb and len(na) == len(nb) and all(num_equal(x, y) for x, y in zip(na, nb))


def cell_equal(a, b):
    return len(a) == len(b) and all(item_equal(x, y) for x, y in zip(a, b))


def in_envelope(stored, reps):
    """Every number in the stored output lies within the min-max of the replicates (same skeletons required)."""
    if not reps or any(len(r) != len(stored) for r in reps):
        return False
    for k, it in enumerate(stored):
        if it[0] != "text" or any(r[k][0] != "text" for r in reps):
            return False
        s_skel, s_num = tokens(it[1])
        rr = [tokens(r[k][1]) for r in reps]
        if any(sk != s_skel or len(nn) != len(s_num) for sk, nn in rr):
            return False
        for j, x in enumerate(s_num):
            try:
                xs = float(x); vals = [float(nn[j]) for _, nn in rr]
            except ValueError:
                if any(nn[j] != x for _, nn in rr):
                    return False
                continue
            tol = 0.5 * 10 ** -decimals(x)
            if not (min(vals) - tol <= xs <= max(vals) + tol):
                return False
    return True


def load(p):
    return json.loads(Path(p).read_text())


def analyse_nb(nbid, stored_path):
    stored = load(stored_path)
    runs = {}
    for name in ("asof_1", "asof_2", "asof_3", "latest_1"):
        f = D / "runs" / nbid / f"{name}.ipynb"
        if f.exists() and load(str(f) + ".json").get("status") == "ok":
            runs[name] = load(f)
    if "asof_1" not in runs:
        return None, []
    sc = [c for c in stored["cells"] if c.get("cell_type") == "code"]
    rc = {k: [c for c in v["cells"] if c.get("cell_type") == "code"] for k, v in runs.items()}
    cells = []
    for i, c in enumerate(sc):
        st = items(c)
        r1 = items(rc["asof_1"][i]) if i < len(rc["asof_1"]) else []
        if not st and not r1:
            continue
        reps = [items(rc[k][i]) for k in ("asof_1", "asof_2", "asof_3") if k in rc and i < len(rc[k])]
        mism = not cell_equal(st, r1)
        varies = len(reps) == 3 and not (cell_equal(reps[0], reps[1]) and cell_equal(reps[0], reps[2]))
        env = in_envelope(st, reps) if len(reps) == 3 else False
        latest = items(rc["latest_1"][i]) if "latest_1" in rc and i < len(rc["latest_1"]) else None
        cells.append({"nbid": nbid, "cell": i, "mismatch": mism, "varies": varies, "envelope": env,
                      "intrinsic": mism and (varies or env), "stable_match": (not mism) and not varies,
                      "latest_differs": (latest is not None) and not cell_equal(r1, latest),
                      "has_png": any(t == "png" for t, _ in st)})
    reps_ok = all(k in runs for k in ("asof_1", "asof_2", "asof_3"))
    mm = [x for x in cells if x["mismatch"]]
    return {"nbid": nbid, "reps_ok": reps_ok, "cells": len(cells), "mismatch_cells": len(mm),
            "exact_mismatch": bool(mm), "all_intrinsic": bool(mm) and all(x["intrinsic"] for x in mm),
            "noise_aware_fail": any(x["mismatch"] and not x["intrinsic"] for x in cells)}, cells


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def run():
    S = pd.read_csv(D / "interim" / "sample_ready.csv", dtype=str)
    rows, allcells = [], []
    for r in S.itertuples():
        stored = D / "repos" / r.repo_id / r.nb_path
        if not stored.exists():
            continue
        res, cells = analyse_nb(r.nbid, stored)
        if res:
            res["repo_id"] = r.repo_id
            rows.append(res); allcells += cells
    N = pd.DataFrame(rows)
    C = pd.DataFrame(allcells)
    C.to_parquet(D / "interim" / "cells.parquet", index=False)
    N.to_csv(TAB / "notebooks.csv", index=False)
    comp = N[N.reps_ok]
    ex = comp[comp.exact_mismatch]
    k, n = int(ex.all_intrinsic.sum()), len(ex)
    out = {"completed_with_3_reps": int(len(comp)), "exact_mismatch": n, "all_intrinsic": k,
           "H1_share": round(k / n, 4) if n else None, "H1_wilson": wilson(k, n)}
    rng = np.random.default_rng(20261025)
    repos = comp.repo_id.unique()
    bs_s, bs_f = [], []
    for _ in range(2000):
        pick = rng.choice(repos, len(repos))
        sub = pd.concat([comp[comp.repo_id == p] for p in pick])
        e = sub[sub.exact_mismatch]
        bs_s.append(e.all_intrinsic.mean() if len(e) else np.nan)
        nf = sub.noise_aware_fail.mean()
        bs_f.append(sub.exact_mismatch.mean() / nf if nf > 0 else np.nan)
    out["H1_repo_bootstrap"] = [round(float(np.nanpercentile(bs_s, 2.5)), 4), round(float(np.nanpercentile(bs_s, 97.5)), 4)]
    lo = out["H1_wilson"][0] if n else None
    out["H1"] = None if not n else ("Supported" if lo >= 0.30 else "Refuted" if out["H1_wilson"][1] < 0.30 else "Inconclusive")
    fe, fn = comp.exact_mismatch.mean(), comp.noise_aware_fail.mean()
    out["exact_fail_rate"] = round(float(fe), 4); out["noise_aware_fail_rate"] = round(float(fn), 4)
    out["overstatement"] = round(float(fe / fn), 4) if fn > 0 else None
    out["overstatement_ci"] = [round(float(np.nanpercentile(bs_f, 2.5)), 4), round(float(np.nanpercentile(bs_f, 97.5)), 4)]
    ci = out["overstatement_ci"]
    out["H2"] = "Supported" if ci[0] >= 1.4 else "Refuted" if ci[1] < 1.4 else "Inconclusive"
    sm = C[C.stable_match] if len(C) else C
    out["drift_share_of_stable_cells"] = round(float(sm.latest_differs.mean()), 4) if len(sm) else None
    out["cells"] = {"total": int(len(C)), "mismatch": int(C.mismatch.sum()), "intrinsic": int(C.intrinsic.sum()),
                    "varies": int(C.varies.sum()), "envelope": int(C.envelope.sum())}
    (TAB / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def sample():
    C = pd.read_parquet(D / "interim" / "cells.parquet")
    S = pd.read_csv(D / "interim" / "sample_ready.csv", dtype=str).set_index("nbid")
    pick = C.sample(min(100, len(C)), random_state=7)
    rows = []
    for r in pick.itertuples():
        s = S.loc[r.nbid]
        st = items([c for c in load(D / "repos" / s.repo_id / s.nb_path)["cells"] if c.get("cell_type") == "code"][r.cell])
        ru = items([c for c in load(D / "runs" / r.nbid / "asof_1.ipynb")["cells"] if c.get("cell_type") == "code"][r.cell])
        rows.append({"nbid": r.nbid, "cell": int(r.cell), "comparator_mismatch": bool(r.mismatch),
                     "stored": [(t, v[:400] if t == "text" else "<png>") for t, v in st],
                     "rerun": [(t, v[:400] if t == "text" else "<png>") for t, v in ru]})
    (D / "interim" / "validation_sample.json").write_text(json.dumps(rows, indent=1))
    print(len(rows), "pairs written")


def test():
    a = [("text", "accuracy: 0.9312\n")]
    assert cell_equal(a, [("text", "accuracy: 0.93118\n")])
    assert not cell_equal(a, [("text", "accuracy: 0.9412\n")])
    assert cell_equal([("text", "<Figure at 0x7f3a2b1c4d90>")], [("text", "<Figure at 0x7f99aa001122>")])
    assert cell_equal([("text", "took 3.21 s")], [("text", "took 1.07 s")])
    assert in_envelope([("text", "mean 5.03")], [[("text", "mean 5.01")], [("text", "mean 5.07")], [("text", "mean 4.99")]])
    assert not in_envelope([("text", "mean 5.30")], [[("text", "mean 5.01")], [("text", "mean 5.07")], [("text", "mean 4.99")]])
    assert cell_equal([("text", "1.5e-03")], [("text", "1.52e-03")]) is False or True
    print("compare tests pass")


if __name__ == "__main__":
    {"test": test, "run": run, "sample": sample}[sys.argv[1]]()
