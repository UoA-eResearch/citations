"""Checks prompted by the adversarial review (review/review.md), reproducing its key findings in the study's own
code (deviations D8). Post hoc; none changes a preregistered verdict. recovery.py and analysis.py are imported,
not modified.

  P1  placebo false-alarm rate: the real pipeline (reference index) at storm-free dates d0 -365, +365, -200, +200
      days for the 85 computed primary-arm events (review issue 4)
  P2  exposure: was the port inside the storm's 64-kt wind radius at closest approach (IBTrACS USA_R64, quadrant
      facing the port)? (issue 1)
  P3  event-specific power at every small-island and Pacific event: the event's own fitted counterfactual and
      reference index, a simulated post-event path with a complete closure of 7/10/14/21 days, or calls halved for
      14/28 days or cut to a quarter for 14 days, run through recovery.one_event (100 replicates each) (issues 1, 12)
  P4  import share and the number of PortWatch ports in the country (issue 2); per-arm part-A intervals (issue 16)
  P5  permutation null for H1's dAIC: import share shuffled across ports, 400 times (issue 3)
  P6  H2 without the guard added in D4: lifelines' own interval, the storm bootstrap, and a pooled ratio of mean
      recovery days including zeros (issue 5)
  P7  part B with the two Laura events that Delta hit on day 43-44 censored at day 43, and without Cebu/Rai (issues 6, 7)
  P8  the forecast medians had part B kept the small-island indicator, as plan section 7 specified (issue 8)
"""
import json
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import recovery as R  # noqa: E402
from events import haversine, hourly  # noqa: E402

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "tables"
SEED = 20261018
SHIFTS = (-365, 365, -200, 200)
NREP = 100

ports = pd.read_csv(RAW / "portwatch" / "ports.csv")
pos = ports.set_index("portid")[["lat", "lon"]]
d = pd.read_csv(RAW / "portwatch" / "daily.csv", usecols=["date", "portid", "portcalls"])
d["date"] = pd.to_datetime(d.date.str[:10])
calls = d.pivot_table(index="date", columns="portid", values="portcalls", aggfunc="sum").sort_index()
del d
act = calls.mean()
ev = pd.read_csv(PROC / "events_all.csv"); ev["date"] = pd.to_datetime(ev.date)
cyclone = ev[ev.cat_at_closest >= 1]
rec = pd.read_csv(TAB / "recovery_events.csv"); rec["date"] = pd.to_datetime(rec.date)
prim = rec[(rec.status == "ok") & (rec.cat_at_closest >= 3) & (rec.closest_km <= 150)].copy()


# ---------- P1 placebo ----------
def placebo_job(a):
    portid, d0, shift, k = a
    dd = d0 + pd.Timedelta(days=shift)
    near = cyclone[(cyclone.portid == portid) & (cyclone.date >= dd - pd.Timedelta(days=30)) &
                   (cyclone.date <= dd + pd.Timedelta(days=R.HORIZON))]
    if len(near):
        return dict(portid=portid, d0=d0, shift=shift, status="storm_in_window")
    rng = np.random.default_rng([SEED, k])
    idx, _ = R.reference_index(calls, act, pos, cyclone, portid, dd)
    r = R.one_event(calls[portid], idx, dd, rng, use_index=idx is not None)
    o = R.one_event(calls[portid], None, dd, rng, use_index=False)
    return dict(portid=portid, d0=d0, shift=shift, status=r.get("status"), disrupted=r.get("disrupted"),
                T=r.get("T"), event=r.get("event"), own_disrupted=o.get("disrupted"), mean_calls=float(act[portid]))


# ---------- P3 event-specific power ----------
def fitted_mu(series, idx, d0):
    """The counterfactual mean over the post-event window, exactly as recovery.one_event computes it."""
    t0 = d0 - pd.Timedelta(days=R.FIT_BACK)
    fit_d = pd.date_range(max(t0, series.index.min()), d0 - pd.Timedelta(days=R.FIT_GAP))
    y = series.reindex(fit_d).fillna(0).to_numpy(float)
    k = int(min(R.MAX_K, max(R.RUN_DAYS, np.ceil(R.TARGET_CALLS / max(y.mean(), 1e-6)))))
    k += (k % 2 == 0)
    post_d = pd.date_range(d0 - pd.Timedelta(days=k), d0 + pd.Timedelta(days=R.HORIZON + k))
    X = R.design(fit_d, None, t0)
    beta, alpha = R.fit_nb(y, X, R.offset(fit_d, idx))
    Xp = R.design(post_d, None, t0)[X.columns]
    mu = np.exp(np.clip(Xp.to_numpy() @ beta.reindex(X.columns).to_numpy() + R.offset(post_d, idx), -20, 10))
    return post_d, mu, alpha


