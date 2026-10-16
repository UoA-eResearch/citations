"""Reviewer check 8: re-derive forecast_table.csv from forecast_model.json with score_forecast.predict; the alternative
with the small-island indicator kept in part B (plan section 7 as written); benchmark fairness; censoring in scoring."""
import sys, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import analysis as A
import score_forecast as S
from lifelines import WeibullAFTFitter
model = json.load(open(RUN / "results/tables/forecast_model.json"))
print("model sha256", hashlib.sha256((RUN / "results/tables/forecast_model.json").read_bytes()).hexdigest())
print("table sha256", hashlib.sha256((RUN / "results/tables/forecast_table.csv").read_bytes()).hexdigest())
ft = pd.read_csv(RUN / "results/tables/forecast_table.csv")
ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv").set_index("portid")
act = pd.read_csv(RUN / "data/raw/portwatch/daily.csv", usecols=["portid", "portcalls"]).groupby("portid").portcalls.mean()
maxdp = maxdm = 0
for _, row in ft.iterrows():
    p = ports.loc[row.portid]
    x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[row.portid]), cat=float(row["cat"]), closest_100km=row.closest_km / 100,
             share=p.share_country_maritime_import / 100, sids=1.0)
    pd_, md = S.predict(model, x)
    maxdp = max(maxdp, abs(pd_ - row.p_disrupted)); maxdm = max(maxdm, abs(md - row.median_T_if_disrupted))
print(f"all {len(ft)} rows re-derived with score_forecast.predict: max |dp| {maxdp:.2e}, max |dmedian| {maxdm:.2e}")
print("rows with median > 120 (horizon):", int((ft.median_T_if_disrupted > 120).sum()), "; > 60:", int((ft.median_T_if_disrupted > 60).sum()))
print(ft[ft.median_T_if_disrupted > 120][["portname", "cat", "closest_km", "p_disrupted", "median_T_if_disrupted"]].round(3).to_string(index=False))
# the part-B fit behind the medians: 28 disrupted events, 6 parameters + rho
r = A.load("primary"); d = r[r.D_].copy(); d["T_"] = d.T_.clip(lower=1)
print("\npart B fitted on", len(d), "disrupted events;", int((d.E_ == 0).sum()), "censored; parameters:", len(model["part_b_weibull_aft"]))
print("implied time ratios: per category step", round(np.exp(model["part_b_weibull_aft"]["lambda_|cat"]), 2),
      "; 25 km vs 125 km", round(np.exp(-model["part_b_weibull_aft"]["lambda_|closest_100km"]), 2))
print("category values among disrupted events:", d["cat"].value_counts().to_dict(), "; max cat in forecast grid: 5 (no Cat 5 in the fitting data)")
fb = WeibullAFTFitter().fit(d[A.BASE + ["share", "sids", "T_", "E_"]], duration_col="T_", event_col="E_")
lam = {k[1]: v for k, v in fb.params_.items() if k[0] == "lambda_"}; rho = np.exp(fb.params_.loc[("rho_", "Intercept")])
print("\nif sids were kept in part B (plan section 7 as written): sids coef", round(float(lam["sids"]), 3), "-> time ratio", round(float(np.exp(lam["sids"])), 3))
out = []
for _, row in ft[(ft["cat"] == 4) & (ft.closest_km == 75)].iterrows():
    p = ports.loc[row.portid]
    x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[row.portid]), cat=4.0, closest_100km=0.75,
             share=p.share_country_maritime_import / 100, sids=1.0)
    ls = lam["Intercept"] + sum(lam[c] * x[c] for c in A.BASE + ["share", "sids"])
    out.append((row.portname, round(row.median_T_if_disrupted, 1), round(float(np.exp(ls) * np.log(2) ** (1 / rho)), 1)))
print("Cat 4 / 75 km medians (frozen, with-sids):", out)
print(f"\nbenchmark share disrupted {model['benchmark_share_disrupted']:.3f} (all ports) vs SIDS-only historical {r[r.sids==1].D_.mean():.3f} vs Pacific measurable 0/5")
print(f"Brier if NO season event is disrupted: benchmark {0.329**2:.3f}; forecast at p=0.08: {0.08**2:.4f}; at p=0.15: {0.15**2:.4f} -> forecast 'beats benchmark' whenever nothing happens")
print(f"Brier if ONE of three events is disrupted: benchmark {((0.329-1)**2+2*0.329**2)/3:.3f}; forecast p=0.08: {((0.08-1)**2+2*0.08**2)/3:.3f}")
# scoring: censoring
print("\nscore_forecast.py treats T=120 (censored) as observed in log(T); a 167-day median forecast vs a censored 120 is scored as |log(167/120)| =", round(abs(np.log(167 / 120)), 3))
# path handling: events.py RAW is module-level; score_forecast sets E.RAW but events.main() writes PROC/events_all.csv (the sealed one)
import events as E
print("events.py PROC path (where a 2027 re-run would write, overwriting the sealed table):", E.PROC)
print("score_forecast reads cyclone table from:", E.PROC / "events_all.csv", "and port covariates/activity from the 2027 vintage, not the frozen ones")
