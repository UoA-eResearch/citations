"""Score the frozen 2026-27 forecast. Written and committed before the season; run in July 2027, unchanged.

  1. Re-pull PortWatch daily calls and IBTrACS into data/raw_2027/ (run code/download.sh with the paths changed,
     recording a new VINTAGE.txt) once PortWatch covers 30 April 2027 + 135 days, i.e. about mid-September 2027.
     (The lead said July 2027; the recovery window needs 135 days after the last possible event.)
  2. Re-run events.py on the 2027 vintage (it writes events_all.csv, used to exclude storm-hit reference ports).
     Build season events exactly as events.py does: Cat 3+ within 150 km of a Pacific island port with
     >= 0.5 calls/day, closest approach between 1 Nov 2026 and 30 Apr 2027.
  3. For each, compute the observed outcome with recovery.one_event (reference-index counterfactual), and the
     forecast from the FROZEN coefficients in results/tables/forecast_model.json at the event's actual
     category and distance (verify that file's sha256 against the one in deviations.md first).
  4. Scores: Brier score for "disrupted" against the benchmark of the historical share disrupted; mean absolute
     log error of recovery time for disrupted events against the historical median. A forecast "beats the
     benchmark" only if it does on both, and with fewer than 3 events the result is reported, not interpreted.

Usage: venv/bin/python code/score_forecast.py data/raw_2027
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recovery as R  # noqa: E402
from events import PICT, haversine, hourly, load_tracks  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEASON = ("2026-11-01", "2027-04-30")


def frozen():
    model = json.load(open(TAB / "forecast_model.json"))
    print("forecast_model.json sha256", hashlib.sha256((TAB / "forecast_model.json").read_bytes()).hexdigest())
    return model


def predict(model, x):
    covs = model["covariates"]
    pa = model["part_a_logit"]
    z = pa["const"] + sum(pa[c] * x[c] for c in covs)
    p_dis = 1 / (1 + np.exp(-z))
    lam = model["part_b_weibull_aft"]
    log_scale = lam["lambda_|Intercept"] + sum(lam[f"lambda_|{c}"] * x[c] for c in covs)
    rho = np.exp(lam["rho_|Intercept"])
    median = np.exp(log_scale) * np.log(2) ** (1 / rho)
    return p_dis, median


def main(raw):
    raw = Path(raw)
    model = frozen()
    ports = pd.read_csv(raw / "portwatch" / "ports.csv")
    d = pd.read_csv(raw / "portwatch" / "daily.csv", usecols=["date", "portid", "portcalls"])
    d["date"] = pd.to_datetime(d.date.str[:10])
    calls = d.pivot_table(index="date", columns="portid", values="portcalls", aggfunc="sum").sort_index()
    act = calls.mean()
    pac = ports[ports.ISO3.isin(PICT) & ports.portid.map(act).ge(R.MIN_ACTIVITY)]
    import events as E
    E.RAW = raw
    tr = load_tracks()
    pos = ports.set_index("portid")[["lat", "lon"]]
    cyc = pd.read_csv(E.PROC / "events_all.csv")
    cyc["date"] = pd.to_datetime(cyc.date)
    cyc = cyc[cyc.cat_at_closest >= 1]
    tr = tr[(tr.ISO_TIME >= SEASON[0]) & (tr.ISO_TIME <= pd.Timestamp(SEASON[1]) + pd.Timedelta(days=1))]
    rows = []
    rng = np.random.default_rng(R.SEED)
    for sid, t in tr.groupby("SID"):
        times, la, lo, cat = hourly(t)
        for _, p in pac.iterrows():
            dist = haversine(p.lat, p.lon, la, lo)
            i = int(np.argmin(dist))
            if dist[i] <= 150 and cat[i] >= 3:
                d0 = pd.Timestamp(times[i].date())
                idx, _ = R.reference_index(calls, act, pos, cyc, p.portid, d0)
                res = R.one_event(calls[p.portid], idx, d0, rng, use_index=idx is not None)
                x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[p.portid]), cat=float(cat[i]),
                         closest_100km=dist[i] / 100, share=p.share_country_maritime_import / 100, sids=1.0)
                p_dis, med = predict(model, x)
                rows.append(dict(storm=t.NAME.iloc[0], port=p.portname, date=str(d0.date()), p_disrupted=p_dis,
                                 median_forecast=med, **{k: res.get(k) for k in ("status", "disrupted", "T", "event")}))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "forecast_scored.csv", index=False)
    ok = out[out.status == "ok"] if len(out) else out
    if len(ok) == 0:
        print("no scorable events in the season")
        return
    brier = float(np.mean((ok.p_disrupted - ok.disrupted.astype(float)) ** 2))
    brier0 = float(np.mean((model["benchmark_share_disrupted"] - ok.disrupted.astype(float)) ** 2))
    dis = ok[ok.disrupted.astype(bool)]
    mae = float(np.mean(np.abs(np.log(dis["T"].clip(lower=1)) - np.log(dis.median_forecast)))) if len(dis) else None
    mae0 = float(np.mean(np.abs(np.log(dis["T"].clip(lower=1)) - np.log(model["benchmark_median_T_disrupted"])))) if len(dis) else None
    json.dump(dict(n_events=int(len(ok)), brier=brier, brier_benchmark=brier0, mae_log_T=mae, mae_log_T_benchmark=mae0,
                   beats_benchmark=bool(brier < brier0 and (mae is None or mae < mae0)),
                   interpret=bool(len(ok) >= 3)), open(TAB / "forecast_score.json", "w"), indent=1)
    print(open(TAB / "forecast_score.json").read())


if __name__ == "__main__":
    # The observed outcome uses the same reference-index counterfactual as the historical events
    # (recovery.reference_index), so the forecast is scored on exactly the quantity it was fitted to.
    # Run events.py against the 2027 tracks first so events_all.csv holds the season's storms.
    sys.exit(main(sys.argv[1]))
