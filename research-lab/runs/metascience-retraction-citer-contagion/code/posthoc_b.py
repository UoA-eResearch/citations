"""Post hoc design B (D1.4): not-yet-treated controls.

Controls are works in the same source and year as the exposed work that cite at least one Retraction Watch-retracted
paper, but only papers retracted after T+4 (so untreated through the event window), and are not themselves exposed.
Matching and the effect are as in posthoc.py (trajectory to T-1; mean T+1..T+4 minus T-1).

  posthoc_b.py select   -> data/interim/candidates_nyt.parquet, data/interim/targets_nyt.npy
  posthoc_b.py count    -> data/interim/cites_nyt.parquet (citations per year to new candidates)
  posthoc_b.py analyse  -> results/tables/posthoc_b.json, event_profile_nyt.csv
"""
import glob
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import build as Bd  # noqa: E402

INT = Bd.INT


def select():
    rng = np.random.default_rng(Bd.SEED + 11)
    R = pd.read_parquet(INT / "retracted.parquet").merge(pd.read_parquet(INT / "rw.parquet"), on="doi")
    ry = dict(zip(R.wid, R.ret_year))
    C = pd.read_parquet(INT / "citers1.parquet")
    C["first_ret"] = [min((ry[r] for r in c if r in ry), default=9999) for c in C.cited]
    D1, D2 = pd.read_parquet(INT / "d1.parquet"), pd.read_parquet(INT / "d2.parquet")
    exposed = set(D1.wid) | set(D2.wid) | set(R.wid)
    C = C[~C.wid.isin(exposed)]
    W = pd.concat([pd.DataFrame({k: v for k, v in np.load(f).items() if k in ("wid", "src", "oaret")})
                   for f in sorted(glob.glob(str(INT / "works" / "*.npz")))])
    W = W[W.wid.isin(set(C.wid)) & ~W.oaret]
    C = C.merge(W[["wid", "src"]], on="wid")
    E = pd.read_parquet(INT / "exposed_meta.parquet").merge(pd.concat([D1[["wid", "T"]], D2[["wid", "T"]]]), on="wid")
    cells = {k: g for k, g in C.groupby(["src", "year"])}
    rows = []
    for e in E.itertuples():
        g = cells.get((e.src, e.year))
        if g is None:
            continue
        pool = g.wid.to_numpy()[g.first_ret.to_numpy() > e.T + 4]
        if len(pool) == 0:
            continue
        pick = pool[rng.choice(len(pool), min(20, len(pool)), replace=False)]
        rows += [{"exposed": e.wid, "cand": int(c)} for c in pick]
    P = pd.DataFrame(rows)
    P.to_parquet(INT / "candidates_nyt.parquet", index=False)
    old = set(np.load(INT / "targets.npy").tolist())
    new = np.array(sorted(set(P.cand) - old), np.int64)
    np.save(INT / "targets_nyt.npy", new)
    print("exposed with not-yet-treated candidates", P.exposed.nunique(), "of", len(E), "rows", len(P), "new targets", len(new))


def _init():
    Bd.TARGET = np.load(INT / "targets_nyt.npy")


def count():
    parts = []
    with ProcessPoolExecutor(Bd.WORKERS, initializer=_init) as ex:
        for k, r in enumerate(ex.map(Bd._d, Bd.files(), chunksize=4), 1):
            parts.append(r)
            if k % 400 == 0:
                print(k, "files", flush=True)
    d = pd.concat(parts).groupby(["wid", "cyear"]).n.sum().reset_index()
    d.to_parquet(INT / "cites_nyt.parquet", index=False)
    print("rows", len(d))


def analyse():
    import analyse as A
    import posthoc as PH
    rng = np.random.default_rng(A.SEED + 13)
    E, _, cites = A.load()
    for w, g in pd.read_parquet(INT / "cites_nyt.parquet").groupby("wid"):
        cites[w] = dict(zip(g.cyear.astype(int), g.n.astype(int)))
    P = pd.read_parquet(INT / "candidates_nyt.parquet")
    R, prof = PH.rows(PH.match_t1(E, P, cites), cites)
    M = A.ret_means(R)
    out = {"pairs": {str(d): int((R.depth == d).sum()) for d in (1, 2)}}
    for d in (1, 2):
        m = M[M.depth == d]
        e_, c_, n_ = A.boot_mean(m, rng)
        out[f"depth{d}"] = {"effect": round(e_, 5), "ci": [round(x, 5) for x in c_], "retractions": n_, "pct": round(100 * (np.exp(e_) - 1), 2)}
        for cls in ("misconduct", "honest", "other"):
            msk = (m.cls == cls).to_numpy()
            if msk.sum() >= 30:
                e2, c2, n2 = A.boot_mean(m, rng, msk)
                out[f"depth{d}"][cls] = {"effect": round(e2, 5), "ci": [round(x, 5) for x in c2], "n": n2}
    pr = prof.groupby(["ret", "depth", "k"]).d.mean().reset_index().groupby(["depth", "k"]).d.agg(["mean", "count"]).reset_index()
    pr.to_csv(A.TAB / "event_profile_nyt.csv", index=False)
    (A.TAB / "posthoc_b.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    print(pr.to_string())


if __name__ == "__main__":
    {"select": select, "count": count, "analyse": analyse}[sys.argv[1]]()
