"""POST HOC (written after posthoc_distance.py found same-day flagged records for most co-located Dutch and Ukrainian
presences): are the flagged GBIF records copies of the evaluated relevés?

Cells: source test cells holding exactly one sPlotOpen plot, from a core-flagged source database, with a recording
date, so the cell's evaluation targets are that plot's species list (SAGE names). For each such cell, the species of
that database's flagged GBIF records in the same grid cell (a) dated the same day as the plot and (b) on other days.
Recall = share of the plot's species found among the flagged records; precision = share of the flagged species found
on the plot. Same relevé: both high on the same day.
-> results/tables/posthoc_same_releve.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from audit import B, T, W, csr, eval_cells  # noqa: E402


def main():
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", low_memory=False)
    flags = pd.read_csv(T / "provenance_flags.csv")
    core = flags[flags.flag == "core"]
    test = set(np.load(B / "test_indices.npy").tolist())
    one = meta.groupby("cell_row").size()
    one = set(one[one == 1].index) & test
    pl = meta[meta.cell_row.isin(one) & meta.GIVD_ID.isin(set(core.givd_source))].copy()
    pl["date"] = pd.to_datetime(pl.Date_of_recording, errors="coerce")
    pl = pl[pl.date.notna()].merge(eval_cells(), left_on="cell_row", right_on="ecell")
    keys = core.groupby("givd_source").datasetKey.apply(set).to_dict()
    eptr, eidx = csr(B / "targets" / "eval_targets.h5")
    rec = pd.read_parquet(W / "core", columns=["sp", "gx", "gy", "datasetkey", "year", "month", "day"])
    rec = rec.merge(pl[["gx", "gy"]].drop_duplicates(), on=["gx", "gy"])
    rec = rec.groupby(["gx", "gy"])
    out, rows = {}, []
    for t in pl.itertuples():
        P = set(int(s) for s in eidx[eptr[t.cell_row]:eptr[t.cell_row + 1]])
        if not P or (t.gx, t.gy) not in rec.groups:
            continue
        r = rec.get_group((t.gx, t.gy))
        r = r[r.datasetkey.isin(keys[t.GIVD_ID])]
        same = (r.year == t.date.year) & (r.month == t.date.month) & (r.day == t.date.day)
        for lab, g in (("same_day", set(r[same].sp)), ("other_days", set(r[~same].sp))):
            if g:
                rows.append({"Dataset": t.Dataset, "cell": t.cell_row, "which": lab, "plot_species": len(P),
                             "flagged_species": len(g), "recall": len(P & g) / len(P), "precision": len(P & g) / len(g)})
    d = pd.DataFrame(rows)
    for (db, lab), g in d.groupby(["Dataset", "which"]):
        out.setdefault(db, {})[lab] = {"cells": int(len(g)), "median_recall": round(float(g.recall.median()), 3),
                                       "median_precision": round(float(g.precision.median()), 3),
                                       "share_recall_and_precision_ge_0_8": round(float(((g.recall >= 0.8) & (g.precision >= 0.8)).mean()), 3),
                                       "median_plot_species": float(g.plot_species.median()),
                                       "median_flagged_species": float(g.flagged_species.median())}
    for db in out:
        out[db]["single_plot_dated_cells"] = int((pl.Dataset == db).sum())
    (T / "posthoc_same_releve.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
