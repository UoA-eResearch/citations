"""Primary and secondary analyses, as preregistered (plan section 5-6). Reads data/linked.csv. Writes
results/tables/primary.json and results/tables/stage_table.csv.

Population: cohort substances not excluded as old (D2.2). Cutoff: the latest community Schedule edition
(data/linked.csv carries no cutoff; it is read from data/pharmac_listings.csv). Days throughout.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import AalenJohansenFitter, KaplanMeierFitter

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
NB, SEED = 2000, 20261020
D = lambda a, b: (b - a).dt.days


def load():
    d = pd.read_csv(RUN / "data" / "linked.csv", parse_dates=["t0", "t1", "t2", "t3b", "t3h", "t3", "t3_au", "consent_ended"])
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", usecols=["edition", "source"])
    cutoff = pd.to_datetime(L[L.source == "schedule"].edition).max()
    d = d[~d.excluded_old].copy()
    d.loc[d.t3 > cutoff, "t3"] = pd.NaT
    return d, cutoff


def boot(df, fn):
    rng = np.random.default_rng(SEED)
    v = [fn(df.iloc[rng.integers(0, len(df), len(df))]) for _ in range(NB)]
    v = [x for x in v if x is not None and np.isfinite(x)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else [None, None]


def km(dur, event):
    k = KaplanMeierFitter().fit(dur, event)
    med = k.median_survival_time_
    rm = float(np.trapz(k.survival_function_at_times(np.arange(0, 3653)).values, dx=1)) if len(dur) else None
    return k, (float(med) if np.isfinite(med) else None), rm


def main():
    d, cutoff = load()
    out = dict(cutoff=str(cutoff.date()), n_cohort=int(len(d)), n_excluded_old=None)
    out["n_excluded_old"] = int(pd.read_csv(RUN / "data" / "linked.csv").excluded_old.sum())
    pre = d[d.t0.dt.year <= 2023]
    funded = pre[pre.t3.notna()]
    clean = funded[funded.t2.notna() & (funded.t0 <= funded.t2) & (funded.t2 <= funded.t3)].copy()
    out["H1_population"] = dict(t0_2010_2023=int(len(pre)), funded=int(len(funded)), used=int(len(clean)),
                                funded_before_consent=int((funded.t2.notna() & (funded.t3 < funded.t2)).sum()),
                                funded_without_consent=int(funded.t2.isna().sum()),
                                consent_before_t0=int((funded.t2.notna() & (funded.t2 < funded.t0)).sum()))
    share = lambda x: float(D(x.t0, x.t2).sum() / D(x.t0, x.t3).sum()) if len(x) else None
    s, ci = share(clean), boot(clean, share)
    out["H1a_regulatory_share"] = dict(aggregate=s, ci=ci, median_per_substance=float((D(clean.t0, clean.t2) / D(clean.t0, clean.t3).clip(lower=1)).median()),
                                       verdict="Supported" if ci[1] < 0.25 else "Refuted" if ci[0] > 0.25 else "Inconclusive")
    med = lambda x: float(D(x.t0, x.t3).median()) if len(x) else None
    m, mci = med(clean), boot(clean, med)
    out["H1b_median_total_days"] = dict(median=m, ci=mci, funded_all_median=med(funded),
                                        verdict="Supported" if (m >= 1500 and mci[0] >= 1350) else "Refuted" if mci[1] < 1500 else "Inconclusive")
    # H3: three denominators for T2 -> T3 (years) and T0 -> T3
    c2 = d[d.t2.notna()].copy()
    c2 = c2[~(c2.t3.notna() & (c2.t3 < c2.t2))]
    f2 = c2[c2.t3.notna()]
    yrs = lambda x: x / 365.25
    dur = D(c2.t2, c2.t3.fillna(cutoff)).clip(lower=0); ev = c2.t3.notna()
    k, kmed, rm = km(dur, ev)
    k0, kmed0, rm0 = km(D(d.t0, d.t3.fillna(cutoff)).clip(lower=0), d.t3.notna())
    out["H3_denominators_T2_T3_years"] = dict(
        funded_only=dict(n=int(len(f2)), mean=yrs(float(D(f2.t2, f2.t3).mean())), median=yrs(float(D(f2.t2, f2.t3).median()))),
        consented_km=dict(n=int(len(c2)), events=int(ev.sum()), median=yrs(kmed) if kmed else None, rmst_10y=yrs(rm),
                          funded_by_5y=float(1 - k.survival_function_at_times(1826).iloc[0]),
                          funded_by_10y=float(1 - k.survival_function_at_times(3652).iloc[0])),
        all_cohort_T0_T3_km=dict(n=int(len(d)), events=int(d.t3.notna().sum()), median=yrs(kmed0) if kmed0 else None,
                                 rmst_10y=yrs(rm0)))
    h = out["H3_denominators_T2_T3_years"]
    near = lambda v: v is not None and abs(v - 7.7) <= 1
    funded_hit = near(h["funded_only"]["mean"]) or near(h["funded_only"]["median"])
    cens_hit = near(h["consented_km"]["median"]) or near(h["consented_km"]["rmst_10y"])
    h["verdict"] = "Supported" if (funded_hit and not cens_hit) else "Refuted"
    h["other_claims"] = dict(days_1050_funded_median_T2_T3=float(D(f2.t2, f2.t3).median()),
                             years_7_to_10=dict(funded_mean_in_range=bool(7 <= h["funded_only"]["mean"] <= 10)))
    # competing risks: funding vs consent ended before funding
    cr = c2.copy()
    end = cr.t3.where(cr.t3.notna(), cr.consent_ended.where(cr.consent_ended.notna() & (cr.consent_ended <= cutoff)))
    cr["event"] = np.where(cr.t3.notna(), 1, np.where(cr.consent_ended.notna() & (cr.consent_ended <= cutoff), 2, 0))
    cr["dur"] = D(cr.t2, end.fillna(cutoff)).clip(lower=0)
    aj = AalenJohansenFitter(seed=SEED).fit(cr.dur, cr.event, event_of_interest=1)
    ci_at = lambda t: float(aj.cumulative_density_.loc[:t].iloc[-1, 0]) if (aj.cumulative_density_.index <= t).any() else 0.0
    out["competing_risks"] = dict(n=int(len(cr)), funded=int((cr.event == 1).sum()), consent_ended_first=int((cr.event == 2).sum()),
                                  cif_funded_5y=ci_at(1826), cif_funded_10y=ci_at(3652))
    # stage split among funded substances with T1, by T0 period
    st = d[d.t3.notna() & d.t1.notna() & d.t2.notna()]
    st = st[(st.t0 <= st.t1) & (st.t1 <= st.t2) & (st.t2 <= st.t3)].copy()
    st["period"] = pd.cut(st.t0.dt.year, [2009, 2014, 2019, 2023, 2024], labels=["2010-14", "2015-19", "2020-23", "2024"])
    rows = []
    for p, g in list(st.groupby("period", observed=True)) + [("all 2010-23", st[st.t0.dt.year <= 2023])]:
        a, b_, c_ = D(g.t0, g.t1), D(g.t1, g.t2), D(g.t2, g.t3); tot = D(g.t0, g.t3)
        rows.append(dict(period=str(p), n=len(g), sponsor_median=a.median(), medsafe_median=b_.median(), funding_median=c_.median(),
                         total_median=tot.median(), sponsor_share=a.sum() / tot.sum(), medsafe_share=b_.sum() / tot.sum(),
                         funding_share=c_.sum() / tot.sum()))
    pd.DataFrame(rows).to_csv(TAB / "stage_table.csv", index=False)
    out["stage_split"] = rows
    # H2: Australia, T0 2019-2024
    au = d[(d.t0.dt.year >= 2019) & (d.t0.dt.year <= 2024)].copy()
    au_cut = min(cutoff, pd.Timestamp("2026-10-01"))
    nz_k, nz_med, _ = km(D(au.t0, au.t3.where(au.t3 <= au_cut).fillna(au_cut)).clip(lower=0), au.t3.notna() & (au.t3 <= au_cut))
    au_k, au_med, _ = km(D(au.t0, au.t3_au.where(au.t3_au <= au_cut).fillna(au_cut)).clip(lower=0), au.t3_au.notna() & (au.t3_au <= au_cut))
    h2 = dict(n=int(len(au)), nz_events=int((au.t3.notna() & (au.t3 <= au_cut)).sum()), au_events=int((au.t3_au.notna() & (au.t3_au <= au_cut)).sum()),
              nz_median=nz_med, au_median=au_med,
              nz_listed_by_3y=float(1 - nz_k.survival_function_at_times(1096).iloc[0]),
              au_listed_by_3y=float(1 - au_k.survival_function_at_times(1096).iloc[0]))
    if nz_med and au_med:
        def diff(x):
            a_ = km(D(x.t0, x.t3.where(x.t3 <= au_cut).fillna(au_cut)).clip(lower=0), x.t3.notna() & (x.t3 <= au_cut))[1]
            b2 = km(D(x.t0, x.t3_au.where(x.t3_au <= au_cut).fillna(au_cut)).clip(lower=0), x.t3_au.notna() & (x.t3_au <= au_cut))[1]
            return (a_ - b2) if (a_ and b2) else None
        h2["difference"] = nz_med - au_med; h2["ci"] = boot(au, diff)
        h2["verdict"] = ("Supported" if h2["difference"] >= 400 and h2["ci"][0] > 0 else "Refuted" if h2["ci"][1] < 400 else "Inconclusive")
    else:
        h2["verdict"] = "not testable as stated (median not reached)"
    out["H2_australia"] = h2
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("H1_population", "H1a_regulatory_share", "H1b_median_total_days", "H2_australia")}, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
