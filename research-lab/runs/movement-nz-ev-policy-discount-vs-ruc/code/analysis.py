"""The two shocks, as preregistered (plan sections 3 and 4).

Reads data/registrations.csv. Writes results/tables/primary.json, monthly.csv and placebos.csv.

  baseline   log(count + 1) on a linear trend and calendar-month effects, fitted 2021-01 to 2023-09 and
             projected forward, separately for the treated group (BEV + PHEV) and the hybrid control
  H1         R = (December 2023 excess) / (January-March 2024 shortfall), both in levels
  H2         Q = |delta_RUC| / |delta_CCD|, where delta_CCD is the treated group's mean log deviation from its
             baseline over January-March 2024 and delta_RUC is a difference-in-differences across 1 April 2024
             against the hybrid control, excluding April as a transition month
  intervals  residual block bootstrap, blocks of three months, 2,000 resamples, seed 20261020. Residuals are
             taken around the fitted baseline before 2023-10 and around each analysis window's own mean after it,
             so post-period noise is estimated rather than assumed away.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B, SEED, BLOCK = 2000, 20261020, 3
FIT_FROM, FIT_TO = (2021, 1), (2023, 9)
BEV = {"ELECTRIC", "ELECTRIC [PETROL EXTENDED]", "ELECTRIC [DIESEL EXTENDED]", "ELECTRIC FUEL CELL OTHER",
       "ELECTRIC FUEL CELL HYDROGEN"}
PHEV = {"PLUGIN PETROL HYBRID", "PLUGIN DIESEL HYBRID", "PLUG IN FUEL CELL HYDROGEN HYBRID",
        "PLUG IN FUEL CELL OTHER HYBRID"}
HEV = {"PETROL HYBRID", "DIESEL HYBRID", "PETROL ELECTRIC HYBRID", "DIESEL ELECTRIC HYBRID"}
ICE = {"PETROL", "DIESEL", "LPG", "CNG", "OTHER"}


def group_of(mp):
    return "BEV" if mp in BEV else "PHEV" if mp in PHEV else "HEV" if mp in HEV else "ICE" if mp in ICE else None


def idx(y, m):
    return y * 12 + (m - 1)


def label(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


def design(ix):
    """Linear trend plus calendar-month effects."""
    ix = np.asarray(ix)
    X = [np.ones(len(ix)), (ix - ix[0]) / 12.0]
    for m in range(1, 12):
        X.append((ix % 12 == m).astype(float))
    return np.column_stack(X)


def main():
    rows = list(csv.DictReader(open(RUN / "data" / "registrations.csv")))
    series = defaultdict(lambda: defaultdict(float))
    for r in rows:
        g = group_of(r["motive_power"])
        if g is None:
            continue
        i, n = idx(int(r["year"]), int(r["month"])), float(r["n"])
        used = "used" if "USED" in r["import_status"].upper() else "new"
        for key in (g, f"{g}|{used}"):
            series[key][i] += n
    months = sorted({i for s in series.values() for i in s})
    months = [i for i in months if idx(*FIT_FROM) <= i <= idx(2026, 9)]
    with open(T / "monthly.csv", "w", newline="") as fh:
        keys = sorted(series)
        w = csv.writer(fh); w.writerow(["month"] + keys)
        for i in months:
            w.writerow([label(i)] + [int(series[k].get(i, 0)) for k in keys])

    fit_ix = [i for i in months if idx(*FIT_FROM) <= i <= idx(*FIT_TO)]
    rng = np.random.default_rng(SEED)

    def fit(key):
        y = np.log(np.array([series[key].get(i, 0) for i in fit_ix]) + 1.0)
        X = design(fit_ix)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        Xall = design(months)
        # the trend/month design must be built on the same origin as the fit
        Xall = np.column_stack([np.ones(len(months)), (np.array(months) - fit_ix[0]) / 12.0]
                               + [(np.array(months) % 12 == m).astype(float) for m in range(1, 12)])
        return beta, resid, Xall

    def stats(y_tr, y_ct, beta_tr, Xall):
        """R, delta_CCD, delta_RUC and Q from one realisation of the two series."""
        pred = Xall @ beta_tr
        lev_pred = np.exp(pred) - 1.0
        pos = {i: k for k, i in enumerate(months)}
        dec = pos[idx(2023, 12)]
        q1 = [pos[idx(2024, m)] for m in (1, 2, 3)]
        post = [pos[idx(2024, m)] for m in (5, 6, 7, 8, 9, 10)]
        E = float((np.exp(y_tr[dec]) - 1.0) - lev_pred[dec])
        M = float(sum(lev_pred[j] - (np.exp(y_tr[j]) - 1.0) for j in q1))
        R = E / M if M > 0 else np.nan
        d_ccd = float(np.mean([y_tr[j] - pred[j] for j in q1]))
        d_ruc = float(np.mean(y_tr[post]) - np.mean(y_tr[q1]) - (np.mean(y_ct[post]) - np.mean(y_ct[q1])))
        Q = abs(d_ruc) / abs(d_ccd) if d_ccd != 0 else np.nan
        return R, d_ccd, d_ruc, Q, E, M

    treated = {i: series["BEV"].get(i, 0) + series["PHEV"].get(i, 0) for i in months}
    series["TREATED"] = treated
    beta_tr, res_tr, Xall = fit("TREATED")
    beta_ct, res_ct, _ = fit("HEV")
    y_tr = np.log(np.array([treated.get(i, 0) for i in months]) + 1.0)
    y_ct = np.log(np.array([series["HEV"].get(i, 0) for i in months]) + 1.0)
    R, d_ccd, d_ruc, Q, E, M = stats(y_tr, y_ct, beta_tr, Xall)

    def fitted_series(y, beta):
        """Baseline fit before 2023-10; afterwards the mean of the month's own analysis window, so that
        month-to-month noise is estimated in the post period too rather than assumed away."""
        fit = (Xall @ beta).copy()
        wins = [[idx(2023, 12)], [idx(2024, m) for m in (1, 2, 3)], [idx(2024, 4)],
                [idx(2024, m) for m in (5, 6, 7, 8, 9, 10)]]
        rest = [i for i in months if i >= idx(2023, 10) and not any(i in w for w in wins)]
        for w in wins + [rest]:
            js = [pos0[i] for i in w if i in pos0]
            if js:
                fit[js] = np.mean(y[js])
        return fit

    pos0 = {i: k for k, i in enumerate(months)}
    fit_tr, fit_ct = fitted_series(y_tr, beta_tr), fitted_series(y_ct, beta_ct)
    res_tr_all, res_ct_all = y_tr - fit_tr, y_ct - fit_ct

    def block_resample(res):
        out = []
        while len(out) < len(months):
            s0 = rng.integers(0, max(len(res) - BLOCK, 1))
            out.extend(res[s0:s0 + BLOCK])
        return np.array(out[:len(months)])

    draws = []
    for _ in range(B):
        yb_tr = fit_tr + block_resample(res_tr_all)
        yb_ct = fit_ct + block_resample(res_ct_all)
        bb, *_ = np.linalg.lstsq(design(fit_ix), yb_tr[:len(fit_ix)], rcond=None)
        draws.append(stats(yb_tr, yb_ct, bb, Xall)[:4])
    D = np.array(draws, dtype=float)

    def ci(col):
        v = D[:, col][np.isfinite(D[:, col])]
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))], float(np.std(v, ddof=1))

    ci_R, se_R = ci(0); ci_ccd, se_ccd = ci(1); ci_ruc, se_ruc = ci(2); ci_Q, se_Q = ci(3)
    out = dict(months=[label(months[0]), label(months[-1])], n_fit_months=len(fit_ix),
               december_2023_excess=E, q1_2024_shortfall=M,
               H1=dict(R=R, ci=ci_R, se=se_R, threshold=0.5,
                       verdict="Supported" if ci_R[0] >= 0.5 else "Refuted" if ci_R[1] < 0.5 else "Inconclusive"),
               delta_ccd=dict(estimate=d_ccd, ci=ci_ccd, pct=100 * (np.exp(d_ccd) - 1)),
               delta_ruc=dict(estimate=d_ruc, ci=ci_ruc, pct=100 * (np.exp(d_ruc) - 1), mde_pct=100 * (np.exp(2.8 * se_ruc) - 1)),
               H2=dict(Q=Q, ci=ci_Q, se=se_Q, threshold=1 / 3,
                       verdict="Supported" if ci_Q[1] < 1 / 3 else "Refuted" if ci_Q[0] >= 1 / 3 else "Inconclusive"))

    # placebos: the same difference-in-differences at 1 April of other years
    pl = []
    pos = {i: k for k, i in enumerate(months)}
    for yr in (2022, 2023, 2025, 2026):
        pre = [pos[idx(yr, m)] for m in (1, 2, 3) if idx(yr, m) in pos]
        post = [pos[idx(yr, m)] for m in (5, 6, 7, 8, 9, 10) if idx(yr, m) in pos]
        if len(pre) < 3 or len(post) < 3:
            continue
        d = float(np.mean(y_tr[post]) - np.mean(y_tr[pre]) - (np.mean(y_ct[post]) - np.mean(y_ct[pre])))
        pl.append(dict(year=yr, delta=d, pct=100 * (np.exp(d) - 1)))
    with open(T / "placebos.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "delta", "pct"]); w.writeheader(); w.writerows(pl)
    out["placebos"] = pl

    # secondary splits
    sec = {}
    for key in ("BEV", "PHEV", "BEV|new", "BEV|used", "PHEV|new", "PHEV|used", "HEV|new", "HEV|used"):
        s = series.get(key)
        if not s:
            continue
        ys = np.log(np.array([s.get(i, 0) for i in months]) + 1.0)
        pre = [pos[idx(2024, m)] for m in (1, 2, 3)]
        post = [pos[idx(2024, m)] for m in (5, 6, 7, 8, 9, 10)]
        sec[key] = dict(ruc_diff_pct=100 * (np.exp(np.mean(ys[post]) - np.mean(ys[pre])) - 1))
    for key in sec:
        base = "HEV|new" if key.endswith("new") else "HEV|used" if key.endswith("used") else "HEV"
        if base in sec:
            sec[key]["vs_hev_pct"] = sec[key]["ruc_diff_pct"] - sec[base]["ruc_diff_pct"]
    out["secondary"] = sec
    out["annual_totals"] = {str(y): int(sum(v for i, v in treated.items() if i // 12 == y)) for y in range(2021, 2027)}
    out["share_treated_pct"] = {label(i): round(100 * treated[i] / max(sum(series[g].get(i, 0) for g in ("BEV", "PHEV", "HEV", "ICE")), 1), 2)
                                for i in months}
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("months", "december_2023_excess", "q1_2024_shortfall", "H1",
                                          "delta_ccd", "delta_ruc", "H2", "placebos")}, indent=1, default=float))


if __name__ == "__main__":
    main()
