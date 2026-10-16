"""Post-hoc checks, written after the preregistered results were seen (deviations D7). None changes a verdict.

The preregistered results say ports carrying more of their country's imports, and small-island ports, are LESS
often detectably disrupted. Part A controls detectability with log mean daily calls, a straight line; but the
simulation (detectability.py) shows detection power is a steep threshold in traffic - near zero for a week-long
closure below one call a day, near one above two. A straight line cannot absorb a threshold, so the negative
coefficients could be detectability leaking through. Three checks:

  S1  each event's power: the chance the method detects a 7-day and a 14-day closure at that port, interpolated
      from the simulation grid at the port's mean calls and the dispersion fitted for the event
  S2  part A refitted with logit(power for a 7-day closure) in place of log mean calls
  S3  part A refitted on events where a 7-day closure would be caught >= 80% of the time

Also writes the Pacific case series (every Pacific event in the primary arm, with the shortest closure the method
could have seen at that port) and a per-storm table of the small-island events.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def power_table():
    g = pd.DataFrame(json.load(open(TAB / "detectability.json"))["grid"])
    return g


def power(g, mu, alpha, L):
    """Detection probability for a closure of L days, interpolated in log(mu) at the nearer simulated dispersion."""
    a = 0.25 if (not np.isfinite(alpha) or alpha < np.sqrt(0.25 * 1.0)) else 1.0
    s = g[(g.alpha == a) & (g.closure_days == L)].sort_values("mu")
    return float(np.interp(np.log(mu), np.log(s.mu), s.p_detect))


def shortest80(g, mu, alpha):
    a = 0.25 if (not np.isfinite(alpha) or alpha < 0.5) else 1.0
    for L in sorted(g.closure_days.unique()):
        if L > 0 and power(g, mu, a, L) >= 0.8:
            return int(L)
    return None


def fit_a(r, covs):
    X = sm.add_constant(r[covs].astype(float))
    return sm.Logit(r.D_.astype(float), X).fit(disp=0, cov_type="cluster",
                                                cov_kwds={"groups": r.sid.astype("category").cat.codes})


def coef(m, term):
    ci = m.conf_int().loc[term]
    return dict(coef=float(m.params[term]), lo=float(ci[0]), hi=float(ci[1]), p=float(m.pvalues[term]))


def main():
    g = power_table()
    r = A.load("primary")
    r["pow7"] = [power(g, m, a, 7) for m, a in zip(r.mean_calls, r.alpha)]
    r["pow14"] = [power(g, m, a, 14) for m, a in zip(r.mean_calls, r.alpha)]
    r["logit_pow7"] = np.log(r.pow7.clip(0.01, 0.99) / (1 - r.pow7.clip(0.01, 0.99)))
    out = {}
    out["S1_power"] = {name: dict(n=int(len(d)), mean_pow7=float(d.pow7.mean()), mean_pow14=float(d.pow14.mean()),
                                  share_pow7_ge_80=float((d.pow7 >= 0.8).mean()), share_disrupted=float(d.D_.mean()))
                       for name, d in (("sids", r[r.sids == 1]), ("non_sids", r[r.sids == 0]))}
    covs_pow = ["log_size", "logit_pow7", "cat", "closest_100km"]
    s2 = {}
    for term in ("share", "sids"):
        m0 = fit_a(r, A.BASE + [term])
        m1 = fit_a(r, covs_pow + [term])
        s2[term] = dict(preregistered_control=coef(m0, term), power_control=coef(m1, term),
                        aic_log_activity=float(m0.aic), aic_power=float(m1.aic))
    out["S2_power_as_control"] = s2
    hp = r[r.pow7 >= 0.8]
    s3 = dict(n=int(len(hp)), storms=int(hp.sid.nunique()), n_sids=int(hp.sids.sum()),
              n_sids_disrupted=int((hp.D_ & (hp.sids == 1)).sum()),
              share_disrupted_sids=float(hp[hp.sids == 1].D_.mean()) if hp.sids.sum() else None,
              share_disrupted_non_sids=float(hp[hp.sids == 0].D_.mean()))
    try:
        s3["share"] = coef(fit_a(hp, A.BASE + ["share"]), "share")
    except Exception as e:
        s3["share"] = dict(error=str(e))
    out["S3_high_power_only"] = s3
    out["external_check"] = dict(
        non_sids_median_T_disrupted=float(r[(r.sids == 0) & r.D_].T_.median()),
        non_sids_p90_T_disrupted=float(r[(r.sids == 0) & r.D_].T_.quantile(0.9)),
        verschuur_2020=dict(median_days=6, p95_days=22.2, source="Transp. Res. D 85:102393, AIS, 74 ports"))
    json.dump(out, open(TAB / "supplementary.json", "w"), indent=1)
    print(json.dumps(out, indent=1))

    # Pacific case series: every Pacific event in the primary arm, computed or not
    allr = pd.read_csv(TAB / "recovery_events.csv")
    pac = allr[allr.pict & (allr.cat_at_closest >= 3) & (allr.closest_km <= 150)].copy()
    pac["shortest_closure_seen_80pct"] = [shortest80(g, m, a) if m >= 0.25 else None
                                          for m, a in zip(pac.mean_calls, pac.alpha.fillna(0.25))]
    # below the simulated range (0.25 calls/day) np.interp would clamp to the grid's lowest row and overstate
    # power, so those ports get no number - their power for a 14-day closure is below 0.38 and falls with traffic
    pac["pow14"] = [power(g, m, a, 14) if m >= g.mu.min() else np.nan
                    for m, a in zip(pac.mean_calls, pac.alpha.fillna(0.25))]
    keep = ["portname", "ISO3", "storm", "date", "cat_at_closest", "closest_km", "mean_calls", "status",
            "shortest_closure_seen_80pct", "pow14", "depth_min_ratio", "depth_crit", "disrupted", "T"]
    pac[keep].sort_values(["date", "closest_km"]).to_csv(TAB / "pacific_case_series.csv", index=False)
    print(pac[keep].sort_values(["date", "closest_km"]).round(2).to_string(index=False))
    sids = allr[allr.sids & (allr.cat_at_closest >= 3) & (allr.closest_km <= 150)]
    per_storm = sids.groupby("storm").agg(events=("portid", "size"), computed=("status", lambda s: int((s == "ok").sum())),
                                          disrupted=("disrupted", lambda s: int((s == True).sum())))  # noqa: E712
    per_storm.to_csv(TAB / "sids_by_storm.csv")
    print(per_storm.to_string())


if __name__ == "__main__":
    sys.exit(main())
