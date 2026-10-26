"""Draws and DE jobs (plan sections 0, 3, 4).

  draws.py agemap          -> results/tables/age_map.csv (every development_stage string -> years, bin) (G4)
  draws.py build           -> data/jobs/<contrast>/{counts.f32, meta.csv, donors.csv, draws.csv, genes.txt}
                              + data/meta/contrast_index.csv, results/tables/draw_fallbacks.csv
  draws.py control         -> data/jobs/control_sex/ (G3 positive control: male vs female normal donors)
  draws.py run WORKERS     -> runs code/de.R in the sc-negctl-de:1 image (no network), job lists split across workers
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

RUN = Path(__file__).resolve().parents[1]
META, PB, JOBS, T = RUN / "data" / "meta", RUN / "data" / "pb", RUN / "data" / "jobs", RUN / "results" / "tables"
SEED, R_REAL, B_NULL, MIN_CELLS = 20261027, 25, 500, 10
BINS = ["<40", "40-59", "60-74", ">=75", "unknown"]
WORDS = {"third": 25, "fourth": 35, "fifth": 45, "sixth": 55, "seventh": 65, "eighth": 75, "ninth": 85, "tenth": 95}
YOUNG = ("newborn", "pediatric", "child stage", "juvenile", "post-fertilization", "carnegie", "embryonic", "fetal")


def parse_age(s):
    """development_stage label -> (years or NaN, bin). Deterministic; every distinct string is listed in age_map.csv."""
    t = str(s).lower()
    if m := re.match(r"(\d+)-year-old stage", t):
        y = float(m.group(1))
    elif m := re.match(r"(\d+)-month-old stage", t):
        y = float(m.group(1)) / 12
    elif m := re.match(r"(\d+) year-old and over stage", t):
        y = float(m.group(1)) + 5
    elif m := re.match(r"(\d+)-(\d+) year-old", t):
        y = (float(m.group(1)) + float(m.group(2))) / 2
    elif m := re.match(r"(\w+) decade stage", t):
        y = float(WORDS.get(m.group(1), np.nan))
    elif any(k in t for k in YOUNG):
        return np.nan, "<40"
    else:
        return np.nan, "unknown"
    if np.isnan(y):
        return y, "unknown"
    return y, "<40" if y < 40 else "40-59" if y < 60 else "60-74" if y < 75 else ">=75"


def agemap():
    o = pd.read_parquet(META / "obs_counts.parquet")
    s = sorted(o.development_stage.astype(str).unique())
    rows = [(x, *parse_age(x)) for x in s]
    T.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["development_stage", "years", "bin"]).to_csv(T / "age_map.csv", index=False)
    print(pd.DataFrame(rows, columns=["s", "y", "bin"]).bin.value_counts().to_dict())


def eligible_donors():
    """(dataset_id, donor_id) pairs with a single disease label among the dataset's primary cells (plan section 1)."""
    o = pd.read_parquet(META / "obs_counts.parquet")
    o = o[o.is_primary_data.astype(str) == "True"]
    n = o.groupby(["dataset_id", "donor_id"]).disease.nunique()
    return set(n[n == 1].index)


def match_draw(pool, target, rng, fb):
    """Draw donors from pool (DataFrame with sex, bin) to reproduce target counts by (sex, bin); fallbacks counted."""
    chosen, avail = [], pool.copy()
    for (sex, b), k in target.items():
        cand = avail[(avail.sex == sex) & (avail.bin == b)]
        take = list(rng.choice(cand.index, size=min(k, len(cand)), replace=False)) if len(cand) else []
        avail = avail.drop(take); chosen += take
        short = k - len(take)
        if short and b != "unknown":
            order = sorted([x for x in BINS[:4] if x != b], key=lambda x: (abs(BINS.index(x) - BINS.index(b)), BINS.index(x)))
            for nb in order:
                cand = avail[(avail.sex == sex) & (avail.bin == nb)]
                t2 = list(rng.choice(cand.index, size=min(short, len(cand)), replace=False)) if len(cand) else []
                avail = avail.drop(t2); chosen += t2; fb["nearest_bin"] += len(t2); short -= len(t2)
                if not short:
                    break
        if short:
            cand = avail[avail.sex == sex]
            t2 = list(rng.choice(cand.index, size=min(short, len(cand)), replace=False)) if len(cand) else []
            avail = avail.drop(t2); chosen += t2; fb["same_sex_any_bin"] += len(t2); short -= len(t2)
        if short:
            t2 = list(rng.choice(avail.index, size=short, replace=False))
            avail = avail.drop(t2); chosen += t2; fb["any_donor"] += len(t2)
    return chosen


