"""Provenance audit (plan sections 0 H2, 3 and 5) and the RF species population (section 4).

Training presences: SAGE's 1 km training targets (cells x species CSR). A presence is provenance-only if every snapshot
record of that species in that cell comes from core-flagged datasets (n_core > 0, no broad or other records).
Source cells: SAGE test cells (test_indices.npy) holding at least one plot from a GIVD source database with a
core-flagged GBIF dataset. Test presences: species present in a source cell (eval targets) and inside its native-range
mask (as SAGE evaluates).

-> data/work/prov_only.parquet (sp, cell) ; results/tables/audit.json ; results/tables/population.csv
"""
import json
from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401  (SAGE's HDF5 compression filters)
import numpy as np
import pandas as pd
from pyproj import Transformer

RUN = Path(__file__).resolve().parents[1]
B, W, T = Path("/mnt/sage/bench"), RUN / "data" / "work", RUN / "results" / "tables"
SEED = 20261025
TR = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)


def csr(path):
    with h5py.File(path) as h:
        g = h["csr"]
        return g["indptr"][:], g["indices"][:]


def train_cells():
    L = h5py.File(B / "predictors" / "train_location_1km.h5")["predictor_data"][:]
    x, y = TR.transform(L[:, 0].astype(float), L[:, 1].astype(float))
    gx = np.round(x / 1000 - 0.5).astype(np.int32)                         # stored points are cell centres
    gy = np.round(y / 1000 - 0.5).astype(np.int32)
    return pd.DataFrame({"cell": np.arange(len(L), dtype=np.int32), "gx": gx, "gy": gy})


def eval_cells():
    E = h5py.File(B / "predictors" / "eval_location.h5")["predictor_data"][:]
    x, y = TR.transform(E[:, 0].astype(float), E[:, 1].astype(float))
    return pd.DataFrame({"ecell": np.arange(len(E), dtype=np.int32), "gx": np.floor_divide(x, 1000).astype(np.int32),
                         "gy": np.floor_divide(y, 1000).astype(np.int32)})


