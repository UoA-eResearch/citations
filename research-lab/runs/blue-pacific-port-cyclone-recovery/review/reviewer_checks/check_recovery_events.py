"""Reviewer check 3 and 6: plot calls vs counterfactual for named events; event-specific power (under each event's own
fitted model, window and threshold) for complete and partial closures at all 17 small-island events; NB fit status;
second storms inside the recovery window; Cebu's monthly series."""
import sys, pickle, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import recovery as R
HERE = Path(__file__).parent
calls = pickle.load(open(HERE / "cache/calls.pkl", "rb"))
act = calls.mean()
ports = pd.read_csv(RUN / "data/raw/portwatch/ports.csv"); pos = ports.set_index("portid")[["lat", "lon"]]
ev = pd.read_csv(RUN / "data/processed/events_all.csv"); ev["date"] = pd.to_datetime(ev.date)
cyclone = ev[ev.cat_at_closest >= 1]
rec = pd.read_csv(RUN / "results/tables/recovery_events.csv"); rec["date"] = pd.to_datetime(rec.date)
ok = rec[(rec.status == "ok") & (rec.cat_at_closest >= 3) & (rec.closest_km <= 150)].copy()

def internals(series, idx, d0, rng, use_index=True):
    """recovery.one_event with its internals exposed (same arithmetic, same seed usage)."""
    t0 = d0 - pd.Timedelta(days=R.FIT_BACK)
    fit_d = pd.date_range(max(t0, series.index.min()), d0 - pd.Timedelta(days=R.FIT_GAP))
    y = series.reindex(fit_d).fillna(0).to_numpy(float)
    k = int(min(R.MAX_K, max(R.RUN_DAYS, np.ceil(R.TARGET_CALLS / max(y.mean(), 1e-6))))); k += (k % 2 == 0)
    post_d = pd.date_range(d0 - pd.Timedelta(days=k), d0 + pd.Timedelta(days=R.HORIZON + k))
    ix = idx if use_index else None
    X = R.design(fit_d, None, t0)
    # did the NB MLE converge, or did fit_nb fall back to Poisson + moment alpha?
    conv = None
    try:
        m0 = sm.NegativeBinomial(y, X, offset=R.offset(fit_d, ix)).fit(disp=0, maxiter=200)
        conv = dict(converged=bool(m0.mle_retvals.get("converged", True)), alpha_mle=float(m0.params["alpha"]))
    except Exception as e:
        conv = dict(converged=False, error=str(e)[:60])
    beta, alpha = R.fit_nb(y, X, R.offset(fit_d, ix))
    Xp = R.design(post_d, None, t0)[X.columns]
    mu = np.exp(np.clip(Xp.to_numpy() @ beta.reindex(X.columns).to_numpy() + R.offset(post_d, ix), -20, 10))
    n = 1.0 / alpha
    sims = rng.negative_binomial(n, n / (n + mu), size=(R.NSIM, len(mu)))
    sim_c = pd.DataFrame(sims).T.rolling(k, center=True, min_periods=k).mean()
    lower = sim_c.quantile(0.05, axis=1).to_numpy()
    m = R.centred(mu, k).to_numpy(); obs = series.reindex(post_d).fillna(0).to_numpy(float)
    r = R.centred(obs, k).to_numpy(); day = (post_d - d0).days.to_numpy()
    w = (day >= 0) & (day <= max(R.DROP_WINDOW, k)); mm = np.maximum(m, 1e-9)
    depth = float(np.nanmin(np.where(w, r / mm, np.nan)))
    sim_depth = np.nanmin(np.where(w[:, None], sim_c.to_numpy() / mm[:, None], np.nan), axis=0)
    crit = float(np.nanpercentile(sim_depth, 5))
    return dict(k=k, post_d=post_d, day=day, mu=mu, m=m, r=r, obs=obs, lower=lower, w=w, depth=depth, crit=crit, alpha=alpha, n=n, conv=conv,
                fit_mean=float(y.mean()), index_post=(ix.reindex(post_d).to_numpy(float) if ix is not None else None))

