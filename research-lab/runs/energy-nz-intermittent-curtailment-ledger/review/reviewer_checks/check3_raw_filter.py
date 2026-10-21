"""Reviewer check 3: re-fetched raw EMI offers for 2025-10-15 against the study's filtered file; latest-row potentials
that are empty (and so dropped by the fetcher), MaximumOutputMegawatts, and the panel's P/offered for that day."""
import sys
import pandas as pd, numpy as np
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
raw = pd.read_csv(sys.argv[1], dtype=str)
print("raw rows", len(raw), "cols", list(raw.columns))
pocs = set(pd.read_csv(f"{RUN}/data/offers/20251015.csv.gz").PointOfConnection)
e = raw[(raw.ProductType == "Energy") & (raw.IsLatestYesNo == "Y")]
print("energy latest rows", len(e), " of which with potential:", e.ForecastOfGenerationPotentialMegawatts.fillna("").str.strip().ne("").sum())
w = e[e.PointOfConnection.isin(pocs)]
print("rows at the study's POCs:", len(w), " with potential:", w.ForecastOfGenerationPotentialMegawatts.fillna("").str.strip().ne("").sum())
print("units at those POCs:", sorted(w.Unit.unique()))
emp = w[w.ForecastOfGenerationPotentialMegawatts.fillna("").str.strip() == ""]
print("latest energy rows at study POCs with EMPTY potential (dropped by fetch.py):", len(emp), emp.groupby(["PointOfConnection", "Unit"]).size().to_dict())
# are there units with potential at POCs outside the study set?
x = e[e.ForecastOfGenerationPotentialMegawatts.fillna("").str.strip().ne("") & ~e.PointOfConnection.isin(pocs)]
print("latest energy rows with potential at POCs NOT in the study:", len(x), sorted(x.PointOfConnection.unique())[:20])
print("IsLatestYesNo values:", raw.IsLatestYesNo.value_counts().to_dict(), " ProductType:", raw.ProductType.value_counts().to_dict())
filt = pd.read_csv(f"{RUN}/data/offers/20251015.csv.gz")
print("study filtered rows:", len(filt), " expected:", int(w.ForecastOfGenerationPotentialMegawatts.fillna("").str.strip().ne("").sum()))
# one plant-day: WWD1102 TP 30-33: all submissions (latest and not) and the panel's P, offered, G, price
sub = raw[(raw.PointOfConnection == "LTN2201") & (raw.TradingPeriod.astype(int).between(30, 32))][
    ["TradingPeriod", "Unit", "SubmissionOrder", "IsLatestYesNo", "UTCSubmissionDate", "UTCSubmissionTime", "Tranche", "Megawatts", "DollarsPerMegawattHour", "ForecastOfGenerationPotentialMegawatts", "MaximumOutputMegawatts"]]
print(sub.sort_values(["TradingPeriod", "SubmissionOrder", "Tranche"]).to_string(index=False))
pan = pd.read_parquet(f"{RUN}/data/panel.parquet")
print(pan[(pan.poc == "LTN2201") & (pan.date == "2025-10-15") & pan.tp.between(30, 32)].to_string(index=False))
