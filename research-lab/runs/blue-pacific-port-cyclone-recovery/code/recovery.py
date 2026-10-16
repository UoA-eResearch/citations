"""Recovery time for every event: how long until a port's daily calls are back inside their expected range?

Committed with plan.md and run only after it.

For an event at port p with closest approach on day d0:

  counterfactual  A negative-binomial GLM fitted to the port's calls over [d0-730, d0-15]: day of week, two annual
                  harmonics, a linear trend, and an OFFSET of log summed calls at the REFERENCE ports (every port
                  with >= 0.5 calls/day lying 1000-4000 km from p and not itself within 250 km of a Cat 1+ storm in
                  [d0-30, d0+120]) - i.e. a model of the port's share of regional traffic, so a shock to all
                  shipping (COVID, early 2020) cancels. Sensitivity: the same model without the offset.
  window          k days, scaled to traffic: about TARGET_CALLS expected calls per window, at least 7, odd, at most
                  35. All smoothing is a centred k-day mean.
  disrupted       familywise: the deepest dip of observed / counterfactual (centred k-day means) over days
                  0..max(14, k) is below the 5th percentile of the same statistic over 2000 simulated paths.
  recovery time   if disrupted, the first day from the DEEPEST DIP onward such that the observed centred mean stays
                  at or above the pointwise 5% band for k consecutive days; censored at 120 days if never. If not
                  disrupted, 0 - reported as "no detectable disruption", never as a recovery.
  sensitivity     T10: the same, with "back within 10% of the counterfactual mean" in place of the band.

(This docstring was corrected after the adversarial review, deviations D8; it previously described the
pointwise 7-day rule and "first drop" start that tests replaced before any real event was computed. The code
below is unchanged since plan commit d12c3f0.)

Writes data/processed/recovery.csv.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from events import PICT, haversine  # noqa: E402

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW, PROC = RUN / "data" / "raw", RUN / "data" / "processed"
SEED = 20261017
NSIM = 2000
FIT_BACK, FIT_GAP, MIN_FIT_DAYS = 730, 15, 270
HORIZON, DROP_WINDOW, RUN_DAYS = 120, 14, 7
TARGET_CALLS, MAX_K = 10, 35       # expected calls per window, and the longest window allowed
MIN_ACTIVITY = 0.5
REF_KM = (1000.0, 4000.0)
SIDS = ["ATG", "BHS", "BRB", "BLZ", "CPV", "COM", "CUB", "DMA", "DOM", "FJI", "GRD", "GNB", "GUY", "HTI", "JAM", "KIR",
        "MDV", "MHL", "MUS", "FSM", "NRU", "PLW", "PNG", "WSM", "STP", "SYC", "SGP", "SLB", "KNA", "LCA", "VCT", "SUR",
        "TLS", "TON", "TTO", "TUV", "VUT", "BHR", "AIA", "ABW", "BMU", "VGB", "CYM", "MNP", "COK", "CUW", "PYF", "GLP",
        "GUM", "MTQ", "MSR", "NCL", "NIU", "PRI", "SXM", "TCA", "VIR", "ASM"]


def design(dates, index=None, t0=None):
    t = (dates - t0).days.to_numpy(float) / 365.25
    doy = dates.dayofyear.to_numpy(float)
    cols = {"const": 1.0, "trend": t}
    for k in (1, 2):
        cols[f"s{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
        cols[f"c{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
    dow = pd.get_dummies(dates.dayofweek, prefix="d", drop_first=True).astype(float)
    X = pd.DataFrame(cols, index=dates)
    X[dow.columns] = dow.to_numpy()
    return X


def offset(dates, index):
    """log of the reference index, entered with its coefficient fixed at 1: the model is then for the port's
    SHARE of regional traffic. A first version estimated the coefficient from the pre-event years, which contain
    no shared shocks, so it came out near zero and absorbed nothing (test_recovery.py check 4 caught it)."""
    if index is None:
        return np.zeros(len(dates))
    return np.log(index.reindex(dates).to_numpy(float) + 1.0)


def fit_nb(y, X, off):
    """NB2 by maximum likelihood; falls back to Poisson with a moment estimate of alpha."""
    try:
        r = sm.NegativeBinomial(y, X, offset=off).fit(disp=0, maxiter=200)
        alpha = float(r.params["alpha"])
        beta = r.params.drop("alpha")
        if np.isfinite(alpha) and alpha > 0 and r.mle_retvals.get("converged", True):
            return beta, alpha
    except Exception:
        pass
    r = sm.GLM(y, X, family=sm.families.Poisson(), offset=off).fit()
    mu = r.mu
    alpha = max(float(np.mean(((y - mu) ** 2 - mu) / np.maximum(mu, 1e-9) ** 2)), 1e-4)
    return r.params, alpha


def centred(a, k=RUN_DAYS):
    """Centred rolling mean over k days (k odd)."""
    s = pd.Series(a) if not isinstance(a, pd.Series) else a
    return s.rolling(k, center=True, min_periods=k).mean()


def one_event(calls, idx, d0, rng, use_index=True):
    t0 = d0 - pd.Timedelta(days=FIT_BACK)
    fit_d = pd.date_range(max(t0, calls.index.min()), d0 - pd.Timedelta(days=FIT_GAP))
    if len(fit_d) < MIN_FIT_DAYS:
        return dict(status="short_history", fit_days=len(fit_d))
    y = calls.reindex(fit_d).fillna(0).to_numpy(float)
    # Window length scaled to traffic: about TARGET_CALLS expected calls per window, at least 7 days, odd so
    # it centres. With a fixed 7-day window a 28-day closure at 0.5 calls/day went undetected every time in
    # simulation (detectability.py), because zero-call weeks occur by chance and the statistic floors at zero.
    k = int(min(MAX_K, max(RUN_DAYS, np.ceil(TARGET_CALLS / max(y.mean(), 1e-6)))))
    k += (k % 2 == 0)
    post_d = pd.date_range(d0 - pd.Timedelta(days=k), d0 + pd.Timedelta(days=HORIZON + k))
    if post_d.max() > calls.index.max():
        return dict(status="short_followup", window=k)
    ix = idx if use_index else None
    X = design(fit_d, None, t0)
    beta, alpha = fit_nb(y, X, offset(fit_d, ix))
    Xp = design(post_d, None, t0)[X.columns]
    mu = np.exp(np.clip(Xp.to_numpy() @ beta.reindex(X.columns).to_numpy() + offset(post_d, ix), -20, 10))
    n = 1.0 / alpha
    sims = rng.negative_binomial(n, n / (n + mu), size=(NSIM, len(mu)))
    sim_c = pd.DataFrame(sims).T.rolling(k, center=True, min_periods=k).mean()
    lower = sim_c.quantile(0.05, axis=1).to_numpy()
    m = centred(mu, k).to_numpy()
    r = centred(calls.reindex(post_d).fillna(0).to_numpy(float), k).to_numpy()
    day = (post_d - d0).days.to_numpy()
    w = (day >= 0) & (day <= max(DROP_WINDOW, k))
    below = (r < lower) & np.isfinite(lower)
    # Familywise: "below the pointwise 5% band on any of 15 days" gave 23% false alarms in testing, since it is
    # fifteen correlated chances. Instead the deepest dip in the window, r/m, is compared with the 5th percentile
    # of the same statistic over the simulated no-disruption paths.
    mm = np.maximum(m, 1e-9)
    depth = float(np.nanmin(np.where(w, r / mm, np.nan)))
    sim_depth = np.nanmin(np.where(w[:, None], sim_c.to_numpy() / mm[:, None], np.nan), axis=0)
    crit = float(np.nanpercentile(sim_depth, 5))
    out = dict(status="ok", fit_days=len(fit_d), alpha=alpha, cf_mean=float(np.nanmean(mu[day >= 0])),
               window=k, depth_min_ratio=depth, depth_crit=crit, disrupted=bool(depth < crit))
    if not out["disrupted"]:
        out.update(T=0.0, event=1, T10=0.0, event10=1)
        return out

    def recover(ok):
        """First day after the deepest dip from which the series stays back in range for a full window."""
        first_drop = int(np.nanargmin(np.where(w, r / mm, np.inf)))
        for i in range(first_drop, len(day) - k):
            if day[i] > HORIZON:
                break
            if ok[i:i + k].all():
                return float(day[i]), 1
        return float(HORIZON), 0
    out["T"], out["event"] = recover((r >= lower) & np.isfinite(r))
    out["T10"], out["event10"] = recover((r >= 0.9 * m) & np.isfinite(r))
    return out


def reference_index(calls, act, pos, cyclone, p, d0):
    """Summed daily calls at the reference ports for an event at port p on day d0: every port with >= 0.5
    calls/day lying 1000-4000 km from p and not itself within 250 km of a Cat 1+ storm in [d0-30, d0+120].
    Used identically for the historical events and for scoring the frozen 2026-27 forecast."""
    dist = haversine(pos.loc[p, "lat"], pos.loc[p, "lon"], pos.lat.to_numpy(), pos.lon.to_numpy())
    cand = pos.index[(dist >= REF_KM[0]) & (dist <= REF_KM[1])]
    hit = set(cyclone[(cyclone.date >= d0 - pd.Timedelta(days=30)) &
                      (cyclone.date <= d0 + pd.Timedelta(days=HORIZON))].portid)
    ref = [q for q in cand if q in calls and act.get(q, 0) >= MIN_ACTIVITY and q not in hit]
    return (calls[ref].sum(axis=1) if ref else None), ref


def main():
    ports = pd.read_csv(RAW / "portwatch" / "ports.csv")
    d = pd.read_csv(RAW / "portwatch" / "daily.csv", usecols=["date", "portid", "portcalls"])
    d["date"] = pd.to_datetime(d.date.str[:10])
    calls = d.pivot_table(index="date", columns="portid", values="portcalls", aggfunc="sum").sort_index()
    act = calls.mean()
    ev = pd.read_csv(PROC / "events_all.csv")
    ev["date"] = pd.to_datetime(ev.date)
    cyclone = ev[ev.cat_at_closest >= 1]                         # for excluding storm-affected reference ports
    pos = ports.set_index("portid")[["lat", "lon"]]
    prim = ev[(ev.cat_at_closest >= 1) & (ev.closest_km <= 250)].copy()   # compute for every arm's superset
    rng = np.random.default_rng(SEED)
    rows = []
    for _, e in prim.iterrows():
        p = e.portid
        base = dict(e.drop(labels=["date"]).to_dict(), date=e.date.date().isoformat(),
                    mean_calls=float(act.get(p, np.nan)), sids=e.ISO3 in SIDS, pict=e.ISO3 in PICT)
        if p not in calls or act.get(p, 0) < MIN_ACTIVITY:
            rows.append(dict(base, status="low_activity"))
            continue
        idx, ref = reference_index(calls, act, pos, cyclone, p, e.date)
        res = one_event(calls[p], idx, e.date, rng, use_index=idx is not None)
        res_own = one_event(calls[p], None, e.date, rng, use_index=False)
        rows.append(dict(base, n_ref_ports=len(ref), **res,
                         **{f"own_{k}": v for k, v in res_own.items() if k in ("T", "event", "disrupted", "status")}))
    out = pd.DataFrame(rows)
    out.to_csv(PROC / "recovery.csv", index=False)
    ok = out[out.status == "ok"]
    print(f"events {len(out)}; computed {len(ok)}; status counts {out.status.value_counts().to_dict()}")


if __name__ == "__main__":
    sys.exit(main())