def power(I, rng, L, keep, reps=300):
    """Share of model-simulated paths with calls on days 0..L-1 thinned to `keep` (0 = complete closure) whose deepest
    dip falls below this event's own threshold."""
    mu, n, k, w, mm = I["mu"], I["n"], I["k"], I["w"], np.maximum(I["m"], 1e-9)
    sims = rng.negative_binomial(n, n / (n + mu), size=(reps, len(mu))).astype(float)
    cl = (I["day"] >= 0) & (I["day"] < L)
    sims[:, cl] = rng.binomial(sims[:, cl].astype(int), keep) if keep > 0 else 0.0
    sim_c = pd.DataFrame(sims).T.rolling(k, center=True, min_periods=k).mean().to_numpy()
    depth = np.nanmin(np.where(w[:, None], sim_c / mm[:, None], np.nan), axis=0)
    return float(np.mean(depth < I["crit"]))

def run(portname, storm):
    e = rec[(rec.portname == portname) & (rec.storm == storm)].iloc[0]
    rng = np.random.default_rng(R.SEED)
    idx, ref = R.reference_index(calls, act, pos, cyclone, e.portid, e.date)
    I = internals(calls[e.portid], idx, e.date, rng, use_index=idx is not None)
    return e, I, ref

def plot(e, I, name, T):
    fig, ax = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    d = I["day"]
    ax[0].bar(d, I["obs"], color="#999", width=1, label="observed daily calls")
    ax[0].plot(d, I["mu"], color="#2a78d6", lw=1.2, label="counterfactual mean (reference-index model)")
    ax[0].axvline(0, color="k", lw=0.8); ax[0].legend(fontsize=8, loc="upper right"); ax[0].set_ylabel("calls/day")
    ax[0].set_title(f"{e.portname} / {e.storm} ({e.date.date()}, Cat {e.cat_at_closest:.0f} at {e.closest_km:.0f} km): mean {e.mean_calls:.2f}/day, window {I['k']} d, "
                    f"dip {I['depth']:.2f} vs threshold {I['crit']:.2f}, disrupted={bool(e.disrupted)}, T={T}", fontsize=9, loc="left")
    ax[1].plot(d, I["r"], color="k", lw=1.4, label=f"observed, centred {I['k']}-day mean")
    ax[1].plot(d, I["m"], color="#2a78d6", lw=1.2, label="counterfactual, centred mean")
    ax[1].plot(d, I["lower"], color="#2a78d6", lw=0.8, ls="--", label="5th percentile of simulated paths")
    ax[1].axvline(0, color="k", lw=0.8)
    if T and T > 0: ax[1].axvline(T, color="#eb6834", lw=1, ls=":", label=f"recovery day {T:.0f}")
    ax[1].set_xlim(-I["k"], 120 + I["k"]); ax[1].set_xlabel("days from closest approach"); ax[1].legend(fontsize=8, loc="upper right")
    if I["index_post"] is not None:
        ax2 = ax[1].twinx(); ax2.plot(d, I["index_post"], color="#bbb", lw=0.8); ax2.set_ylabel("reference index (grey)", color="#888", fontsize=8); ax2.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(HERE / "figs" / f"{name}.png", dpi=130); plt.close(fig)

pd.set_option("display.width", 220)
named = [("Kingston", "MELISSA"), ("Noumea", "NIRAN"), ("Cebu", "RAI"), ("Lake Charles", "LAURA"), ("Calcasieu Pass LNG Terminal", "LAURA"),
         ("Montego Bay", "MELISSA"), ("Santiago De Cuba", "MELISSA"), ("Nuku'alofa", "HAROLD"), ("Suva", "HAROLD"), ("Apra Harbor", "MAWAR"), ("Kingston", "BERYL")]
print("=== named events: reproduce the study's dip/threshold and show the NB fit status ===")
for pn, st in named:
    e, I, ref = run(pn, st)
    plot(e, I, f"{pn.replace(' ', '_').replace(chr(39), '')}_{st}", e["T"])
    print(f"{pn:28s} {st:8s} study dip {e.depth_min_ratio:.3f}/crit {e.depth_crit:.3f} | review dip {I['depth']:.3f}/crit {I['crit']:.3f} | k {I['k']} | alpha {I['alpha']:.4f} NB-MLE {I['conv']} | refs {len(ref)}")