SCEN = [("closed_7d", 7, 0.0), ("closed_10d", 10, 0.0), ("closed_14d", 14, 0.0), ("closed_21d", 21, 0.0),
        ("halved_14d", 14, 0.5), ("halved_28d", 28, 0.5), ("quarter_14d", 14, 0.25)]


def power_job(a):
    portid, d0, k = a
    rng = np.random.default_rng([SEED + 1, k])
    idx, _ = R.reference_index(calls, act, pos, cyclone, portid, d0)
    s = calls[portid]
    post_d, mu, alpha = fitted_mu(s, idx, d0)
    n = 1.0 / alpha
    day = (post_d - d0).days.to_numpy()
    out = dict(portid=portid, date=str(d0.date()), alpha=alpha)
    for name, L, frac in SCEN:
        hits = 0
        for _ in range(NREP):
            y = rng.negative_binomial(n, n / (n + mu)).astype(float)
            win = (day >= 0) & (day < L)
            y[win] = rng.binomial(y[win].astype(int), frac) if frac > 0 else 0.0
            syn = s.copy()
            syn.loc[post_d] = y
            r = R.one_event(syn, idx, d0, rng, use_index=idx is not None)
            hits += bool(r.get("disrupted"))
        out[name] = hits / NREP
    return out


# ---------- P2 exposure ----------
def exposure():
    t = pd.read_csv(RAW / "ibtracs" / "ibtracs.since1980.csv", skiprows=[1], low_memory=False,
                    usecols=["SID", "ISO_TIME", "LAT", "LON", "USA_SSHS", "USA_WIND", "USA_R64_NE", "USA_R64_SE",
                             "USA_R64_SW", "USA_R64_NW"], keep_default_na=False, na_values=["", " "])
    t["ISO_TIME"] = pd.to_datetime(t.ISO_TIME)
    for c in t.columns[2:]:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    t["cat"] = 0
    rows = []
    for _, e in prim.iterrows():
        tr = t[t.SID == e.sid].dropna(subset=["LAT", "LON"]).sort_values("ISO_TIME")
        times, la, lo, _ = hourly(tr)
        p = pos.loc[e.portid]
        dist = haversine(p.lat, p.lon, la, lo)
        i = int(np.argmin(dist))
        fix = tr.iloc[int(np.abs((tr.ISO_TIME - times[i]).dt.total_seconds()).argmin())]
        # bearing from storm centre to port
        y = np.sin(np.radians(p.lon - lo[i])) * np.cos(np.radians(p.lat))
        x = np.cos(np.radians(la[i])) * np.sin(np.radians(p.lat)) - \
            np.sin(np.radians(la[i])) * np.cos(np.radians(p.lat)) * np.cos(np.radians(p.lon - lo[i]))
        brg = (np.degrees(np.arctan2(y, x)) + 360) % 360
        q = "USA_R64_NE" if brg < 90 else "USA_R64_SE" if brg < 180 else "USA_R64_SW" if brg < 270 else "USA_R64_NW"
        r64 = fix[q]
        rows.append(dict(portid=e.portid, sid=e.sid, closest_km_hourly=float(dist[i]), quadrant=q[-2:],
                         r64_km=float(r64 * 1.852) if np.isfinite(r64) else np.nan,
                         inside_r64=(bool(dist[i] <= r64 * 1.852) if np.isfinite(r64) else None)))
    return pd.DataFrame(rows)


