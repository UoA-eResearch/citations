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
    d = pd.read_csv(RUN / "data" / "linked.csv", parse_dates=["t0", "t1", "t2", "t3b", "t3h", "t3", "t3_au", "consent_ended", "t_app", "t_dec", "t_tga", "t_prov"])
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
    # D3.1: funding stage split at the PHARMAC application, and application-based versions of the 7.7-year claim
    fa = pre[pre.t3.notna() & pre.t2.notna() & pre.t_app.notna()]
    fa = fa[(fa.t2 <= fa.t_app) & (fa.t_app <= fa.t3)]
    tot = D(fa.t2, fa.t3)
    out["D3_funding_stage_split"] = dict(n=int(len(fa)), consent_to_application_median_days=float(D(fa.t2, fa.t_app).median()) if len(fa) else None,
                                         application_to_listing_median_days=float(D(fa.t_app, fa.t3).median()) if len(fa) else None,
                                         application_share_of_funding_stage=float(D(fa.t_app, fa.t3).sum() / tot.sum()) if len(fa) else None,
                                         funded_with_application_before_consent=int((pre.t3.notna() & pre.t2.notna() & pre.t_app.notna() & (pre.t_app < pre.t2)).sum()))
    ap = d[d.t_app.notna()].copy()
    dec = ap[ap.t_dec.notna() & (ap.t_dec >= ap.t_app)]
    k_a, med_a, rm_a = km(D(ap.t_app, ap.t_dec.where(ap.t_dec >= ap.t_app).fillna(cutoff)).clip(lower=0), ap.t_dec.notna() & (ap.t_dec >= ap.t_app))
    c2d = d[d.t2.notna()].copy(); c2d = c2d[~(c2d.t_dec.notna() & (c2d.t_dec < c2d.t2))]
    k_b, med_b, rm_b = km(D(c2d.t2, c2d.t_dec.fillna(cutoff)).clip(lower=0), c2d.t_dec.notna())
    dd = c2d[c2d.t_dec.notna()]
    out["D3_H3_application_based_years"] = dict(
        application_to_approval_decided_only=dict(n=int(len(dec)), mean=yrs(float(D(dec.t_app, dec.t_dec).mean())) if len(dec) else None,
                                                  median=yrs(float(D(dec.t_app, dec.t_dec).median())) if len(dec) else None),
        application_to_approval_km=dict(n=int(len(ap)), median=yrs(med_a) if med_a else None, rmst_10y=yrs(rm_a)),
        consent_to_approval_decided_only=dict(n=int(len(dd)), mean=yrs(float(D(dd.t2, dd.t_dec).mean())) if len(dd) else None,
                                              median=yrs(float(D(dd.t2, dd.t_dec).median())) if len(dd) else None),
        consent_to_approval_km=dict(n=int(len(c2d)), median=yrs(med_b) if med_b else None, rmst_10y=yrs(rm_b)))
    # D3.3: regulator benchmark, Medsafe (T2) vs TGA (T_TGA), whole cohort
    tga_cut = min(cutoff, d.t_tga.max()) if d.t_tga.notna().any() else cutoff
    both = d[d.t2.notna() & d.t_tga.notna()]
    kn, mn, _ = km(D(d.t0, d.t2.where(d.t2 <= tga_cut).fillna(tga_cut)).clip(lower=0), d.t2.notna() & (d.t2 <= tga_cut))
    ka, ma, _ = km(D(d.t0, d.t_tga.where(d.t_tga <= tga_cut).fillna(tga_cut)).clip(lower=0), d.t_tga.notna() & (d.t_tga <= tga_cut))
    sh = lambda k, t: float(1 - k.survival_function_at_times(t).iloc[0])
    out["D3_TGA_benchmark"] = dict(cutoff=str(tga_cut.date()), n=int(len(d)), both=int(len(both)),
                                   median_medsafe_minus_tga_days=float(D(both.t_tga, both.t2).median()) if len(both) else None,
                                   nz_km_median_days=mn, au_km_median_days=ma,
                                   nz_by_2y=sh(kn, 730), au_by_2y=sh(ka, 730), nz_by_5y=sh(kn, 1826), au_by_5y=sh(ka, 1826))
    # competing risks: funding vs consent ended before funding
    cr = c2.copy()
    end = cr.t3.where(cr.t3.notna(), cr.consent_ended.where(cr.consent_ended.notna() & (cr.consent_ended <= cutoff)))
    cr["event"] = np.where(cr.t3.notna(), 1, np.where(cr.consent_ended.notna() & (cr.consent_ended <= cutoff), 2, 0))
    cr["dur"] = D(cr.t2, end.fillna(cutoff)).clip(lower=0)
    aj = AalenJohansenFitter(seed=SEED).fit(cr.dur, cr.event, event_of_interest=1)
    ci_at = lambda t: float(aj.cumulative_density_.loc[:t].iloc[-1, 0]) if (aj.cumulative_density_.index <= t).any() else 0.0
    out["competing_risks"] = dict(n=int(len(cr)), funded=int((cr.event == 1).sum()), consent_ended_first=int((cr.event == 2).sum()),
                                  cif_funded_5y=ci_at(1826), cif_funded_10y=ci_at(3652))
    # stage split among funded substances with T1, by T0 period. D8 (review issue 3): a sponsor that applied in NZ before
    # the first FDA/EMA approval has a sponsor delay of 0 (T1 clipped at T0), not exclusion
    st = d[d.t3.notna() & d.t1.notna() & d.t2.notna()].copy()
    out["stage_early_filers"] = int((st.t1 < st.t0).sum())
    st["t1c"] = st[["t1", "t0"]].max(axis=1)
    st = st[(st.t0 <= st.t2) & (st.t1c <= st.t2) & (st.t2 <= st.t3)].copy()
    st["period"] = pd.cut(st.t0.dt.year, [2009, 2014, 2019, 2023, 2024], labels=["2010-14", "2015-19", "2020-23", "2024"])
    rows = []
    for p, g in list(st.groupby("period", observed=True)) + [("all 2010-23", st[st.t0.dt.year <= 2023])]:
        a, b_, c_ = D(g.t0, g.t1c), D(g.t1c, g.t2), D(g.t2, g.t3); tot = D(g.t0, g.t3)
        rows.append(dict(period=str(p), n=len(g), sponsor_median=a.median(), medsafe_median=b_.median(), funding_median=c_.median(),
                         total_median=tot.median(), sponsor_share=a.sum() / tot.sum(), medsafe_share=b_.sum() / tot.sum(),
                         funding_share=c_.sum() / tot.sum()))
    pd.DataFrame(rows).to_csv(TAB / "stage_table.csv", index=False)
    out["stage_split"] = rows
    s23 = st[st.t0.dt.year <= 2023]
    shr = lambda x, a, b: float(D(x[a], x[b]).sum() / D(x.t0, x.t3).sum()) if len(x) else None
    out["decomposition_one_population"] = dict(
        n=int(len(s23)), regulatory_T0_T2=shr(s23, "t0", "t2"), regulatory_ci=boot(s23, lambda x: shr(x, "t0", "t2")),
        sponsor=shr(s23, "t0", "t1c"), sponsor_ci=boot(s23, lambda x: shr(x, "t0", "t1c")),
        medsafe=shr(s23, "t1c", "t2"), medsafe_ci=boot(s23, lambda x: shr(x, "t1c", "t2")),
        funding=shr(s23, "t2", "t3"), funding_ci=boot(s23, lambda x: shr(x, "t2", "t3")))
    # provisional consent lower bound (review issue 4): T2 no later than the first Section 23 application
    pv = clean.copy()
    pv["t2"] = pv[["t2", "t_prov"]].min(axis=1)
    out["H1a_provisional_lower_bound"] = dict(n_with_section23=int(clean.t_prov.notna().sum()), aggregate=share(pv))
    # H3 context (review issues 1-2)
    rm_h = {}
    for tau in (1826, 2812, 3652, 4383):
        rm_h[str(round(tau / 365.25, 1))] = yrs(float(np.trapz(k.survival_function_at_times(np.arange(0, tau + 1)).values, dx=1)))
    ap2 = ap[ap.t_dec.notna() & (ap.t_dec >= ap.t_app)].copy()
    ap2["dy"] = ap2.t_dec.dt.year
    out["H3_context"] = dict(rmst_by_horizon_years=rm_h,
                             funded_T2_T3_ge7y=int((D(f2.t2, f2.t3) >= 7 * 365.25).sum()),
                             funded_T2_T3_7_to_10y=int(((D(f2.t2, f2.t3) >= 7 * 365.25) & (D(f2.t2, f2.t3) < 10 * 365.25)).sum()),
                             funded_T2_T3_gt10y=int((D(f2.t2, f2.t3) >= 10 * 365.25).sum()), funded_n=int(len(f2)),
                             unfunded_at_7y_km=float(k.survival_function_at_times(2557).iloc[0]),
                             funded_T2_T3_mean_days=float(D(f2.t2, f2.t3).mean()),
                             decided_app_to_approval_by_decision_year={str(lab): dict(n=int(len(g)), mean=yrs(float(D(g.t_app, g.t_dec).mean())),
                                                                                      median=yrs(float(D(g.t_app, g.t_dec).median())))
                                                                       for lab, g in ap2.groupby(pd.cut(ap2.dy, [2000, 2021, 2023, 2026], labels=["to 2021", "2022-23", "2024-26"]), observed=True)})
    t24 = d[d.t0.dt.year == 2024]
    out["t0_2024"] = dict(n=int(len(t24)), consented=int(t24.t2.notna().sum()), funded=int(t24.t3.notna().sum()))
    out["excluded_hml_first_edition"] = int(pd.read_csv(RUN / "data" / "linked.csv").get("hml_first_edition", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
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
