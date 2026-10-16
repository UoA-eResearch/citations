"""Score the frozen 2026-27 forecast. Revised after the adversarial review (deviations D8) so that it runs without
judgement calls; the forecast itself (forecast_model.json, forecast_table.csv) is unchanged and frozen.

When PortWatch covers 30 April 2027 + 135 days (about mid-September 2027):

  1. Download a new vintage into data/raw_2027/ (code/download.sh with its output directory changed) and record
     data/raw_2027/VINTAGE.txt.
  2. venv/bin/python code/events.py data/raw_2027 data/processed_2027
     (rebuilds the cyclone-port event table from the new tracks; the sealed data/raw and data/processed are
     untouched).
  3. venv/bin/python code/score_forecast.py data/raw_2027 data/processed_2027

What it does:
  - checks forecast_model.json's sha256 against the value frozen in deviations D6, and stops if it differs;
  - takes the ports and their covariates from results/tables/forecast_port_covariates.csv (the 2026 vintage, as
    forecast), not from the new vintage, and first checks that they reproduce forecast_table.csv exactly;
  - finds season events exactly as events.py defines them (Category 3+ within 150 km, closest approach between
    1 Nov 2026 and 30 Apr 2027) on hourly-interpolated FULL tracks, filtering by the closest-approach time;
  - computes each event's observed outcome with recovery.one_event and the reference index, from the new
    vintage's daily calls (seeded per event);
  - Brier score for "disrupted" against two benchmarks: the frozen all-port historical share (0.329) and the
    small-island historical share (1 of 17 = 0.059), reporting both;
  - recovery-time error, censoring-aware: for an observed recovery, |log T - log median|; for a recovery censored
    at 120 days, max(0, log 120 - log median) (a forecast at or beyond the censoring point is not penalised); the
    same for the benchmark median (5.5 days);
  - decision rule: fewer than 3 events -> reported, not interpreted; 3+ events with none disrupted ->
    uninformative about skill (low probabilities win automatically); otherwise the forecast "shows skill" only
    if its Brier score beats BOTH benchmarks AND its recovery error beats the benchmark median's.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recovery as R  # noqa: E402
from events import haversine, hourly  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEASON = (pd.Timestamp("2026-11-01"), pd.Timestamp("2027-04-30 23:59"))
MODEL_SHA256 = "0cbaa6e125ad071f05641a2c3ad58f096c4ad993bbef50220ed77ff6e43b8d25"   # deviations D6
SIDS_HISTORICAL_SHARE = 1 / 17                                                      # primary arm, results D4


def frozen():
    h = hashlib.sha256((TAB / "forecast_model.json").read_bytes()).hexdigest()
    if h != MODEL_SHA256:
        raise SystemExit(f"forecast_model.json sha256 {h} does not match the frozen {MODEL_SHA256}")
    return json.load(open(TAB / "forecast_model.json"))


def predict(model, x):
    pa = model["part_a_logit"]
    z = pa["const"] + sum(pa[c] * x[c] for c in model["covariates"])
    lam = model["part_b_weibull_aft"]
    log_scale = lam["lambda_|Intercept"] + sum(lam[f"lambda_|{c}"] * x[c]
                                               for c in model.get("part_b_covariates", model["covariates"]))
    rho = np.exp(lam["rho_|Intercept"])
    return float(1 / (1 + np.exp(-z))), float(np.exp(log_scale) * np.log(2) ** (1 / rho))


def self_check(model, cov):
    ft = pd.read_csv(TAB / "forecast_table.csv")
    for _, row in ft.iterrows():
        c = cov.loc[row.portid]
        x = dict(log_size=c.log_size, log_activity=c.log_activity, cat=float(row["cat"]),
                 closest_100km=row.closest_km / 100, share=c.share, sids=c.sids)
        p, med = predict(model, x)
        assert abs(p - row.p_disrupted) < 1e-9 and abs(med - row.median_T_if_disrupted) < 1e-6 * max(1, med), row.portname


def logerr(T, event, med):
    if event == 1:
        return abs(np.log(max(T, 1.0)) - np.log(med))
    return max(0.0, np.log(R.HORIZON) - np.log(med))


def main(raw, proc):
    raw, proc = Path(raw), Path(proc)
    model = frozen()
    cov = pd.read_csv(TAB / "forecast_port_covariates.csv").set_index("portid")
    self_check(model, cov)
    import events as E
    E.RAW = raw
    tracks = E.load_tracks()
    tracks = tracks[(tracks.ISO_TIME >= SEASON[0] - pd.Timedelta(days=30)) &
                    (tracks.ISO_TIME <= SEASON[1] + pd.Timedelta(days=30))]
    ports = pd.read_csv(raw / "portwatch" / "ports.csv")
    d = pd.read_csv(raw / "portwatch" / "daily.csv", usecols=["date", "portid", "portcalls"])
    d["date"] = pd.to_datetime(d.date.str[:10])
    calls = d.pivot_table(index="date", columns="portid", values="portcalls", aggfunc="sum").sort_index()
    act = calls.mean()
    pos = ports.set_index("portid")[["lat", "lon"]]
    cyc = pd.read_csv(proc / "events_all.csv"); cyc["date"] = pd.to_datetime(cyc.date)
    cyc = cyc[cyc.cat_at_closest >= 1]
    rows = []
    for sid, t in tracks.groupby("SID"):
        if len(t) < 2:
            continue
        times, la, lo, cat = hourly(t)                       # the full track, then filter by closest approach
        for portid, c in cov.iterrows():
            dist = haversine(c.lat, c.lon, la, lo)
            i = int(np.argmin(dist))
            if not (SEASON[0] <= times[i] <= SEASON[1]) or dist[i] > 150 or cat[i] < 3:
                continue
            d0 = pd.Timestamp(times[i].date())
            rng = np.random.default_rng([R.SEED, int(d0.strftime("%Y%m%d")), int(portid.replace("port", ""))])
            idx, _ = R.reference_index(calls, act, pos, cyc, portid, d0)
            res = R.one_event(calls[portid], idx, d0, rng, use_index=idx is not None) if portid in calls else \
                dict(status="no_calls")
            x = dict(log_size=c.log_size, log_activity=c.log_activity, cat=float(cat[i]),
                     closest_100km=dist[i] / 100, share=c.share, sids=c.sids)
            p, med = predict(model, x)
            rows.append(dict(storm=t.NAME.iloc[0], sid=sid, port=c.portname, date=str(d0.date()), cat=float(cat[i]),
                             closest_km=float(dist[i]), p_disrupted=p, median_forecast=med,
                             **{k: res.get(k) for k in ("status", "disrupted", "T", "event")}))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "forecast_scored.csv", index=False)
    ok = out[out.status == "ok"] if len(out) else out
    if len(ok) == 0:
        json.dump(dict(n_events=0, note="no scorable events in the season"), open(TAB / "forecast_score.json", "w"))
        print("no scorable events in the season")
        return
    y = ok.disrupted.astype(float)
    brier = float(np.mean((ok.p_disrupted - y) ** 2))
    b_all = float(np.mean((model["benchmark_share_disrupted"] - y) ** 2))
    b_sids = float(np.mean((SIDS_HISTORICAL_SHARE - y) ** 2))
    dis = ok[ok.disrupted.astype(bool)]
    err = [logerr(r.T, r.event, r.median_forecast) for r in dis.itertuples()]
    err0 = [logerr(r.T, r.event, model["benchmark_median_T_disrupted"]) for r in dis.itertuples()]
    score = dict(n_events=int(len(ok)), n_disrupted=int(len(dis)), brier=brier,
                 brier_benchmark_all_ports=b_all, brier_benchmark_small_island=b_sids,
                 mae_log_T=float(np.mean(err)) if err else None,
                 mae_log_T_benchmark=float(np.mean(err0)) if err0 else None,
                 interpret=bool(len(ok) >= 3))
    # decision rule, fixed after the review (deviations D8) so September 2027 holds no judgement call
    if len(ok) < 3:
        score["verdict"] = "reported, not interpreted (fewer than 3 events)"
    elif len(dis) == 0:
        score["verdict"] = "uninformative about skill (no event disrupted)"
    else:
        skill = (brier < b_all) and (brier < b_sids) and (score["mae_log_T"] < score["mae_log_T_benchmark"])
        score["verdict"] = "shows skill" if skill else "does not show skill"
    json.dump(score, open(TAB / "forecast_score.json", "w"), indent=1)
    print(json.dumps(score, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: venv/bin/python code/score_forecast.py data/raw_2027 data/processed_2027")
    sys.exit(main(sys.argv[1], sys.argv[2]))