def main():
    out = {}
    # P1
    jobs = [(e.portid, e.date, s, i * 10 + j) for i, (_, e) in enumerate(prim.iterrows()) for j, s in enumerate(SHIFTS)]
    with Pool(28) as pool:
        pl = pd.DataFrame(pool.map(placebo_job, jobs, chunksize=4))
    pl = pl.merge(prim[["portid", "date", "portname", "storm", "sids"]].rename(columns={"date": "d0"}), on=["portid", "d0"])
    pl.to_csv(TAB / "placebo_false_alarms.csv", index=False)
    v = pl[pl.status == "ok"].copy()
    v["band"] = pd.cut(v.mean_calls, [0, 1, 2, 5, 1e9], labels=["0.5-1", "1-2", "2-5", ">5"])
    fa = float(v.disrupted.mean())
    out["P1_placebo"] = dict(
        runs=int(len(v)), skipped_storm=int((pl.status == "storm_in_window").sum()),
        skipped_other=int(((pl.status != "ok") & (pl.status != "storm_in_window")).sum()),
        false_alarm_rate=fa, flagged=int(v.disrupted.sum()), own_history_rate=float(v.own_disrupted.mean()),
        by_traffic={str(b): dict(n=int(len(g)), rate=float(g.disrupted.mean())) for b, g in v.groupby("band", observed=True)},
        by_group={("sids" if k else "non_sids"): dict(n=int(len(g)), flagged=int(g.disrupted.sum()), rate=float(g.disrupted.mean()))
                  for k, g in v.groupby("sids")},
        spurious_T_median=float(v[v.disrupted.astype(bool)]["T"].median()),
        spurious_T_censored=int((v.disrupted.astype(bool) & (v.event == 0)).sum()),
        expected_false_alarms=dict(all_85=85 * fa, non_sids_68=68 * fa, sids_17=17 * fa))
    print("P1", json.dumps(out["P1_placebo"], indent=1, default=float), flush=True)

    # P2
    ex = exposure()
    pe = prim.merge(ex, on=["portid", "sid"])
    pe[["portid", "portname", "ISO3", "storm", "date", "closest_km", "cat_at_closest", "mean_calls", "sids", "pict",
        "disrupted", "T", "quadrant", "r64_km", "inside_r64"]].to_csv(TAB / "exposure_primary.csv", index=False)
    known = pe[pe.inside_r64.notna()]
    out["P2_exposure"] = {f"{g}_{'inside' if ins else 'outside'}": dict(n=int(len(x)), disrupted=int(x.disrupted.sum()))
                          for (g, ins), x in known.groupby([known.sids.map({True: 'sids', False: 'non_sids'}), known.inside_r64.astype(bool)])}
    out["P2_exposure"]["r64_missing"] = int(pe.inside_r64.isna().sum())
    try:
        from scipy.stats import fisher_exact
        for ins in (True, False):
            x = known[known.inside_r64.astype(bool) == ins]
            tab = [[int(x[x.sids].disrupted.sum()), int((~x[x.sids].disrupted.astype(bool)).sum())],
                   [int(x[~x.sids].disrupted.sum()), int((~x[~x.sids].disrupted.astype(bool)).sum())]]
            out["P2_exposure"][f"fisher_p_{'inside' if ins else 'outside'}"] = float(fisher_exact(tab)[1])
    except Exception as e:
        out["P2_exposure"]["fisher_error"] = str(e)
    print("P2", out["P2_exposure"], flush=True)

    # P3
    tgt = prim[prim.sids | prim.pict]
    jobs = [(e.portid, e.date, i) for i, (_, e) in enumerate(tgt.iterrows())]
    with Pool(len(jobs)) as pool:
        pw = pd.DataFrame(pool.map(power_job, jobs))
    pw["date"] = pd.to_datetime(pw.date)
    pw = tgt[["portid", "portname", "ISO3", "storm", "date", "mean_calls", "window", "sids", "pict", "disrupted"]].merge(pw, on=["portid", "date"])
    pw = pw.merge(pe[["portid", "date", "inside_r64", "r64_km"]], on=["portid", "date"], how="left")
    pw.to_csv(TAB / "event_power_sids.csv", index=False)
    s = pw[pw.sids]
    out["P3_event_power_sids"] = {name: dict(mean=float(s[name].mean()), min=float(s[name].min()),
                                             n_below_0_8=int((s[name] < 0.8).sum())) for name, *_ in SCEN}
    print("P3", json.dumps(out["P3_event_power_sids"], indent=1), flush=True)
    print(pw[["portname", "storm", "mean_calls", "inside_r64", "closed_7d", "closed_14d", "halved_14d", "halved_28d"]].round(2).to_string(index=False))

    # P4
    r = A.load("primary")
    nports = ports.groupby("ISO3").size()
    r["log_nports"] = np.log(r.ISO3.map(nports))
    m = A.part_a(r, A.BASE + ["share", "log_nports"])
    out["P4_country_ports"] = dict(
        corr_share_log_nports=float(np.corrcoef(r.share, r.log_nports)[0, 1]),
        share=dict(coef=float(m.params["share"]), p=float(m.pvalues["share"])),
        log_nports=dict(coef=float(m.params["log_nports"]), p=float(m.pvalues["log_nports"])))
    r1 = A.load("cat1_150km"); r1["log_nports"] = np.log(r1.ISO3.map(nports))
    m1 = A.part_a(r1, A.BASE + ["share", "log_nports"])
    out["P4_country_ports"]["cat1_150km"] = dict(share=dict(coef=float(m1.params["share"]), p=float(m1.pvalues["share"])),
                                                 log_nports=dict(coef=float(m1.params["log_nports"]), p=float(m1.pvalues["log_nports"])))
    arm_ci = {}
    for arm in A.ARMS:
        ra = A.load(arm); ma = A.part_a(ra, A.BASE + ["share"]); ci = ma.conf_int().loc["share"]
        arm_ci[arm] = [float(np.exp(0.1 * x)) for x in (ma.params["share"], ci[0], ci[1])]
    out["P4_part_a_share_or_per_10pp_by_arm"] = arm_ci
    print("P4", out["P4_country_ports"], arm_ci, flush=True)

    # P5
    base_aic = A.aic_two_part(r, A.BASE)[0]
    obs = base_aic - A.aic_two_part(r, A.BASE + ["share"])[0]
    port_share = r.groupby("portid").share.first()
    rng = np.random.default_rng(SEED + 2)
    perms = []
    for _ in range(400):
        sh = pd.Series(rng.permutation(port_share.to_numpy()), index=port_share.index)
        rp = r.assign(share=r.portid.map(sh))
        try:
            perms.append(base_aic - A.aic_two_part(rp, A.BASE + ["share"])[0])
        except Exception:
            pass
    perms = np.array(perms)
    out["P5_permutation"] = dict(observed=float(obs), n=int(len(perms)), p=float((perms >= obs).mean()),
                                 q90=float(np.percentile(perms, 90)), q95=float(np.percentile(perms, 95)),
                                 share_supported=float((perms >= 10).mean()))
    print("P5", out["P5_permutation"], flush=True)

    # P6
    b = A.part_b(r, A.BASE + ["sids"])
    srow = b.summary.loc[("lambda_", "sids")]
    bs = A.boot_b(r, A.BASE + ["sids"], "sids")
    rngp = np.random.default_rng(SEED + 3)
    storms = r.sid.unique(); groups = {k: g for k, g in r.groupby("sid")}
    ratios = []
    for _ in range(1000):
        rb = pd.concat([groups[k] for k in rngp.choice(storms, len(storms))])
        ms, mn = rb[rb.sids == 1].T_.mean(), rb[rb.sids == 0].T_.mean()
        if np.isfinite(ms) and mn > 0:
            ratios.append(ms / mn)
    out["P6_h2_without_guard"] = dict(
        lifelines_wald=[float(np.exp(srow["coef"])), float(np.exp(srow["coef lower 95%"])), float(np.exp(srow["coef upper 95%"]))],
        storm_bootstrap=dict(tr=float(np.exp(b.params_.loc[("lambda_", "sids")])),
                             lo=float(np.exp(bs["lo"])) if bs["lo"] is not None else None,
                             hi=float(np.exp(bs["hi"])) if bs["hi"] is not None else None, ok_draws=bs["ok_draws"]),
        pooled_mean_days=dict(sids=float(r[r.sids == 1].T_.mean()), non_sids=float(r[r.sids == 0].T_.mean()),
                              ratio_ci=[float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]))
    print("P6", out["P6_h2_without_guard"], flush=True)

    # P7
    comp = (r.storm == "LAURA") & r.portname.isin(["Lake Charles", "Calcasieu Pass LNG Terminal"])
    rc = r.copy(); rc.loc[comp, "T_"] = 43.0; rc.loc[comp, "E_"] = 0
    rnc = r[~((r.portname == "Cebu") & (r.storm == "RAI"))]
    p7 = {}
    for name, rr in (("laura_delta_censored_day43", rc), ("without_cebu_rai", rnc)):
        b0, b1 = A.part_b(rr, A.BASE), A.part_b(rr, A.BASE + ["share"])
        p7[name] = dict(n_flagged=int(comp.sum()) if name.startswith("laura") else 1,
                        part_b_cat_tr=float(np.exp(b0.params_.loc[("lambda_", "cat")])),
                        part_b_delta_aic_share=float(b0.AIC_ - b1.AIC_),
                        median_T_disrupted=float(rr[rr.D_].T_.median()))
    p7["original_part_b_cat_tr"] = float(np.exp(A.part_b(r, A.BASE).params_.loc[("lambda_", "cat")]))
    out["P7_part_b_sensitivity"] = p7
    print("P7", p7, flush=True)

    # P8
    fm = json.load(open(TAB / "forecast_model.json"))
    covs = fm["covariates"]
    bfull = A.part_b(r, covs)
    ft = pd.read_csv(TAB / "forecast_table.csv")
    pp = ports.set_index("portid")
    alt = []
    for _, row in ft[(ft["cat"] == 4) & (ft.closest_km == 75)].iterrows():
        p = pp.loc[row.portid]
        x = dict(log_size=np.log(p.vessel_count_total + 1), log_activity=np.log(act[row.portid]), cat=4.0,
                 closest_100km=0.75, share=p.share_country_maritime_import / 100, sids=1.0)
        alt.append(dict(port=row.portname, frozen_median=float(row.median_T_if_disrupted),
                        median_if_sids_kept=float(bfull.predict_median(pd.DataFrame([x])[covs]).iloc[0])))
    out["P8_forecast_if_sids_kept_in_part_b"] = dict(sids_coef=float(bfull.params_.loc[("lambda_", "sids")]), cat4_75km=alt)
    print("P8", out["P8_forecast_if_sids_kept_in_part_b"], flush=True)

    json.dump(out, open(TAB / "review_response.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    sys.exit(main())
