"""H1, H2 and secondaries (plan sections 0 and 5) from the DE engine's outputs; G2 coverage for every stage.

  analyse.py   -> results/tables/primary.json, contrasts.csv (per-contrast exceedance), pairs.csv, coverage.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

RUN = Path(__file__).resolve().parents[1]
META, PB, JOBS, T = RUN / "data" / "meta", RUN / "data" / "pb", RUN / "data" / "jobs", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, BOOT, B_NULL, R_REAL = 20261027, 2000, 500, 25
STATS = ["pi1", "n_de", "mean_abs_lfc_top100"]


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def coverage_pb():
    cov = Coverage("pseudobulk", T / "coverage.json")
    o = pd.read_parquet(META / "obs_counts.parquet")
    meta_cells = o[o.is_primary_data.astype(str) == "True"].groupby("dataset_id").cells.sum()
    for ds in pd.read_csv(META / "needed_datasets.csv").dataset_id:
        cov.attempt(ds)
        f = PB / f"{ds}.cov.json"
        if not f.exists():
            cov.drop(ds, "no pseudobulk"); continue
        c = json.loads(f.read_text())
        prim = c["cells_h5ad"]          # all cells in the H5AD; the kept count is primary cells of needed groups
        if c["nonint_share_sampled"] > 0:
            cov.drop(ds, "non-integer counts"); continue
        if c["genes_not_in_census_var"] and c["counts_dropped_not_in_census"] > 0:
            cov.fallback(ds, "genes outside Census var dropped")
        else:
            cov.ok(ds)
        if prim < meta_cells.get(ds, 0):
            raise SystemExit(f"{ds}: H5AD has fewer cells than the Census metadata")
    cov.save()


def coverage_donors(ci):
    """Donor-groups considered for each contrast (its disease or normal, its tissue and cell type) and why any were left out."""
    sys.path.insert(0, str(RUN / "code"))
    from draws import eligible_donors, MIN_CELLS
    elig = eligible_donors()
    cov = Coverage("contrast_donors", T / "coverage.json")
    ok, drops = 0, {"more than one disease label in the dataset": 0, f"fewer than {MIN_CELLS} cells": 0}
    for ds, cg in ci.groupby("dataset_id"):
        g = pd.read_parquet(PB / f"{ds}.groups.parquet")
        for c in cg.itertuples():
            sel = g[(g.tissue_general == c.tissue_general) & (g.cell_type == c.cell_type) & g.disease.isin([c.disease, "normal"])]
            e = np.array([(ds, d) in elig for d in sel.donor_id])
            enough = (sel.n_cells >= MIN_CELLS).to_numpy()
            ok += int((e & enough).sum())
            drops["more than one disease label in the dataset"] += int((~e).sum())
            drops[f"fewer than {MIN_CELLS} cells"] += int((e & ~enough).sum())
    cov.add_counts(ok=ok, drops=drops)
    cov.save()


def stats_of(c):
    f = JOBS / c / "stats.csv"
    return pd.read_csv(f, keep_default_na=False, na_values=["NA"]) if f.exists() else None   # "null" is a draw kind, not NA


def ot_lookup():
    """disease label -> Series(Census var row -> Open Targets direct overall score); absent genes score 0."""
    var = pd.read_parquet(META / "var.parquet")
    row = pd.Series(np.arange(len(var)), index=var.feature_id.astype(str))
    ot = pd.read_parquet(META / "ot_assoc.parquet")
    ot = ot[ot.ensembl_id.isin(row.index)]
    # several Open Targets rows can land on the same Census var row, so keep the strongest score per row
    return {d: pd.Series(g.score.to_numpy(), index=row[g.ensembl_id].to_numpy()).groupby(level=0).max()
            for d, g in ot.groupby("disease")}


def ot_stat(top100, genes, score):
    rows = genes[np.array([int(x) for x in str(top100).split(";") if x != ""], int)]
    return float(score.reindex(rows).fillna(0).mean())


def h1(ci):
    OT = ot_lookup()
    cov_c = Coverage("primary_contrasts", T / "coverage.json")
    cov_f = Coverage("de_fits", T / "coverage.json")
    rows = []
    for c in ci[ci.primary].itertuples():
        cov_c.attempt(c.contrast)
        st = stats_of(c.contrast)
        if st is None:
            cov_c.drop(c.contrast, "no DE output"); continue
        fails = st[~st.ok.astype(bool)]
        cov_f.add_counts(ok=int(st.ok.astype(bool).sum()), drops={f"{k} fit failed": int((fails.kind == k).sum()) for k in ("full", "real", "null")})
        real, null = st[(st.kind == "real") & st.ok.astype(bool)], st[(st.kind == "null") & st.ok.astype(bool)]
        if B_NULL - len(null) > 0.10 * B_NULL or len(real) == 0:
            cov_c.drop(c.contrast, "not evaluable: >10% null fits failed or no real fit"); continue
        cov_c.ok(c.contrast)
        r = {"contrast": c.contrast, "dataset_id": c.dataset_id, "tissue_general": c.tissue_general, "cell_type": c.cell_type,
             "disease": c.disease, "n_disease": c.n_disease_elig, "n_normal": c.n_normal_elig, "m": c.m,
             "median_cells": c.median_cells, "real_ok": len(real), "null_ok": len(null)}
        for s in STATS:
            tr = float(np.median(real[s]))
            r[f"{s}_real"] = tr
            r[f"{s}_null_median"] = float(np.median(null[s]))
            r[f"{s}_null_q95"] = float(np.percentile(null[s], 95))
            r[f"{s}_null_iqr"] = float(np.subtract(*np.percentile(null[s], [75, 25])))
            r[f"{s}_p"] = (1 + int((null[s] >= tr).sum())) / (len(null) + 1)
        if c.disease in OT:                     # enrichment secondary: single-ID diseases only
            genes = np.loadtxt(JOBS / c.contrast / "genes.txt", dtype=int, ndmin=1)
            er = [ot_stat(x, genes, OT[c.disease]) for x in real.top100]
            en = np.array([ot_stat(x, genes, OT[c.disease]) for x in null.top100])
            r["ot_real"], r["ot_null_median"] = float(np.median(er)), float(np.median(en))
            r["ot_p"] = (1 + int((en >= np.median(er)).sum())) / (len(en) + 1)
        full = st[(st.kind == "full") & st.ok.astype(bool)]
        r["pi1_full"] = float(full.pi1.iloc[0]) if len(full) else np.nan
        r["n_de_full"] = float(full.n_de.iloc[0]) if len(full) else np.nan
        d = pd.read_csv(JOBS / c.contrast / "donors.csv")
        D, H = d.iloc[:c.n_disease_elig], d.iloc[c.n_disease_elig:]
        r["sex_imbalance"] = abs((D.sex == "male").mean() - (H.sex == "male").mean())
        pa, pb = D.bin.value_counts(normalize=True), H.bin.value_counts(normalize=True)
        r["age_imbalance_tv"] = 0.5 * float(pa.sub(pb, fill_value=0).abs().sum())
        r["assay"] = d.assay.mode().iloc[0]
        r["suspension_type"] = d.suspension_type.mode().iloc[0]
        rows.append(r)
    cov_c.save(); cov_f.save()
    df = pd.DataFrame(rows)
    for s in STATS:
        df[f"{s}_q"] = bh(df[f"{s}_p"])
    df["indistinguishable"] = df.pi1_q >= 0.05
    df["indistinguishable_nde"] = df.n_de_q >= 0.05     # D2: the statistic the G3 power check shows is sensitive
    e = df.dropna(subset=["ot_p"]).copy()
    e["ot_q"] = bh(e.ot_p)
    df = df.merge(e[["contrast", "ot_q"]], on="contrast", how="left")
    rng = np.random.default_rng(SEED)
    dss = df.dataset_id.unique()
    by = {d: df.indistinguishable[df.dataset_id == d].to_numpy() for d in dss}
    bs = []
    for _ in range(BOOT):
        pick = rng.choice(dss, len(dss), replace=True)
        v = np.concatenate([by[d] for d in pick])
        bs.append(v.mean())
    S1 = float(df.indistinguishable.mean())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    verdict = "Supported" if lo > 0.5 else "Refuted" if hi < 0.5 else "Inconclusive"
    per_dis = df.groupby("disease").indistinguishable.mean()

    def share_and_verdict(col):
        by2 = {d: df[col][df.dataset_id == d].to_numpy() for d in dss}
        r2 = np.random.default_rng(SEED + 5)
        b2 = [np.concatenate([by2[d] for d in r2.choice(dss, len(dss), replace=True)]).mean() for _ in range(BOOT)]
        l2, h2 = np.percentile(b2, [2.5, 97.5])
        return {"S1": round(float(df[col].mean()), 4), "ci95": [round(float(l2), 4), round(float(h2), 4)],
                "verdict": "Supported" if l2 > 0.5 else "Refuted" if h2 < 0.5 else "Inconclusive",
                "S1_equal_weight_per_disease": round(float(df.groupby("disease")[col].mean().mean()), 4)}
    out = {"contrasts_evaluable": int(len(df)), "datasets": int(len(dss)), "diseases": int(df.disease.nunique()),
           "S1": round(S1, 4), "ci95": [round(float(lo), 4), round(float(hi), 4)], "verdict": verdict,
           "by_n_de_power_selected": share_and_verdict("indistinguishable_nde"),   # D2: 87% power vs pi1's 8%
           "S1_equal_weight_per_disease": round(float(per_dis.mean()), 4),
           "share_indistinguishable_by_stat": {s: round(float((df[f"{s}_q"] >= 0.05).mean()), 4) for s in STATS},
           "share_real_above_null_q95": {s: round(float((df[f"{s}_real"] > df[f"{s}_null_q95"]).mean()), 4) for s in STATS},
           "median_pi1_real": round(float(df.pi1_real.median()), 4), "median_pi1_null_median": round(float(df.pi1_null_median.median()), 4),
           "median_n_de_full": float(df.n_de_full.median()), "share_full_with_any_de": round(float((df.n_de_full > 0).mean()), 4),
           "ot_enrichment": {"contrasts": int(len(e)), "share_enriched_q05": round(float((e.ot_q < 0.05).mean()), 4) if len(e) else None,
                             "release": json.loads((META / "ot_release.json").read_text())["meta"]}}
    # exploratory attribution
    df["excess"] = (df.pi1_real - df.pi1_null_median) / df.pi1_null_iqr.replace(0, np.nan)
    out["attribution"] = attribution(df)
    df.to_csv(T / "contrasts.csv", index=False)
    return out, df


def ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0][1:]


def attribution(df):
    d = df.dropna(subset=["excess"]).copy()
    feats = {"log2_m": np.log2(d.m), "log2_median_cells": np.log2(d.median_cells), "sex_imbalance": d.sex_imbalance,
             "age_imbalance_tv": d.age_imbalance_tv, "nucleus": (d.suspension_type == "nucleus").astype(float)}
    X = pd.DataFrame(feats)
    X = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    y = d.excess.clip(-50, 50).to_numpy()
    beta = ols(X.to_numpy(), y)
    rng = np.random.default_rng(SEED + 1)
    groups = d.dataset_id.to_numpy()
    ug = np.unique(groups)
    bs = []
    for _ in range(BOOT):
        pick = rng.choice(ug, len(ug), replace=True)
        ii = np.concatenate([np.flatnonzero(groups == g) for g in pick])
        bs.append(ols(X.to_numpy()[ii], y[ii]))
    bs = np.array(bs)
    return {k: {"beta": round(float(b), 3), "ci95": [round(float(x), 3) for x in np.percentile(bs[:, j], [2.5, 97.5])]}
            for j, (k, b) in enumerate(zip(X.columns, beta))} | {"n": int(len(d)), "note": "exploratory; excess clipped to +/-50 null IQRs"}


def tvec(c, draw):
    f = JOBS / c / f"t_{draw}.f32"
    if not f.exists():
        return None
    t = np.fromfile(f, np.float32)
    kept = np.loadtxt(JOBS / c / f"kept_{draw}.txt", dtype=int, ndmin=1)
    genes = np.loadtxt(JOBS / c / "genes.txt", dtype=int, ndmin=1)
    return pd.Series(t, index=genes[kept])


def h2(ci):
    col = pd.read_parquet(META / "datasets.parquet").set_index("dataset_id").collection_id
    rep = pd.read_csv(META / "contrasts_replication.csv")
    key = ["dataset_id", "tissue_general", "cell_type", "disease"]
    rc = ci.merge(rep[key], on=key)
    rc["collection_id"] = rc.dataset_id.map(col)
    cov = Coverage("replication_pairs", T / "coverage.json")
    rows = []
    for (dis, ti, ct), g in rc.groupby(["disease", "tissue_general", "cell_type"]):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g.loc[i], g.loc[j]
                if a.collection_id == b.collection_id:
                    continue
                u = (a.contrast, b.contrast)
                cov.attempt(u)
                ta, tb = tvec(a.contrast, 0), tvec(b.contrast, 0)
                if ta is None or tb is None:
                    cov.drop(u, "full-size fit missing"); continue
                common = ta.index.intersection(tb.index)
                if len(common) < 500:
                    cov.drop(u, "fewer than 500 shared genes"); continue
                cov.ok(u)
                rho = float(spearmanr(ta[common], tb[common]).statistic)
                da, db = (pd.read_csv(JOBS / x.contrast / "donors.csv") for x in (a, b))
                def imb(d, n):
                    return abs((d.iloc[:n].sex == "male").mean() - (d.iloc[n:].sex == "male").mean())
                nulls = []
                if a.primary and b.primary:
                    for k in range(20):
                        na, nb = tvec(a.contrast, 1 + R_REAL + k), tvec(b.contrast, 1 + R_REAL + k)
                        if na is not None and nb is not None:
                            cc = na.index.intersection(nb.index)
                            nulls.append(float(spearmanr(na[cc], nb[cc]).statistic))
                rows.append({"disease": dis, "tissue_general": ti, "cell_type": ct, "contrast_a": a.contrast, "contrast_b": b.contrast,
                             "rho": rho, "genes": len(common),
                             "d": np.log2(min(a.n_disease_elig, a.n_normal_elig, b.n_disease_elig, b.n_normal_elig)),
                             "c": np.log2(min(a.median_cells, b.median_cells)),
                             "sex_imb": max(imb(da, a.n_disease_elig), imb(db, b.n_disease_elig)),
                             "same_assay": float(da.assay.mode().iloc[0] == db.assay.mode().iloc[0]),
                             "null_rho_median": float(np.median(nulls)) if nulls else np.nan, "null_draws": len(nulls)})
    cov.save()
    p = pd.DataFrame(rows)
    p.to_csv(T / "pairs.csv", index=False)
    Z = p[["d", "c", "sex_imb"]]
    Z = (Z - Z.mean()) / Z.std(ddof=0)
    X = np.column_stack([Z.to_numpy(), p.same_assay.to_numpy()])
    y = p.rho.to_numpy()
    beta = ols(X, y)

    def boot(clusters, seed):
        rng = np.random.default_rng(seed)
        ug = np.unique(clusters)
        idx = {g: np.flatnonzero(clusters == g) for g in ug}
        out = []
        for _ in range(BOOT):
            ii = np.concatenate([idx[g] for g in rng.choice(ug, len(ug), replace=True)])
            out.append(ols(X[ii], y[ii]))
        return np.array(out)
    grp = (p.disease + "|" + p.tissue_general + "|" + p.cell_type).to_numpy()
    res = {}
    for name, cl, sd in (("group", grp, SEED + 2), ("disease", p.disease.to_numpy(), SEED + 3)):
        bs = boot(cl, sd)
        ci_ = lambda j: [round(float(x), 4) for x in np.percentile(bs[:, j], [2.5, 97.5])]
        diff = [round(float(x), 4) for x in np.percentile(bs[:, 0] - bs[:, 1], [2.5, 97.5])]
        res[name] = {"beta_d_ci": ci_(0), "beta_c_ci": ci_(1), "beta_sex_ci": ci_(2), "beta_same_assay_ci": ci_(3), "d_minus_c_ci": diff,
                     "clusters": int(len(np.unique(cl)))}
    g = res["group"]
    verdict = ("Supported" if g["beta_d_ci"][0] > 0 and g["d_minus_c_ci"][0] > 0
               else "Refuted" if (beta[1] >= beta[0] and g["d_minus_c_ci"][1] < 0) or g["beta_d_ci"][1] < 0 else "Inconclusive")
    nb = p.dropna(subset=["null_rho_median"])
    return {"pairs": int(len(p)), "groups": int(len(np.unique(grp))), "diseases": int(p.disease.nunique()),
            "median_rho": round(float(p.rho.median()), 4), "beta": dict(zip(["d", "c", "sex_imb", "same_assay"], [round(float(b), 4) for b in beta])),
            "bootstrap": res, "verdict": verdict,
            "null_baseline": {"pairs": int(len(nb)), "median_real_rho": round(float(nb.rho.median()), 4) if len(nb) else None,
                              "median_null_rho": round(float(nb.null_rho_median.median()), 4) if len(nb) else None}}


def main():
    T.mkdir(parents=True, exist_ok=True)
    coverage_pb()
    ci = pd.read_csv(META / "contrast_index.csv")
    coverage_donors(ci)
    out = {}
    out["H1"], _ = h1(ci)
    out["H2"] = h2(ci)
    fb = pd.read_csv(T / "draw_fallbacks.csv")
    slots = fb.null_donor_slots.sum()
    out["matching_fallbacks"] = {k: int(fb[k].sum()) for k in ("nearest_bin", "same_sex_any_bin", "any_donor")} | {"null_donor_slots": int(slots)}
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