def write_job(jd, X, donors, draws, gene_ids):
    jd.mkdir(parents=True, exist_ok=True)
    nz = np.asarray(X.sum(0)).ravel() > 0
    Xd = X[:, nz].toarray().astype(np.float32)          # donors x genes = column-major genes x donors
    Xd.tofile(jd / "counts.f32")
    pd.DataFrame({"ngenes": [int(nz.sum())], "ndonors": [Xd.shape[0]]}).to_csv(jd / "meta.csv", index=False)
    donors[["donor_id", "sex", "bin", "n_cells", "assay", "suspension_type"]].to_csv(jd / "donors.csv", index=False)
    pd.DataFrame(draws).to_csv(jd / "draws.csv", index=False)
    np.savetxt(jd / "genes.txt", gene_ids[nz], fmt="%d")


def build():
    elig, amap = eligible_donors(), pd.read_csv(T / "age_map.csv").set_index("development_stage").bin
    prim = pd.read_csv(META / "contrasts_primary.csv").assign(role="primary")
    rep = pd.read_csv(META / "contrasts_replication.csv").assign(role="replication")
    allc = pd.concat([prim, rep.drop(columns="collection_id")]).drop_duplicates(["dataset_id", "tissue_general", "cell_type", "disease"])
    allc = allc.sort_values(["dataset_id", "tissue_general", "cell_type", "disease"]).reset_index(drop=True)
    allc["contrast"] = [f"c{i:04d}" for i in range(len(allc))]
    allc["primary"] = allc.set_index(["dataset_id", "tissue_general", "cell_type", "disease"]).index.isin(
        prim.set_index(["dataset_id", "tissue_general", "cell_type", "disease"]).index)
    fbrows, idx = [], []
    for ds, cg in allc.groupby("dataset_id"):
        X = sp.load_npz(PB / f"{ds}.npz").tocsr()
        g = pd.read_parquet(PB / f"{ds}.groups.parquet")
        g["bin"] = g.development_stage.map(amap).fillna("unknown")
        g["eligible"] = [(ds, d) in elig for d in g.donor_id]
        gene_ids = np.arange(X.shape[1])
        for c in cg.itertuples():
            sel = g[(g.tissue_general == c.tissue_general) & (g.cell_type == c.cell_type) & g.eligible & (g.n_cells >= MIN_CELLS)]
            D, H = sel[sel.disease == c.disease], sel[sel.disease == "normal"]
            donors = pd.concat([D, H]).reset_index()             # 'index' = row in X
            nD, nH = len(D), len(H)
            pos = {r: i for i, r in enumerate(donors["index"])}
            Di, Hi = [pos[r] for r in D.index], [pos[r] for r in H.index]
            draws = [{"id": 0, "kind": "full", "a": ";".join(map(str, Di)), "b": ";".join(map(str, Hi)), "save": 1}]
            fb = {"nearest_bin": 0, "same_sex_any_bin": 0, "any_donor": 0}
            m = min(nD, nH // 2)
            if c.primary and m >= 8:
                ci = int(c.contrast[1:])
                comp = []
                for r in range(R_REAL):
                    rng = np.random.default_rng([SEED, ci, r])
                    a, b = rng.choice(Di, m, replace=False), rng.choice(Hi, m, replace=False)
                    draws.append({"id": 1 + r, "kind": "real", "a": ";".join(map(str, a)), "b": ";".join(map(str, b)), "save": 0})
                    comp.append((donors.loc[a].groupby(["sex", "bin"]).size(), donors.loc[b].groupby(["sex", "bin"]).size()))
                Hpool = donors.loc[Hi, ["sex", "bin"]]
                for bdraw in range(B_NULL):
                    rng = np.random.default_rng([SEED, ci, 1000 + bdraw])
                    ta, tb = comp[bdraw % R_REAL]
                    P = match_draw(Hpool, ta, rng, fb)
                    Q = match_draw(Hpool.drop(P), tb, rng, fb)
                    draws.append({"id": 1 + R_REAL + bdraw, "kind": "null", "a": ";".join(map(str, P)), "b": ";".join(map(str, Q)),
                                  "save": int(bdraw < 20)})        # t vectors kept for the null-replication baseline
            write_job(JOBS / c.contrast, X[donors["index"].to_numpy()], donors, draws, gene_ids)
            fbrows.append({"contrast": c.contrast, "m": m, **fb, "null_donor_slots": 2 * m * B_NULL if c.primary and m >= 8 else 0})
            idx.append({**c._asdict(), "n_disease_elig": nD, "n_normal_elig": nH, "m": m,
                        "median_cells": float(sel.n_cells.median()) if len(sel) else np.nan})
        print(ds, len(cg), "contrasts", flush=True)
    pd.DataFrame(idx).drop(columns="Index").to_csv(META / "contrast_index.csv", index=False)
    pd.DataFrame(fbrows).to_csv(T / "draw_fallbacks.csv", index=False)


def control():
    """G3 positive control: male vs female normal donors, largest primary dataset's largest normal cell type."""
    ci = pd.read_csv(META / "contrast_index.csv")
    p = ci[ci.primary].sort_values("n_normal_elig", ascending=False).iloc[0]
    amap = pd.read_csv(T / "age_map.csv").set_index("development_stage").bin
    X = sp.load_npz(PB / f"{p.dataset_id}.npz").tocsr()
    g = pd.read_parquet(PB / f"{p.dataset_id}.groups.parquet")
    g["bin"] = g.development_stage.map(amap).fillna("unknown")
    elig = eligible_donors()
    sel = g[(g.tissue_general == p.tissue_general) & (g.cell_type == p.cell_type) & (g.disease == "normal") & (g.n_cells >= MIN_CELLS)
            & [(p.dataset_id, d) in elig for d in g.donor_id]]
    donors = sel.reset_index()
    M, F = donors.index[donors.sex == "male"].tolist(), donors.index[donors.sex == "female"].tolist()
    m = min(len(M), len(F), len(donors) // 2)
    rng = np.random.default_rng([SEED, 99999])
    draws = []
    for r in range(R_REAL):
        draws.append({"id": r, "kind": "real", "a": ";".join(map(str, rng.choice(M, m, replace=False))), "b": ";".join(map(str, rng.choice(F, m, replace=False)))})
    for b in range(200):
        perm = rng.permutation(donors.index)
        draws.append({"id": R_REAL + b, "kind": "null", "a": ";".join(map(str, perm[:m])), "b": ";".join(map(str, perm[m:2 * m]))})
    d2 = donors.assign(sex="any")          # sex cannot be a covariate when it is the contrast
    write_job(JOBS / "control_sex", X[donors["index"].to_numpy()], d2, draws, np.arange(X.shape[1]))
    (JOBS / "control_sex" / "info.json").write_text(json.dumps({"dataset_id": p.dataset_id, "tissue_general": p.tissue_general,
                                                                 "cell_type": p.cell_type, "m": int(m), "male": len(M), "female": len(F)}))


def run(workers):
    jobs = sorted(p for p in JOBS.iterdir() if p.is_dir() and not (p / "stats.csv").exists())
    size = {p: int(pd.read_csv(p / "draws.csv").shape[0]) for p in jobs}
    lists = [[] for _ in range(workers)]
    load = [0] * workers
    for p in sorted(jobs, key=lambda p: -size[p]):
        k = int(np.argmin(load)); lists[k].append(p); load[k] += size[p]
    def go(k):
        lf = JOBS / f"_list{k}.txt"
        lf.write_text("\n".join(f"/jobs/{p.name}" for p in lists[k]) + "\n")
        return subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "1000:1000", "-e", "HOME=/tmp",
                               "-v", f"{JOBS}:/jobs", "-v", f"{RUN / 'code'}:/code:ro", "sc-negctl-de:1",
                               "Rscript", "/code/de.R", f"/jobs/_list{k}.txt"], capture_output=True, text=True).returncode
    with ThreadPoolExecutor(workers) as ex:
        print(list(ex.map(go, [k for k in range(workers) if lists[k]])), flush=True)


if __name__ == "__main__":
    {"agemap": agemap, "build": build, "control": control}.get(sys.argv[1], lambda: run(int(sys.argv[2])))()