print("\n=== second Cat 1+ storm within 250 km of the same port inside the 120-day window, disrupted events ===")
for _, e in ok[ok.disrupted].iterrows():
    nxt = cyclone[(cyclone.portid == e.portid) & (cyclone.date > e.date) & (cyclone.date <= e.date + pd.Timedelta(days=120))]
    if len(nxt):
        print(f"  {e.portname:28s} {e.storm:10s} T={e['T']:.0f}: followed by " + "; ".join(f"{n.storm} (Cat {n.cat_at_closest:.0f}, {n.closest_km:.0f} km, day {(n.date - e.date).days})" for _, n in nxt.iterrows()))
print("\n=== second storm inside the window, NOT-disrupted SIDS events ===")
for _, e in ok[ok.sids & ~ok.disrupted].iterrows():
    nxt = cyclone[(cyclone.portid == e.portid) & (cyclone.date > e.date) & (cyclone.date <= e.date + pd.Timedelta(days=120))]
    if len(nxt): print(f"  {e.portname:20s} {e.storm:10s}: " + "; ".join(f"{n.storm} (Cat {n.cat_at_closest:.0f}, {n.closest_km:.0f} km, day {(n.date - e.date).days})" for _, n in nxt.iterrows()))

print("\n=== event-specific power at the 17 small-island events (own fitted model, window, threshold; 300 paths) ===")
rows = []
for _, e in ok[ok.sids].sort_values("date").iterrows():
    rng = np.random.default_rng(R.SEED)
    idx, ref = R.reference_index(calls, act, pos, cyclone, e.portid, e.date)
    I = internals(calls[e.portid], idx, e.date, rng, use_index=idx is not None)
    prng = np.random.default_rng(77)
    rows.append(dict(port=e.portname, storm=e.storm, calls=round(e.mean_calls, 2), k=I["k"], alpha=round(I["alpha"], 3), crit=round(I["crit"], 2), dip=round(I["depth"], 2),
                     c7=power(I, prng, 7, 0), c10=power(I, prng, 10, 0), c14=power(I, prng, 14, 0), c21=power(I, prng, 21, 0),
                     h14=power(I, prng, 14, 0.5), h28=power(I, prng, 28, 0.5), q14=power(I, prng, 14, 0.25), q28=power(I, prng, 28, 0.25)))
P = pd.DataFrame(rows); P.to_csv(HERE / "sids_event_power.csv", index=False)
print(P.to_string(index=False))
print("\nmeans: ", P[["c7", "c10", "c14", "c21", "h14", "h28", "q14", "q28"]].mean().round(2).to_dict())
print("(c = complete closure of N days; h = calls halved for N days; q = calls cut to a quarter for N days)")
print("events with power < 0.8 for a complete 14-day closure:", int((P.c14 < 0.8).sum()), "; for calls halved for 28 days:", int((P.h28 < 0.8).sum()))
# per-event power using the study's grid interpolation (supplementary.power) for comparison
import json
g = pd.DataFrame(json.load(open(RUN / "results/tables/detectability.json"))["grid"])
sys.path.insert(0, str(RUN / "code")); import supplementary as SU
P["grid_pow14"] = [SU.power(g, c, a, 14) for c, a in zip(P.calls, P.alpha)]
P["grid_pow7"] = [SU.power(g, c, a, 7) for c, a in zip(P.calls, P.alpha)]
print("\nstudy's grid-interpolated power vs event-specific: mean pow14 grid", round(P.grid_pow14.mean(), 3), "event-specific", round(P.c14.mean(), 3),
      "; pow7 grid", round(P.grid_pow7.mean(), 3), "event-specific", round(P.c7.mean(), 3))

print("\n=== Cebu monthly mean calls (PortWatch break?) ===")
cebu = rec[(rec.portname == "Cebu")].portid.iloc[0]
mth = calls[cebu].resample("MS").mean()
print(mth["2021-06":"2022-12"].round(2).to_string())
print("Cebu yearly means:", calls[cebu].resample("YS").mean().round(2).to_dict())
