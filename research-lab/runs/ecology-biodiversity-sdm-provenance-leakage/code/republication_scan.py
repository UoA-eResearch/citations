"""Republication scan (D4, after the independent review; post hoc). Adapted from the reviewer's check
(review/reviewer_checks/hidden_republication_scan.py), as the review suggested, to serve as a general flag check.

For every single-plot, dated sPlotOpen test cell of every source database, GBIF records in the same 1 km cell on the
plot's recording date (SAGE's basisOfRecord and uncertainty filters) are compared with the plot's species list, per
GBIF dataset. Flag rule (D4): a dataset republishes a source if at least MIN_HI of that source's single-plot cells
have recall >= 0.8 and precision >= 0.5. -> results/tables/republication_scan.csv (per source x dataset) and
results/tables/republication_flags_added.csv (datasets meeting the rule that the frozen list did not flag core).
"""
MIN_HI = 20

import sys, json, glob
import numpy as np, pandas as pd, duckdb
from pathlib import Path
RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN/"code")); import audit
from pyproj import Transformer
TR = Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)
OUT = RUN / "results" / "tables"
meta = pd.read_csv(RUN/"data/raw/eval_plot_metadata.csv", low_memory=False)
test = set(np.load(audit.B/"test_indices.npy").tolist())
one = meta.groupby("cell_row").size(); one = set(one[one==1].index) & test
pl = meta[meta.cell_row.isin(one)].copy(); pl["date"] = pd.to_datetime(pl.Date_of_recording, errors="coerce"); pl = pl[pl.date.notna()]
pl = pl.merge(audit.eval_cells(), left_on="cell_row", right_on="ecell")
pl["y"], pl["m"], pl["d"] = pl.date.dt.year, pl.date.dt.month, pl.date.dt.day
print("single-plot dated test cells:", len(pl), "| by source (top):", pl.Dataset.value_counts().head(12).to_dict(), flush=True)
eptr, eidx = audit.csr(audit.B/"targets/eval_targets.h5")
plot_sp = {int(r.cell_row): set(int(s) for s in eidx[eptr[r.cell_row]:eptr[r.cell_row+1]]) for r in pl.itertuples()}
sk = pd.read_csv(RUN/"data/registry/species_keys.csv"); by_key = {str(int(k)): int(i) for k,i in zip(sk.specieskey, sk["index"]) if pd.notna(k)}; by_name = dict(zip(sk.name, sk["index"]))
con = duckdb.connect(); con.execute("SET threads TO 8; SET memory_limit='20GB'")
P = pl[["cell_row","Dataset","GIVD_ID","y","m","d","Latitude","Longitude","gx","gy"]].rename(columns={"Latitude":"plat","Longitude":"plon"})
con.register("plots", P)
q = f"""
SELECT p.cell_row, p.Dataset, p.GIVD_ID, p.gx, p.gy, r.datasetkey, r.specieskey, r.species, r.decimallatitude, r.decimallongitude
FROM read_parquet('{RUN/"data/gbif_s3"}/*.parquet') r
JOIN plots p ON r.year = p.y AND r.month = p.m AND r.day = p.d
 AND abs(r.decimallatitude - p.plat) < 0.02 AND abs(r.decimallongitude - p.plon) < 0.03
WHERE r.basisofrecord IN ('HUMAN_OBSERVATION','OBSERVATION','PRESERVED_SPECIMEN')
  AND (r.coordinateuncertaintyinmeters IS NULL OR r.coordinateuncertaintyinmeters <= 1000)
"""
R = con.execute(q).df(); print("candidate same-day nearby records:", len(R), flush=True)
x, y = TR.transform(R.decimallongitude.to_numpy(float), R.decimallatitude.to_numpy(float))
R["rgx"], R["rgy"] = np.floor_divide(x,1000).astype(int), np.floor_divide(y,1000).astype(int)
R = R[(R.rgx==R.gx)&(R.rgy==R.gy)]
sp = R.specieskey.astype("string").map(lambda k: by_key.get(str(int(float(k))) if pd.notna(k) else None)); sp = sp.fillna(R.species.map(by_name))
R["sp"] = sp; R = R[R.sp.notna()]; R["sp"]=R.sp.astype(int)
print("same-cell same-day records with a SAGE species:", len(R), flush=True)
flags = pd.read_csv(RUN/"results/tables/provenance_flags_frozen.csv"); fl = dict(zip(flags.datasetKey, flags.flag))
rows=[]
for (cell, db, givd, dk), g in R.groupby(["cell_row","Dataset","GIVD_ID","datasetkey"]):
    S = set(g.sp); P_ = plot_sp[int(cell)]
    if not P_: continue
    rows.append({"cell":cell,"Dataset":db,"GIVD_ID":givd,"datasetkey":dk,"flag":fl.get(dk,"none"),"plot_sp":len(P_),"rec_sp":len(S),"recall":len(P_&S)/len(P_),"precision":len(P_&S)/len(S)})
D = pd.DataFrame(rows)
D["hi"] = (D.recall>=0.8)&(D.precision>=0.5)
summ = D.groupby(["Dataset","datasetkey","flag"]).agg(cells=("cell","nunique"), hi_cells=("hi","sum"), med_recall=("recall","median"), med_precision=("precision","median")).reset_index()
tot = pl.groupby("Dataset").size().rename("single_plot_dated_cells")
summ = summ.merge(tot, left_on="Dataset", right_index=True)
titles = {}
for f in glob.glob(str(RUN/"data/registry/datasets/*.json")):
    try: d=json.load(open(f)); titles[d["key"]]=(d.get("title") or "")[:70]
    except Exception: pass
summ["title"] = summ.datasetkey.map(titles)
summ = summ.sort_values("hi_cells", ascending=False)
summ.to_csv(OUT/"republication_scan.csv", index=False)
add = summ[(summ.hi_cells >= MIN_HI) & (summ.flag != "core")]
add.to_csv(OUT/"republication_flags_added.csv", index=False)
print("\n### meeting the flag rule but not core in the frozen list"); print(add.to_string(index=False))
print("\n### datasets with >= 5 single-plot cells where same-day same-cell records reproduce the plot (recall>=0.8, precision>=0.5)")
print(summ[summ.hi_cells>=5].to_string(index=False))
print("\n### by source database: cells covered by an UNFLAGGED dataset at high recall/precision")
un = D[(D.flag=="none")&D.hi].groupby("Dataset").cell.nunique().rename("cells_unflagged_hi").to_frame().merge(tot, left_index=True, right_index=True)
un["share"] = (un.cells_unflagged_hi/un.single_plot_dated_cells).round(3); print(un.sort_values("cells_unflagged_hi", ascending=False).to_string())
