"""Preregistered analysis (plan.md sections 3-5).

Primary: OLS on site-weeks, AI ~ week FE + zDep + sampler + log pop + z65 + region FE, SEs clustered by site.
H1 ratio exp(b_zDep): Supported if <= 0.85 and CI excludes 1; Contradicted if CI lower bound > 0.85.
H2: zDep x post (weeks ending >= 2023-08-20), with post x covariates; Supported if < 0 and CI excludes 0;
Contradicted if CI lower bound > 0.
Outputs: results/tables/analysis_sites.csv, main_results.csv, loro.csv, site_effects.csv; results/figures/site_effects.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RUN = Path(__file__).resolve().parents[1]
R = RUN / "data" / "raw" / "covid_in_wastewater"
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
POST = pd.Timestamp("2023-08-20")
Z = 1.959964


def load(lag=0, window=("2022-03-01", "2024-06-30"), folder="data_historic"):
    c = pd.read_csv(R / folder / "cases_site.csv", parse_dates=["week_end_date"])
    w = pd.read_csv(R / folder / "ww_site.csv", parse_dates=["week_end_date"])
    if lag:
        w = w.assign(week_end_date=w.week_end_date + pd.Timedelta(weeks=lag))
    m = c.merge(w, on=["week_end_date", "SampleLocation"])
    m = m[(m.week_end_date >= window[0]) & (m.week_end_date <= window[1])]
    m = m[m.case_7d_avg.notna() & m.copies_per_day_per_person.notna() & (m.copies_per_day_per_person > 0)]
    return m


def sample(m, pop_tol=0.25, min_weeks=30):
    k = pd.read_csv(RUN / "data" / "catchments.csv")
    k = k[k.name_match & (k.pop_ratio >= 1 - pop_tol) & (k.pop_ratio <= 1 + pop_tol)]
    n = m.groupby("SampleLocation").size()
    k = k[k.SampleLocation.map(n).fillna(0) >= min_weeks].copy()
    k["zdep"] = (k.nzdep_w - k.nzdep_w.mean()) / k.nzdep_w.std()
    k["z65"] = (k.p65 - k.p65.mean()) / k.p65.std()
    k["logpop"] = np.log(k.esr_pop)
    small = k.Region.value_counts()
    k["region"] = k.Region.where(k.Region.map(small) >= 3, "small regions")
    d = m.merge(k, on="SampleLocation")
    d["ai"] = np.log((7 * d.case_7d_avg + 0.5) / d.esr_pop * 1e5) - np.log(d.copies_per_day_per_person)
    d["post"] = (d.week_end_date >= POST).astype(int)
    d["week"] = d.week_end_date.dt.strftime("%Y-%m-%d")
    return d, k


COV = "C(sampler) + logpop + z65 + C(region)"


def ols(d, f):
    return smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.SampleLocation)[0]})


def h1(d, label, cov=COV):
    m = ols(d, f"ai ~ C(week) + zdep + {cov}")
    b, se = m.params["zdep"], m.bse["zdep"]
    return dict(analysis=label, est="ratio per 1 SD NZDep", value=np.exp(b), lo=np.exp(b - Z * se),
                hi=np.exp(b + Z * se), b=b, se=se, n_sites=d.SampleLocation.nunique(), n_weeks=len(d))


def h2(d, label):
    f = ("ai ~ C(week) + zdep + C(sampler) + logpop + z65 + C(region) + zdep:post + C(sampler):post + logpop:post"
         " + z65:post")
    m = ols(d, f)
    b, se = m.params["zdep:post"], m.bse["zdep:post"]
    return dict(analysis=label, est="zDep x post (log scale)", value=b, lo=b - Z * se, hi=b + Z * se, b=b, se=se,
                n_sites=d.SampleLocation.nunique(), n_weeks=len(d))


def v1(r):
    if r["value"] <= 0.85 and r["hi"] < 1:
        return "Supported"
    if r["lo"] > 0.85:
        return "Contradicted"
    return "Inconclusive"


def v2(r):
    if r["value"] < 0 and r["hi"] < 0:
        return "Supported"
    if r["lo"] > 0:
        return "Contradicted"
    return "Inconclusive"


def main():
    m = load()
    d, k = sample(m)
    k.to_csv(TAB / "analysis_sites.csv", index=False)
    print("sites", d.SampleLocation.nunique(), "site-weeks", len(d), "regions", k.region.value_counts().to_dict())
    rows = []
    r = h1(d, "PRIMARY H1"); r["verdict"] = v1(r); rows.append(r)
    r = h2(d, "PRIMARY H2"); r["verdict"] = v2(r); rows.append(r)
    # secondary
    mm = smf.mixedlm(f"ai ~ C(week) + zdep + {COV}", d, groups=d.SampleLocation).fit(reml=True)
    b, se = mm.params["zdep"], mm.bse["zdep"]
    rows.append(dict(analysis="mixed model (random site intercept)", est="ratio per 1 SD NZDep", value=np.exp(b),
                     lo=np.exp(b - Z * se), hi=np.exp(b + Z * se), b=b, se=se, n_sites=d.SampleLocation.nunique()))
    d["cases_w"] = np.round(7 * d.case_7d_avg).astype(int)
    d["off"] = np.log(d.copies_per_day_per_person * d.esr_pop)
    # negative binomial (D1): the direct NB2 MLE with ~120 week dummies did not converge, so alpha is estimated
    # from a Poisson fit (Cameron-Trivedi auxiliary regression) and the NB GLM is fitted with that alpha
    import statsmodels.api as sm
    g = groups = pd.factorize(d.SampleLocation)[0]
    fpo = smf.glm(f"cases_w ~ C(week) + zdep + {COV}", d, family=sm.families.Poisson(), offset=d.off).fit()
    mu = fpo.mu
    alpha = float(sm.OLS(((d.cases_w - mu) ** 2 - d.cases_w) / mu, mu).fit().params.iloc[0])
    nb = smf.glm(f"cases_w ~ C(week) + zdep + {COV}", d, family=sm.families.NegativeBinomial(alpha=max(alpha, 1e-6)),
                 offset=d.off).fit(cov_type="cluster", cov_kwds={"groups": g})
    b, se = nb.params["zdep"], nb.bse["zdep"]
    rows.append(dict(analysis=f"negative binomial on weekly cases (offset log copies x pop; alpha {alpha:.3f})",
                     est="ratio per 1 SD NZDep", value=np.exp(b), lo=np.exp(b - Z * se), hi=np.exp(b + Z * se), b=b,
                     se=se, n_sites=d.SampleLocation.nunique()))
    rows.append(h1(d[d.sampler == "Autosampler"], "autosampler sites only"))
    dl, _ = sample(load(lag=1))
    rows.append(h1(dl, "wastewater lagged 1 week"))
    d15, _ = sample(m, pop_tol=0.15)
    rows.append(h1(d15, "population rule +/-15%"))
    for lab, msk in [("before 20 Aug 2023", d.post == 0), ("from 20 Aug 2023", d.post == 1)]:
        rows.append(h1(d[msk], f"period: {lab}"))
    for lab, lo_, hi_ in [("2022 H1", "2022-03-01", "2022-06-30"), ("2022 H2", "2022-07-01", "2022-12-31"),
                          ("2023 H1", "2023-01-01", "2023-06-30"), ("2023 H2", "2023-07-01", "2023-12-31"),
                          ("2024 H1", "2024-01-01", "2024-06-30")]:
        q = d[(d.week_end_date >= lo_) & (d.week_end_date <= hi_)]
        rows.append(h1(q, f"calendar half {lab}"))
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "main_results.csv", index=False)
    print(res[["analysis", "value", "lo", "hi", "n_sites"]].round(3).to_string(index=False))
    print("verdicts:", res.dropna(subset=["verdict"])[["analysis", "verdict"]].values.tolist() if "verdict" in res else "")
    lo = []
    for reg in sorted(d.Region.unique()):
        q = d[d.Region != reg]
        lo.append(dict(left_out=reg, **{k_: v for k_, v in h1(q, reg).items() if k_ in ("value", "lo", "hi", "n_sites")}))
    lo = pd.DataFrame(lo); lo.to_csv(TAB / "loro.csv", index=False)
    print("leave-one-region-out range:", lo.value.min().round(3), "-", lo.value.max().round(3))

    # site effects plot: site mean of week-demeaned AI vs deprivation
    d["ai_dm"] = d.ai - d.groupby("week").ai.transform("mean")
    se_ = d.groupby("SampleLocation").agg(ai=("ai_dm", "mean"), n=("ai", "size")).join(k.set_index("SampleLocation")[["nzdep_w", "sampler", "DisplayName"]])
    se_.to_csv(TAB / "site_effects.csv")
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for smp, col in [("Autosampler", "#2f5d8a"), ("Grab", "#d08a2c")]:
        s = se_[se_.sampler == smp]
        ax.scatter(s.nzdep_w, s.ai, s=12 + s.n / 4, color=col, alpha=0.75, label=smp, edgecolor="white", lw=0.5)
    b = np.polyfit(se_.nzdep_w, se_.ai, 1)
    xs = np.linspace(se_.nzdep_w.min(), se_.nzdep_w.max(), 10)
    ax.plot(xs, np.polyval(b, xs), color="#555", lw=1)
    ax.set_xlabel("catchment NZDep2023 score (population-weighted; higher = more deprived)")
    ax.set_ylabel("ascertainment index\n(site mean, week-demeaned, log)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "site_effects.png", dpi=150)


if __name__ == "__main__":
    main()
