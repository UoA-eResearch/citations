"""Features (plan section 3) for every cohort article, from data/cohort_raw and the pass-1 lookups.

Every as-of comparison uses retraction year <= publication year - 1 ("before 1 January of the publication year").
Writes data/features/<n>.parquet; concatenated by code/model.py.
"""
import glob
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
LK, RAW, OUT = RUN / "data" / "lookup", RUN / "data" / "cohort_raw", RUN / "data" / "features"
L = {}


def init():
    for k in ("w_wid", "w_year", "w_src", "w_ret", "a_id", "a_first", "ar_a", "ar_r"):
        L[k] = np.load(LK / f"{k}.npy", mmap_mode="r")
    L["ar_key"] = np.asarray(L["ar_a"], dtype=np.int64) * 4096 + np.asarray(L["ar_r"], dtype=np.int64)
    r = pd.read_parquet(LK / "rates.parquet")
    L["rates"] = {(k, Y): g.set_index("e")[["rate", "n1", "n3"]] for (k, Y), g in r.groupby(["k", "Y"])}


def lookup(sorted_ids, ids):
    i = np.searchsorted(sorted_ids, ids)
    i = np.minimum(i, len(sorted_ids) - 1)
    return i, np.asarray(sorted_ids[i]) == ids


def rate(kind, ents, years, col="rate"):
    out = np.zeros(len(ents))
    for Y in np.unique(years):
        t = L["rates"].get((kind, int(Y)))
        if t is None:
            continue
        m = years == Y
        out[m] = t[col].reindex(ents[m]).fillna(0).to_numpy()
    return out


def seg_sum(vals, seg, n):
    return np.bincount(seg, weights=vals, minlength=n)


def work(path):
    out = OUT / (Path(path).stem + ".parquet")
    if out.exists():
        return 0
    z = np.load(path)
    if "empty" in z.files:
        return 0
    n = len(z["wid"])
    Y = z["year"].astype(np.int64)
    f = pd.DataFrame({"wid": z["wid"], "year": Y, "src": z["src"], "host": z["host"], "field": z["field"],
                      "stype": z["stype"], "oa": z["oa"].astype(np.int8), "nauth": z["nauth"]})
    # label from the lookup (the same DOI match as pass 1)
    i, ok = lookup(L["w_wid"], z["wid"])
    f["ret"] = np.where(ok, np.asarray(L["w_ret"])[i], 0)
    # block A
    f["src_missing"] = (f.src == 0).astype(np.int8)
    f["src_rate"] = rate("S", z["src"], Y)
    f["host_rate"] = rate("H", z["host"], Y)
    f["src_growth"] = (rate("S", z["src"], Y, "n1") + 1) / (rate("S", z["src"], Y, "n3") + 1)
    # block B: authors
    aoff = z["au_off"]; acnt = np.diff(aoff); aseg = np.repeat(np.arange(n), acnt)
    aid = z["au_id"]; ay = Y[aseg]
    lo = np.searchsorted(L["ar_key"], aid * 4096, "left")
    prior = np.searchsorted(L["ar_key"], aid * 4096 + ay, "left") - lo       # retractions with year < Y
    prior[aid == 0] = 0
    f["auth_prior_ret_n"] = seg_sum((prior > 0).astype(float), aseg, n)
    mx = pd.Series(prior).groupby(aseg).max() if len(prior) else pd.Series(dtype=float)
    f["auth_prior_ret_max"] = mx.reindex(range(n)).fillna(0).to_numpy()
    j, okA = lookup(L["a_id"], aid)
    first = np.where(okA & (aid > 0), np.asarray(L["a_first"])[j], 9999)
    newc = ((first >= ay - 2) & (first < 9999)).astype(float)
    known = ((aid > 0) & okA).astype(float)
    f["newcomer_share"] = seg_sum(newc, aseg, n) / np.maximum(seg_sum(known, aseg, n), 1)
    # institutions and countries (per authorship lists)
    ioff = z["in_off"]; iseg_a = np.repeat(np.arange(len(acnt) and len(aid)), np.diff(ioff))
    iw = aseg[iseg_a] if len(iseg_a) else np.array([], dtype=np.int64)
    inst = pd.DataFrame({"w": iw, "e": z["in_id"]})
    inst = inst[inst.e > 0].drop_duplicates()
    f["n_inst"] = inst.groupby("w").size().reindex(range(n)).fillna(0).to_numpy()
    inst["r"] = rate("I", inst.e.to_numpy(), Y[inst.w.to_numpy()])
    f["inst_max_rate"] = inst.groupby("w").r.max().reindex(range(n)).fillna(0).to_numpy()
    coff = z["ct_off"]; cseg_a = np.repeat(np.arange(len(aid)), np.diff(coff))
    ct = pd.DataFrame({"w": aseg[cseg_a] if len(cseg_a) else np.array([], dtype=np.int64), "c": z["ct"],
                       "first": z["au_first"][cseg_a] if len(cseg_a) else np.array([], dtype=bool)})
    f["n_countries"] = ct.drop_duplicates(["w", "c"]).groupby("w").size().reindex(range(n)).fillna(0).to_numpy()
    f["country1"] = ct[ct["first"]].groupby("w").c.first().reindex(range(n)).fillna("").to_numpy()
    # block C: references
    roff = z["rf_off"]; rcnt = np.diff(roff); rseg = np.repeat(np.arange(n), rcnt)
    k, okR = lookup(L["w_wid"], z["rf"])
    ry = np.where(okR, np.asarray(L["w_year"])[k], 0).astype(np.int64)
    rs = np.where(okR, np.asarray(L["w_src"])[k], 0)
    rr = np.where(okR, np.asarray(L["w_ret"])[k], 0).astype(np.int64)
    ny = seg_sum(okR.astype(float), rseg, n)
    f["n_refs"] = rcnt
    f["ref_unresolved_share"] = np.where(rcnt > 0, 1 - ny / np.maximum(rcnt, 1), np.nan)
    f["ref_retracted_share"] = np.where(ny > 0, seg_sum(((rr > 0) & (rr <= Y[rseg] - 1)).astype(float), rseg, n)
                                        / np.maximum(ny, 1), np.nan)
    f["ref_same_source_share"] = np.where(ny > 0, seg_sum(((rs == z["src"][rseg]) & (rs > 0)).astype(float), rseg, n)
                                          / np.maximum(ny, 1), np.nan)
    v = okR & (ry > 0)
    ref = pd.DataFrame({"w": rseg[v], "y": ry[v]})
    g = ref.groupby("w").y
    f["ref_year_sd"] = g.std().reindex(range(n)).to_numpy()
    f["ref_recency_gap"] = Y - g.median().reindex(range(n)).to_numpy()
    f.to_parquet(out, index=False)
    return n


def main(workers=8):
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(RAW / "*.npz")))
    tot = 0
    with ProcessPoolExecutor(workers, initializer=init) as ex:
        for i, k in enumerate(ex.map(work, files, chunksize=8)):
            tot += k
            if (i + 1) % 200 == 0:
                print(i + 1, "files", tot, "articles", flush=True)
    print("features done", tot)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
