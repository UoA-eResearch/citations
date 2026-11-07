"""Blind validation of the comparator (D4, after the independent review's finding 2; post hoc).

  validate_blind.py sample OUT KEY   stratified fresh sample (seed 20261107): 30 text mismatches, 20 text matches,
                                     30 figure mismatches, 15 figure matches under the D4 comparator. Writes the pairs
                                     WITHOUT the comparator's verdict to OUT/pairs.json (+ PNGs in OUT/img/), and the
                                     verdicts to KEY (kept outside the labeller's directory)
  validate_blind.py score OUT KEY    compares OUT/labels.json (written by a separate labeller session that never saw
                                     KEY) with the comparator -> results/tables/validation_blind.json
"""
import base64
import json
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import compare as K  # noqa: E402

STRATA = [("text_mismatch", False, True, 30), ("text_match", False, False, 20),
          ("figure_mismatch", True, True, 30), ("figure_match", True, False, 15)]
SEED = 20261107


def sample(out, key):
    out, key = Path(out), Path(key)
    (out / "img").mkdir(parents=True, exist_ok=True)
    C = pd.read_parquet(K.D / "interim" / "cells.parquet")
    S = pd.read_csv(K.D / "interim" / "sample_ready.csv", dtype=str).set_index("nbid")
    picks = []
    for name, png, mism, n in STRATA:
        g = C[(C.has_png == png) & (C.mismatch == mism)]
        picks.append(g.sample(min(n, len(g)), random_state=SEED).assign(stratum=name))
    P = pd.concat(picks).sample(frac=1, random_state=SEED).reset_index(drop=True)      # shuffle strata together
    pairs, keys = [], []
    for i, r in P.iterrows():
        s = S.loc[r.nbid]
        st = K.items([c for c in K.load(K.D / "repos" / s.repo_id / s.nb_path)["cells"] if c.get("cell_type") == "code"][r.cell])
        ru = K.items([c for c in K.load(K.D / "runs" / r.nbid / "asof_1.ipynb")["cells"] if c.get("cell_type") == "code"][r.cell])
        pid = f"p{i:03d}"

        def show(its, side):
            res = []
            for k, (t, v) in enumerate(its):
                if t == "png":
                    f = out / "img" / f"{pid}_{side}_{k}.png"
                    f.write_bytes(base64.b64decode(v))
                    res.append({"type": "image", "file": f"img/{f.name}"})
                else:
                    res.append({"type": "text", "text": v[:2000] + (" [...truncated]" if len(v) > 2000 else "")})
            return res
        pairs.append({"pair": pid, "stored": show(st, "stored"), "rerun": show(ru, "rerun")})
        keys.append({"pair": pid, "nbid": r.nbid, "cell": int(r.cell), "stratum": r.stratum, "comparator_mismatch": bool(r.mismatch)})
    (out / "pairs.json").write_text(json.dumps(pairs, indent=1))
    key.write_text(json.dumps(keys, indent=1))
    print(len(pairs), "pairs ->", out, "; key ->", key)


def rest(out, key):
    """All figure-mismatch cells not in the first sample -> OUT/pairs2.json and KEY (same format), for a complete
    human adjudication of flagged figure mismatches (post hoc)."""
    out, key = Path(out), Path(key)
    done = {(k["nbid"], k["cell"]) for k in json.loads((key.parent / "key.json").read_text())}
    C = pd.read_parquet(K.D / "interim" / "cells.parquet")
    S = pd.read_csv(K.D / "interim" / "sample_ready.csv", dtype=str).set_index("nbid")
    g = C[C.has_png & C.mismatch]
    g = g[[(a, int(c)) not in done for a, c in zip(g.nbid, g.cell)]].reset_index(drop=True)
    pairs, keys = [], []
    for i, r in g.iterrows():
        s = S.loc[r.nbid]
        st = K.items([c for c in K.load(K.D / "repos" / s.repo_id / s.nb_path)["cells"] if c.get("cell_type") == "code"][r.cell])
        ru = K.items([c for c in K.load(K.D / "runs" / r.nbid / "asof_1.ipynb")["cells"] if c.get("cell_type") == "code"][r.cell])
        pid = f"q{i:03d}"
        def show(its, side):
            res = []
            for k, (t, v) in enumerate(its):
                if t == "png":
                    f = out / "img" / f"{pid}_{side}_{k}.png"; f.write_bytes(base64.b64decode(v))
                    res.append({"type": "image", "file": f"img/{f.name}"})
                else:
                    res.append({"type": "text", "text": v[:2000] + (" [...truncated]" if len(v) > 2000 else "")})
            return res
        pairs.append({"pair": pid, "stored": show(st, "stored"), "rerun": show(ru, "rerun")})
        keys.append({"pair": pid, "nbid": r.nbid, "cell": int(r.cell), "stratum": "figure_mismatch_rest", "comparator_mismatch": True})
    (out / "pairs2.json").write_text(json.dumps(pairs, indent=1)); key.write_text(json.dumps(keys, indent=1))
    print(len(pairs), "pairs")


def score(out, key):
    L = pd.DataFrame(json.loads((Path(out) / "labels.json").read_text()))
    Kk = pd.DataFrame(json.loads(Path(key).read_text()))
    M = Kk.merge(L, on="pair", how="left")
    M["human_different"] = M.label.str.lower().eq("different")
    M["agree"] = M.human_different == M.comparator_mismatch
    res = {"pairs": int(len(M)), "labelled": int(M.label.notna().sum()), "agreement": round(float(M.agree.mean()), 3),
           "by_stratum": {s: {"n": int(len(g)), "agree": int(g.agree.sum()), "share": round(float(g.agree.mean()), 3)}
                          for s, g in M.groupby("stratum")},
           "precision_of_flagged_mismatch": {"text": round(float(M[(M.stratum == "text_mismatch")].human_different.mean()), 3),
                                             "figure": round(float(M[(M.stratum == "figure_mismatch")].human_different.mean()), 3)},
           "disagreements": M[~M.agree][["pair", "nbid", "cell", "stratum", "label", "reason"]].to_dict("records")}
    (K.TAB / "validation_blind.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "disagreements"}, indent=1))


if __name__ == "__main__":
    {"sample": sample, "score": score, "rest": rest}[sys.argv[1]](*sys.argv[2:4])
