"""Models and decision rules, exactly as preregistered in plan.md. Committed before recovery.csv exists.

Recovery is modelled in two parts, because "no detectable disruption" and "how long the disruption lasted" are
different questions, and folding the zeros into one duration model would let the quietest ports - where nothing
can be detected - masquerade as the fastest to recover:

  part A  logistic: disrupted ~ covariates                               (all events)
  part B  Weibull accelerated failure time: recovery days ~ covariates   (disrupted events; censored at 120)

Base covariates in both parts: log port size (PortWatch vessel count), log mean daily calls (a detectability
control - quieter ports show fewer disruptions for statistical reasons alone), cyclone category at closest
approach, and closest-approach distance. Standard errors are clustered by storm, since one storm makes several
events. The two-part AIC is the sum of the parts' AICs.

  H1 (primary)   import concentration: does adding the port's share of national maritime imports improve the
                 two-part fit?  Supported if delta AIC >= 10; Refuted if delta AIC < 2; Inconclusive between.
                 The sign is reported, not presumed: a single-port economy has no backup (slower), but ships
                 cannot divert from it either (faster).
  H2 (secondary) small island states: time ratio exp(b_sids) in part B with the base covariates. Supported if
                 its 95% interval lies above 1 and the point is >= 2 (the lead's factor of two); Refuted if the
                 interval's upper end is below 2; Inconclusive otherwise.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from lifelines import WeibullAFTFitter

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "tables"
BASE = ["log_size", "log_activity", "cat", "closest_100km"]
ARMS = {"primary": (3, 150), "cat1_150km": (1, 150), "cat3_100km": (3, 100), "cat3_250km": (3, 250)}


def load(arm="primary", col_T="T", col_ev="event", col_dis="disrupted"):
    r = pd.read_csv(PROC / "recovery.csv")
    ports = pd.read_csv(RAW / "portwatch" / "ports.csv")[["portid", "vessel_count_total", "share_country_maritime_import"]]
    r = r.merge(ports, on="portid", how="left")
    cat, km = ARMS[arm]
    r = r[(r.status == "ok") & (r.cat_at_closest >= cat) & (r.closest_km <= km)].copy()
    r["log_size"] = np.log(r.vessel_count_total + 1)
    r["log_activity"] = np.log(r.mean_calls)
    r["cat"] = r.cat_at_closest
    r["closest_100km"] = r.closest_km / 100
    r["share"] = r.share_country_maritime_import / 100
    r["sids"] = r.sids.astype(float)
    r["T_"], r["E_"], r["D_"] = r[col_T], r[col_ev], r[col_dis].astype(bool)
    return r


def part_a(r, covs):
    X = sm.add_constant(r[covs].astype(float))
    m = sm.Logit(r.D_.astype(float), X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": r.sid.astype("category").cat.codes})
    return m


def part_b(r, covs):
    d = r[r.D_].copy()
    d["T_"] = d.T_.clip(lower=1.0)                    # a disruption that clears on day 0 counts as one day
    f = WeibullAFTFitter()
    f.fit(d[covs + ["T_", "E_", "sid"]], duration_col="T_", event_col="E_", cluster_col="sid")
    return f


def aic_two_part(r, covs):
    a, b = part_a(r, covs), part_b(r, covs)
    return a.aic + b.AIC_, a, b


def h1(r):
    aic0, a0, b0 = aic_two_part(r, BASE)
    aic1, a1, b1 = aic_two_part(r, BASE + ["share"])
    d = aic0 - aic1
    verdict = "Supported" if d >= 10 else ("Refuted" if d < 2 else "Inconclusive")
    sb = b1.summary.loc[("lambda_", "share")]
    return dict(delta_aic=float(d), verdict=verdict, aic_base=float(aic0), aic_full=float(aic1),
                part_a_share_coef=float(a1.params["share"]), part_a_share_p=float(a1.pvalues["share"]),
                part_b_share_time_ratio=float(np.exp(sb["coef"])),
                part_b_share_tr_ci=[float(np.exp(sb["coef lower 95%"])), float(np.exp(sb["coef upper 95%"]))],
                n_events=int(len(r)), n_disrupted=int(r.D_.sum()), n_storms=int(r.sid.nunique()))


def h2(r):
    b = part_b(r, BASE + ["sids"])
    s = b.summary.loc[("lambda_", "sids")]
    tr, lo, hi = float(np.exp(s["coef"])), float(np.exp(s["coef lower 95%"])), float(np.exp(s["coef upper 95%"]))
    verdict = "Supported" if (lo > 1 and tr >= 2) else ("Refuted" if hi < 2 else "Inconclusive")
    a = part_a(r, BASE + ["sids"])
    return dict(time_ratio=tr, lo=lo, hi=hi, verdict=verdict, disruption_odds_ratio=float(np.exp(a.params["sids"])),
                disruption_or_ci=[float(np.exp(a.conf_int().loc["sids", 0])), float(np.exp(a.conf_int().loc["sids", 1]))],
                n_sids_events=int(r.sids.sum()), n_sids_storms=int(r[r.sids == 1].sid.nunique()))


def describe(r):
    out = {}
    for name, g in (("sids", r[r.sids == 1]), ("non_sids", r[r.sids == 0]), ("pacific", r[r.pict])):
        out[name] = dict(n=int(len(g)), storms=int(g.sid.nunique()), share_disrupted=float(g.D_.mean()) if len(g) else None,
                         median_T_all=float(g.T_.median()) if len(g) else None,
                         median_T_disrupted=float(g[g.D_].T_.median()) if g.D_.any() else None,
                         censored_at_120=int(((g.E_ == 0) & g.D_).sum()))
    return out


def main():
    out = {}
    for arm in ARMS:
        r = load(arm)
        res = dict(describe=describe(r))
        try:
            res["H1"] = h1(r)
        except Exception as e:
            res["H1"] = dict(error=str(e))
        try:
            res["H2"] = h2(r)
        except Exception as e:
            res["H2"] = dict(error=str(e))
        out[arm] = res
    # sensitivities on the primary arm: the 10%-threshold recovery time, and the own-history counterfactual
    r10 = load("primary", col_T="T10", col_ev="event10")
    rown = load("primary", col_T="own_T", col_ev="own_event", col_dis="own_disrupted")
    rown = rown[rown.own_status == "ok"]
    sens = {}
    for name, r in (("T10", r10), ("own_history", rown)):
        try:
            sens[name] = dict(H1=h1(r), H2=h2(r), describe=describe(r))
        except Exception as e:
            sens[name] = dict(error=str(e))
    covid = load("primary")
    covid = covid[~pd.to_datetime(covid.date).between("2020-03-01", "2020-06-30")]
    try:
        sens["excluding_covid_onset"] = dict(H1=h1(covid), H2=h2(covid), describe=describe(covid))
    except Exception as e:
        sens["excluding_covid_onset"] = dict(error=str(e))
    out["sensitivity"] = sens
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    p = out["primary"]
    print("primary arm:", json.dumps(p["describe"], indent=1))
    print("H1:", {k: p["H1"].get(k) for k in ("delta_aic", "verdict", "part_b_share_time_ratio", "part_a_share_coef")})
    print("H2:", {k: p["H2"].get(k) for k in ("time_ratio", "lo", "hi", "verdict")})


if __name__ == "__main__":
    sys.exit(main())
