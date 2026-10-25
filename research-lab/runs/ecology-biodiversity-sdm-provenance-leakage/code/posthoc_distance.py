"""POST HOC (written after the H1 and H2 results): how close are the provenance-shared training records to the source
plots they share a 1 km cell with? Separates literal duplication (records at the plot's coordinates) from co-location
only, and checks coordinate precision on both sides, since generalised coordinates would hide duplicates from the
preregistered 10 m test.

For each source database: test presences (range-masked, source cells) with a core-flagged record of the same species
in the same cell; the distance from each such record to the nearest plot of that database in the cell; per presence the
minimum. Null: the same number of records placed uniformly at random in the presence's EPSG:6933 cell (20 draws,
seed 20261026), distances computed the same way. Coordinate precision: share of records and plots whose latitude and
longitude have at most 2 and at most 3 decimal places (uninformative where coordinates were reprojected). Also the
share of co-located presences whose same-cell training presence is provenance-only, i.e. removed by C1, and the share
with a flagged record dated the same day as a plot of that database in the cell, at any distance (same-relevé check
that does not depend on coordinates).
-> results/tables/posthoc_distance.json
"""
import json
import sys
from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from audit import B, T, W, csr, eval_cells, train_cells  # noqa: E402
from pyproj import Transformer  # noqa: E402

INV = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)


def max_decimals(v, k):
    return np.isclose(np.round(v, k), v, rtol=0, atol=1e-9)


def main():
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", low_memory=False)
    flags = pd.read_csv(T / "provenance_flags.csv")
    core_src = set(flags[flags.flag == "core"].givd_source)
    test = set(np.load(B / "test_indices.npy").tolist())
    src_cells = set(meta[meta.GIVD_ID.isin(core_src)].cell_row) & test
    eptr, eidx = csr(B / "targets" / "eval_targets.h5")
    with h5py.File(B / "range_masks_1km" / "eval_range_mask.h5") as h:
        cl, si = h["cumulative_lengths"][:], h["species_index"][:]
    rows = []
    for c in sorted(src_cells):
        inrange = set(si[cl[c]:cl[c + 1]].tolist())
        rows += [(c, int(s)) for s in eidx[eptr[c]:eptr[c + 1]] if int(s) in inrange]
    tp = pd.DataFrame(rows, columns=["ecell", "sp"]).merge(eval_cells(), on="ecell")
    core = pd.read_parquet(W / "core", columns=["sp", "gx", "gy", "decimallatitude", "decimallongitude", "year", "month", "day"])
    rec = core.merge(tp, on=["sp", "gx", "gy"])
    plots = meta[meta.cell_row.isin(src_cells) & meta.GIVD_ID.isin(core_src)][["cell_row", "Dataset", "Latitude", "Longitude",
                                                                               "Date_of_recording"]]
    m = rec.merge(plots, left_on="ecell", right_on="cell_row")
    dlat = (m.decimallatitude - m.Latitude) * 111320
    dlon = (m.decimallongitude - m.Longitude) * 111320 * np.cos(np.radians(m.Latitude))
    m["dist"] = np.hypot(dlat, dlon)
    d = pd.to_datetime(m.Date_of_recording, errors="coerce")
    m["same_day"] = (m.year == d.dt.year) & (m.month == d.dt.month) & (m.day == d.dt.day)
    m["same_year"] = m.year == d.dt.year
    m["dated"] = d.notna() & m.year.notna() & m.day.notna()
    sd = m.groupby(["Dataset", "ecell", "sp"]).agg(same_day=("same_day", "any"), same_year=("same_year", "any"),
                                                  dated=("dated", "any")).reset_index()
    per = m.groupby(["Dataset", "ecell", "sp"]).dist.min().reset_index()
    # null: k uniform points per presence in its 1 km cell, min distance to the same plots
    k = rec.groupby(["ecell", "sp"]).size().rename("k").reset_index()
    pres = per[["Dataset", "ecell", "sp"]].merge(k, on=["ecell", "sp"]).merge(eval_cells(), on="ecell")
    pl = {key: g[["Latitude", "Longitude"]].to_numpy() for key, g in plots.groupby(["Dataset", "cell_row"])}
    rng = np.random.default_rng(20261026)
    null = {db: [] for db in pres.Dataset.unique()}
    for t in pres.itertuples():
        n = 20 * t.k
        x, y = (t.gx + rng.random(n)) * 1000, (t.gy + rng.random(n)) * 1000
        lon, lat = INV.transform(x, y)
        P = pl[(t.Dataset, t.ecell)]
        dl = (lat[:, None] - P[None, :, 0]) * 111320
        do = (lon[:, None] - P[None, :, 1]) * 111320 * np.cos(np.radians(P[None, :, 0]))
        d = np.hypot(dl, do).min(axis=1).reshape(20, t.k).min(axis=1)
        null[t.Dataset].append(d)
    po = pd.read_parquet(W / "prov_only.parquet").merge(train_cells(), on="cell")[["sp", "gx", "gy"]]
    po["removed"] = True
    col = per[["Dataset", "ecell", "sp"]].merge(eval_cells(), on="ecell").merge(po, on=["sp", "gx", "gy"], how="left")
    col["removed"] = col.removed.fillna(False).astype(bool)
    out = {}
    for db, g in per.groupby("Dataset"):
        r = rec[rec.ecell.isin(plots[plots.Dataset == db].cell_row)].drop_duplicates(["decimallatitude", "decimallongitude"])
        p = plots[plots.Dataset == db]
        q = sd[sd.Dataset == db]
        out[db] = {"presences_with_core_record": int(len(g)),
                   "share_dated_both_sides": round(float(q.dated.mean()), 4),
                   "share_same_day_any_distance": round(float(q.same_day.mean()), 4),
                   "share_same_year_any_distance": round(float(q.same_year.mean()), 4),
                   "share_removed_by_C1": round(float(col[col.Dataset == db].removed.mean()), 4),
                   "median_min_distance_m": round(float(g.dist.median()), 1),
                   "share_within_10m": round(float((g.dist <= 10).mean()), 4),
                   "share_within_100m": round(float((g.dist <= 100).mean()), 4),
                   "share_within_250m": round(float((g.dist <= 250).mean()), 4),
                   "null_median_min_distance_m": round(float(np.median(np.concatenate(null[db]))), 1),
                   "null_share_within_100m": round(float((np.concatenate(null[db]) <= 100).mean()), 4),
                   "null_share_within_250m": round(float((np.concatenate(null[db]) <= 250).mean()), 4),
                   "distinct_record_coordinates": int(len(r)),
                   "records_le_2_decimals": round(float((max_decimals(r.decimallatitude, 2) & max_decimals(r.decimallongitude, 2)).mean()), 4),
                   "records_le_3_decimals": round(float((max_decimals(r.decimallatitude, 3) & max_decimals(r.decimallongitude, 3)).mean()), 4),
                   "plots": int(len(p)),
                   "plots_le_2_decimals": round(float((max_decimals(p.Latitude, 2) & max_decimals(p.Longitude, 2)).mean()), 4),
                   "plots_le_3_decimals": round(float((max_decimals(p.Latitude, 3) & max_decimals(p.Longitude, 3)).mean()), 4)}
    (T / "posthoc_distance.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