def boot_share(num, den, groups, rng, b=2000):
    """Share sum(num)/sum(den) with a bootstrap over groups (cells)."""
    d = pd.DataFrame({"g": groups, "n": num, "d": den}).groupby("g").sum()
    n, dd = d.n.to_numpy(), d.d.to_numpy()
    est = n.sum() / dd.sum()
    bs = []
    for _ in range(b):
        k = rng.integers(len(d), size=len(d))
        bs.append(n[k].sum() / dd[k].sum())
    return float(est), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def main():
    import duckdb
    rng = np.random.default_rng(SEED)
    con = duckdb.connect()
    con.execute("SET threads TO 24; SET memory_limit = '60GB'")
    # training presences
    indptr, idx = csr(B / "targets" / "train_targets_1km.h5")
    pres = pd.DataFrame({"cell": np.repeat(np.arange(len(indptr) - 1, dtype=np.int32), np.diff(indptr)), "sp": idx.astype(np.int16)})
    tc = train_cells()
    con.register("pres", pres); con.register("tc", tc)
    sup = str(W / "support.parquet")
    j = con.execute(f"""
        SELECT p.sp, p.cell, coalesce(s.n_core, 0) AS n_core, coalesce(s.n_broad, 0) AS n_broad, coalesce(s.n_other, 0) AS n_other
        FROM pres p JOIN tc USING (cell) LEFT JOIN read_parquet('{sup}') s ON s.sp = p.sp AND s.gx = tc.gx AND s.gy = tc.gy
    """).df()
    j["prov_only"] = (j.n_core > 0) & (j.n_broad == 0) & (j.n_other == 0)
    j["any_core"] = j.n_core > 0
    j["matched"] = (j.n_core + j.n_broad + j.n_other) > 0
    j.loc[j.prov_only, ["sp", "cell"]].to_parquet(W / "prov_only.parquet", index=False)
    cc = pd.read_parquet(W / "cell_country.parquet")
    jc = j.merge(tc, on="cell").merge(cc, on=["gx", "gy"], how="left")
    out = {"train_presences": int(len(j)), "matched_to_snapshot": round(float(j.matched.mean()), 4),
           "with_core_record": int(j.any_core.sum()), "provenance_only": int(j.prov_only.sum()),
           "provenance_only_share": round(float(j.prov_only.mean()), 5),
           "provenance_only_by_country": jc[jc.prov_only].country.value_counts().head(15).to_dict()}
    del jc
    # evaluation: source cells and test presences
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", low_memory=False)
    flags = pd.read_csv(T / "provenance_flags.csv")
    core_src = set(flags[flags.flag == "core"].givd_source)
    broad_src = set(flags[flags.flag == "broad"].givd_source)
    test = set(np.load(B / "test_indices.npy").tolist())
    src_cells = set(meta[meta.GIVD_ID.isin(core_src)].cell_row) & test
    ec = eval_cells()
    eptr, eidx = csr(B / "targets" / "eval_targets.h5")
    with h5py.File(B / "range_masks_1km" / "eval_range_mask.h5") as h:
        cl, si = h["cumulative_lengths"][:], h["species_index"][:]
    rows = []
    for c in sorted(src_cells):
        inrange = set(si[cl[c]:cl[c + 1]].tolist())
        for s in eidx[eptr[c]:eptr[c + 1]]:
            if int(s) in inrange:
                rows.append((c, int(s)))
    tp = pd.DataFrame(rows, columns=["ecell", "sp"]).merge(ec, on="ecell")
    con.register("tp", tp)
    tp = con.execute(f"""SELECT tp.*, coalesce(s.n_core, 0) AS n_core, coalesce(s.n_broad, 0) AS n_broad
                         FROM tp LEFT JOIN read_parquet('{sup}') s ON s.sp = tp.sp AND s.gx = tp.gx AND s.gy = tp.gy""").df()
    tp["core"] = tp.n_core > 0
    tp["core_or_broad"] = (tp.n_core + tp.n_broad) > 0
    est, ci = boot_share(tp.core.astype(int).to_numpy(), np.ones(len(tp)), tp.ecell.to_numpy(), rng)
    out["H2"] = {"source_test_cells": len(src_cells), "test_presences": int(len(tp)), "share_with_core_record_same_cell": round(est, 4),
                 "ci": [round(c, 4) for c in ci],
                 "verdict": "Supported" if ci[0] > 0.10 else "Refuted" if ci[1] < 0.10 else "Inconclusive"}
    out["H2_broad_sensitivity"] = round(float(tp.core_or_broad.mean()), 4)
    # by source database (a cell is assigned to every core source with a plot in it)
    cs = meta[meta.cell_row.isin(src_cells) & meta.GIVD_ID.isin(core_src)][["cell_row", "Dataset"]].drop_duplicates()
    bys = tp.merge(cs, left_on="ecell", right_on="cell_row").groupby("Dataset").agg(presences=("core", "size"), share=("core", "mean"))
    out["H2_by_source"] = {k: {"presences": int(v.presences), "share": round(float(v.share), 4)} for k, v in bys.iterrows()}
    # exact coordinates (within 10 m of a source plot in the cell) and same date, same species
    core = pd.read_parquet(W / "core")
    core = core.merge(tp[["sp", "gx", "gy", "ecell"]].drop_duplicates(), on=["sp", "gx", "gy"])
    plots = meta[meta.cell_row.isin(src_cells) & meta.GIVD_ID.isin(core_src)][["cell_row", "Latitude", "Longitude", "Date_of_recording"]]
    m = core.merge(plots, left_on="ecell", right_on="cell_row")
    dlat = (m.decimallatitude - m.Latitude) * 111320
    dlon = (m.decimallongitude - m.Longitude) * 111320 * np.cos(np.radians(m.Latitude))
    m["near10"] = np.hypot(dlat, dlon) <= 10
    d = pd.to_datetime(m.Date_of_recording, errors="coerce")
    m["same_date"] = m.near10 & (m.year == d.dt.year) & (m.month == d.dt.month) & (m.day == d.dt.day)
    ex = m.groupby(["ecell", "sp"]).agg(near10=("near10", "any"), same_date=("same_date", "any")).reset_index()
    tp = tp.merge(ex, on=["ecell", "sp"], how="left").fillna({"near10": False, "same_date": False})
    out["exact_coordinate_share"] = round(float(tp.near10.mean()), 4)
    out["exact_coordinate_and_date_share"] = round(float(tp.same_date.mean()), 4)
    # RF population: species with >= 10 presences and >= 10 absences among range-masked source test cells
    absn = {}
    for c in sorted(src_cells):
        inrange = set(si[cl[c]:cl[c + 1]].tolist())
        present = set(eidx[eptr[c]:eptr[c + 1]].tolist())
        for s in inrange - present:
            absn[s] = absn.get(s, 0) + 1
    pop = tp.groupby("sp").size().rename("src_presences").reset_index()
    pop["src_absences"] = pop.sp.map(absn).fillna(0).astype(int)
    pop = pop[(pop.src_presences >= 10) & (pop.src_absences >= 10)]
    out["population_species"] = int(len(pop))
    if len(pop) > 2000:
        pop = pop.sample(2000, random_state=SEED)
    pop.sort_values("sp").to_csv(T / "population.csv", index=False)
    out["population_used"] = int(len(pop))
    (T / "audit.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
