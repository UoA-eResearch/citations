"""Reviewer checks 3-7: H1 baselines, the bootstrap, H2 and placebos, recovery and ute claims.
Reads the study's data/registrations.csv (counts already verified against the service). numpy + statsmodels.
"""
import csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np
import statsmodels.api as sm

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
BEV = {"ELECTRIC", "ELECTRIC [PETROL EXTENDED]", "ELECTRIC [DIESEL EXTENDED]", "ELECTRIC FUEL CELL OTHER", "ELECTRIC FUEL CELL HYDROGEN"}
PHEV = {"PLUGIN PETROL HYBRID", "PLUGIN DIESEL HYBRID", "PLUG IN FUEL CELL HYDROGEN HYBRID", "PLUG IN FUEL CELL OTHER HYBRID"}
HEV = {"PETROL HYBRID", "DIESEL HYBRID", "PETROL ELECTRIC HYBRID", "DIESEL ELECTRIC HYBRID"}
ICE = {"PETROL", "DIESEL", "LPG", "CNG", "OTHER"}
def grp(mp): return "BEV" if mp in BEV else "PHEV" if mp in PHEV else "HEV" if mp in HEV else "ICE" if mp in ICE else None
def idx(y, m): return y * 12 + m - 1
def lab(i): return f"{i // 12}-{i % 12 + 1:02d}"
S = defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open(RUN / "data" / "registrations.csv")):
    g = grp(r["motive_power"]); i = idx(int(r["year"]), int(r["month"])); n = float(r["n"])
    if g is None: print("UNGROUPED motive power:", r["motive_power"]); continue
    used = "used" if "USED" in r["import_status"].upper() else "new"
    S[g][i] += n; S[f"{g}|{used}"][i] += n; S["MP:" + r["motive_power"]][i] += n
months = list(range(idx(2021, 1), idx(2026, 9) + 1)); pos = {i: k for k, i in enumerate(months)}
A = lambda k: np.array([S[k].get(i, 0.0) for i in months])
TR, HV, IC = A("BEV") + A("PHEV"), A("HEV"), A("ICE"); TOT = TR + HV + IC
print("series check vs results/tables/monthly.csv:", end=" ")
mc = list(csv.DictReader(open(RUN / "results" / "tables" / "monthly.csv")))
bad = sum(1 for r in mc for k in ("BEV", "PHEV", "HEV", "ICE") if int(r[k]) != int(S[k].get(idx(int(r["month"][:4]), int(r["month"][5:])), 0)))
print("mismatches", bad, "| months", len(mc), "| total", int(TOT.sum()))

def X_of(ix, origin):
    ix = np.asarray(ix)
    return np.column_stack([np.ones(len(ix)), (ix - origin) / 12.0] + [(ix % 12 == m).astype(float) for m in range(1, 12)])
DEC, Q1, POST = pos[idx(2023, 12)], [pos[idx(2024, m)] for m in (1, 2, 3)], [pos[idx(2024, m)] for m in (5, 6, 7, 8, 9, 10)]

def h1(y, f0, f1, form, extra=()):
    fix = [i for i in months if f0 <= i <= f1]; X = X_of(fix, fix[0]); Xa = X_of(months, fix[0])
    yf = np.array([y[pos[i]] for i in fix])
    if form == "loglin":
        b, *_ = np.linalg.lstsq(X, np.log(yf + 1), rcond=None); pred = np.exp(Xa @ b) - 1
    elif form == "level":
        b, *_ = np.linalg.lstsq(X, yf, rcond=None); pred = Xa @ b
    elif form == "poisson":
        pred = sm.GLM(yf, X, family=sm.families.Poisson()).fit().predict(Xa)
    elif form == "negbin":
        pred = sm.GLM(yf, X, family=sm.families.NegativeBinomial(alpha=0.1)).fit().predict(Xa)
    E = sum(y[j] - pred[j] for j in [DEC] + list(extra)); M = sum(pred[j] - y[j] for j in Q1)
    return E, M, (E / M if M > 0 else float("nan")), pred

print("\n== H1: R under alternative baselines (treated = BEV+PHEV unless stated)")
print(f"  actual: Dec 2023 {TR[DEC]:,.0f}; Jan-Mar 2024 {TR[Q1].sum():,.0f}; Oct-Nov 2023 {TR[pos[idx(2023,10)]]:,.0f}, {TR[pos[idx(2023,11)]]:,.0f}")
print(f"  {'spec':52s} {'E':>7s} {'M':>8s} {'R':>6s}  pred Dec  pred Q1/mo")
for f0, f0l in ((idx(2021, 1), "2021-01"), (idx(2022, 1), "2022-01")):
    for f1, f1l in ((idx(2023, 9), "2023-09"), (idx(2023, 11), "2023-11")):
        for form in ("loglin", "level", "poisson"):
            E, M, R, pred = h1(TR, f0, f1, form)
            print(f"  {form:8s} fit {f0l}..{f1l}{'':25s} {E:7,.0f} {M:8,.0f} {R:6.2f}  {pred[DEC]:8,.0f}  {pred[Q1].mean():8,.0f}")
E, M, R, _ = h1(TR, idx(2021, 1), idx(2023, 9), "loglin", extra=[pos[idx(2023, 11)]]); print(f"  loglin 2021-01..2023-09, excess incl Nov (prereg sens) {E:7,.0f} {M:8,.0f} {R:6.2f}")
NEW = A("BEV|new") + A("PHEV|new")
for form in ("loglin", "level", "poisson"):
    E, M, R, pred = h1(NEW, idx(2021, 1), idx(2023, 9), form); print(f"  NEW ONLY {form:8s} fit 2021-01..2023-09 (plan s5.1 robustness)  {E:7,.0f} {M:8,.0f} {R:6.2f}  {pred[DEC]:8,.0f}  {pred[Q1].mean():8,.0f}")
# local-level counterfactuals: seasonal factors from the preregistered fit, level anchored on Oct-Nov 2023
fix = [i for i in months if idx(2021, 1) <= i <= idx(2023, 9)]; X = X_of(fix, fix[0])
b, *_ = np.linalg.lstsq(X, np.log(np.array([TR[pos[i]] for i in fix]) + 1), rcond=None)
meff = np.array([0.0] + list(b[2:])); slope = b[1] / 12
for with_trend in (False, True):
    anchor = [pos[idx(2023, 10)], pos[idx(2023, 11)]]
    L = np.mean([np.log(TR[j] + 1) - meff[months[j] % 12] for j in anchor]); t0 = np.mean([months[j] for j in anchor])
    cf = np.array([np.exp(L + meff[months[j] % 12] + (slope * (months[j] - t0) if with_trend else 0)) - 1 for j in range(len(months))])
    E = TR[DEC] - cf[DEC]; M = sum(cf[j] - TR[j] for j in Q1)
    print(f"  local level (Oct-Nov 2023 anchor, fitted month effects{', fitted trend' if with_trend else ', no trend'}) {E:7,.0f} {M:8,.0f} {E/M:6.2f}  {cf[DEC]:8,.0f}  {cf[Q1].mean():8,.0f}")
c = (TR[DEC] + 0.5 * TR[Q1].sum()) / 2.5
print(f"  break-even: a flat counterfactual must be <= {c:,.0f}/month for R >= 0.5 (Oct-Nov 2023 actual averaged {TR[[pos[idx(2023,10)], pos[idx(2023,11)]]].mean():,.0f})")

print("\n== Bootstrap: reproduce the study's scheme, then alternatives")
y_tr, y_ct = np.log(TR + 1), np.log(HV + 1)
fix_ix = [i for i in months if idx(2021, 1) <= i <= idx(2023, 9)]; Xf = X_of(fix_ix, fix_ix[0]); Xall = X_of(months, fix_ix[0])
def fit_beta(y): b, *_ = np.linalg.lstsq(Xf, y[:len(fix_ix)], rcond=None); return b
b_tr, b_ct = fit_beta(y_tr), fit_beta(y_ct)
def stats(ytr, yct, btr):
    pred = Xall @ btr; lp = np.exp(pred) - 1
    E = (np.exp(ytr[DEC]) - 1) - lp[DEC]; M = sum(lp[j] - (np.exp(ytr[j]) - 1) for j in Q1)
    R = E / M if M > 0 else np.nan
    dccd = np.mean([ytr[j] - pred[j] for j in Q1])
    druc = np.mean(ytr[POST]) - np.mean(ytr[Q1]) - (np.mean(yct[POST]) - np.mean(yct[Q1]))
    return R, dccd, druc, abs(druc) / abs(dccd), E, M
R0, dccd0, druc0, Q0, E0, M0 = stats(y_tr, y_ct, b_tr)
print(f"  point: R {R0:.4f} E {E0:,.1f} M {M0:,.1f} d_ccd {dccd0:.4f} ({100*(np.exp(dccd0)-1):.1f}%) d_ruc {druc0:.4f} ({100*(np.exp(druc0)-1):.2f}%) Q {Q0:.4f}")
print(f"  CI endpoints in %: exp({-0.437324309179182:.4f})-1 = {100*(np.exp(-0.437324309179182)-1):.2f}% (report says -36%); upper {100*(np.exp(0.9290617201651374)-1):.1f}%")
def fitted_series(y, beta):
    f = (Xall @ beta).copy()
    wins = [[idx(2023, 12)], [idx(2024, m) for m in (1, 2, 3)], [idx(2024, 4)], [idx(2024, m) for m in (5, 6, 7, 8, 9, 10)]]
    rest = [i for i in months if i >= idx(2023, 10) and not any(i in w for w in wins)]
    for w in wins + [rest]:
        js = [pos[i] for i in w]; f[js] = np.mean(y[js])
    return f
fit_tr, fit_ct = fitted_series(y_tr, b_tr), fitted_series(y_ct, b_ct)
res_tr, res_ct = y_tr - fit_tr, y_ct - fit_ct
n_pre, p = len(fix_ix), Xf.shape[1]
print(f"  residual SD: pre-fit treated {res_tr[:n_pre].std(ddof=0):.3f} (leverage-corrected {res_tr[:n_pre].std(ddof=0)*np.sqrt(n_pre/(n_pre-p)):.3f}, n={n_pre}, p={p}); "
      f"post windows treated {res_tr[n_pre:].std(ddof=0):.3f}; control pre {res_ct[:n_pre].std(ddof=0):.3f} post {res_ct[n_pre:].std(ddof=0):.3f}")
print(f"  Jan-Mar 2024 within-window residuals, treated: {np.round(res_tr[Q1],3)}  (window-mean residuals shrink variance by (n-1)/n; the Dec 2023 residual is exactly {res_tr[DEC]:.3f})")

def run_boot(res_t, res_c, block, B=2000, seed=20261020, circular=False, scheme="study"):
    rng = np.random.default_rng(seed); n = len(months); out = []
    def resample(res):
        o = []
        while len(o) < n:
            if circular:
                s0 = rng.integers(0, len(res)); o.extend(np.take(res, range(s0, s0 + block), mode="wrap"))
            else:
                s0 = rng.integers(0, max(len(res) - block, 1)); o.extend(res[s0:s0 + block])
        return np.array(o[:n])
    for _ in range(B):
        yb_tr = fit_tr + resample(res_t); yb_ct = fit_ct + resample(res_c)
        bb = fit_beta(yb_tr); out.append(stats(yb_tr, yb_ct, bb))
    return np.array(out, dtype=float)
def summarise(D, name):
    R = D[:, 0]; fin = np.isfinite(R)
    ciR = np.percentile(R[fin], [2.5, 97.5]); diff = D[:, 4] - 0.5 * D[:, 5]; cid = np.percentile(diff, [2.5, 97.5])
    ruc = np.percentile(D[:, 2], [2.5, 97.5]); Q = D[:, 3]; ciQ = np.percentile(Q[np.isfinite(Q)], [2.5, 97.5])
    print(f"  {name:58s} R CI [{ciR[0]:6.2f},{ciR[1]:6.2f}] dropped(M<=0) {(~fin).sum():4d}/{len(R)}  P(R>=0.5) {np.mean(R[fin]>=0.5):.3f}  "
          f"(E-0.5M) CI [{cid[0]:7,.0f},{cid[1]:7,.0f}]  d_ruc CI % [{100*(np.exp(ruc[0])-1):5.0f},{100*(np.exp(ruc[1])-1):5.0f}] se {D[:,2].std(ddof=1):.3f}  Q CI [{ciQ[0]:.2f},{ciQ[1]:.2f}]")
    return ciR, ruc, ciQ
D0 = run_boot(res_tr, res_ct, 3); summarise(D0, "study scheme (block 3, mixed residuals) - reproduction")
D0c = run_boot(res_tr, res_ct, 3, circular=True); summarise(D0c, "study scheme, circular blocks")
infl = np.sqrt(n_pre / (n_pre - p))
pre_t, pre_c = res_tr[:n_pre] * infl, res_ct[:n_pre] * infl
for blk in (1, 3, 6, 12):
    D = run_boot(pre_t, pre_c, blk, circular=True); summarise(D, f"pre-period fit residuals only, leverage-inflated, block {blk}")
D = run_boot(res_tr[:n_pre], res_ct[:n_pre], 3, circular=True); summarise(D, "pre-period fit residuals only, NOT inflated, block 3")
# residual autocorrelation (is a 3-month block enough?)
def acf(x, k): x = x - x.mean(); return float(np.sum(x[k:] * x[:-k]) / np.sum(x * x))
print("  pre-fit residual ACF treated lag1..4:", [round(acf(res_tr[:n_pre], k), 2) for k in (1, 2, 3, 4)], " control:", [round(acf(res_ct[:n_pre], k), 2) for k in (1, 2, 3, 4)])

print("\n== H2: components, pre-trend, alternative controls / windows / outcomes")
def did(tr, ct, pre, post): return np.mean(np.log(tr[post] + 1)) - np.mean(np.log(tr[pre] + 1)) - (np.mean(np.log(ct[post] + 1)) - np.mean(np.log(ct[pre] + 1)))
pct = lambda d: 100 * (np.exp(d) - 1)
print(f"  treated Jan-Mar 2024 mean {TR[Q1].mean():,.0f} -> May-Oct 2024 mean {TR[POST].mean():,.0f} ({pct(np.mean(y_tr[POST])-np.mean(y_tr[Q1])):+.0f}% in logs); "
      f"hybrids {HV[Q1].mean():,.0f} -> {HV[POST].mean():,.0f} ({pct(np.mean(y_ct[POST])-np.mean(y_ct[Q1])):+.0f}%)")
print(f"  pre-trend inside the pre window: treated Jan->Feb->Mar 2024 = {TR[Q1].astype(int).tolist()} (log slope {np.polyfit([0,1,2], y_tr[Q1], 1)[0]:+.3f}/month); hybrids {HV[Q1].astype(int).tolist()} ({np.polyfit([0,1,2], y_ct[Q1], 1)[0]:+.3f}/month)")
DH = A("MP:DIESEL HYBRID"); HV_noDH = HV - DH
print(f"  DIESEL HYBRID in control: Jan-Mar 2024 {DH[Q1].astype(int).tolist()}, May-Oct 2024 {DH[POST].astype(int).tolist()}")
P_DEC = [pos[idx(2024, m)] for m in range(5, 13)]; P_MAR25 = [pos[idx(2024, m)] for m in range(5, 13)] + [pos[idx(2025, m)] for m in (1, 2, 3)]
P_SEP25 = P_MAR25 + [pos[idx(2025, m)] for m in range(4, 10)]
ctrls = {"HEV (prereg)": HV, "HEV excl. DIESEL HYBRID": HV_noDH, "ICE": IC, "HEV+ICE": HV + IC}
wins = {"May-Oct 2024 (prereg)": POST, "May-Dec 2024": P_DEC, "May 2024-Mar 2025": P_MAR25, "May 2024-Sep 2025": P_SEP25}
for cn, ct in ctrls.items():
    print(f"  control {cn:26s} " + "  ".join(f"{wn}: {pct(did(TR, ct, Q1, w)):+5.0f}%" for wn, w in wins.items()))
print("  treated split vs HEV, prereg window: " + ", ".join(f"{k} {pct(did(A(k), HV, Q1, POST)):+.0f}%" for k in ("BEV", "PHEV", "BEV|new", "BEV|used", "PHEV|new", "PHEV|used")))
print(f"  dose check: BEV (full RUC) vs PHEV (reduced RUC): {pct(did(A('BEV'), A('PHEV'), Q1, POST)):+.0f}%  (a deterrent predicts negative)")
sh_tr, sh_hv = 100 * TR / TOT, 100 * HV / TOT
print(f"  share outcome (pp of light registrations): treated share {sh_tr[Q1].mean():.1f} -> {sh_tr[POST].mean():.1f} pp; HEV share {sh_hv[Q1].mean():.1f} -> {sh_hv[POST].mean():.1f} pp; DiD {sh_tr[POST].mean()-sh_tr[Q1].mean()-(sh_hv[POST].mean()-sh_hv[Q1].mean()):+.1f} pp")
print(f"  log-share DiD equals the log-count DiD by construction: {pct(did(TR/TOT, HV/TOT, Q1, POST) if False else (np.mean(np.log(sh_tr[POST]))-np.mean(np.log(sh_tr[Q1]))-(np.mean(np.log(sh_hv[POST]))-np.mean(np.log(sh_hv[Q1]))))):+.1f}%")

print("\n== Placebo-in-time distribution of the DiD statistic (3 pre, 1 skipped, 6 post), windows not touching Oct 2023-Oct 2024")
excl = set(range(idx(2023, 10), idx(2024, 10) + 1)); pl = []
for s in months:
    w = list(range(s, s + 10))
    if w[-1] > months[-1] or any(i in excl for i in w): continue
    pre = [pos[i] for i in w[:3]]; post = [pos[i] for i in w[4:]]
    pl.append((lab(s + 3), did(TR, HV, pre, post)))
vals = np.array([v for _, v in pl])
print(f"  n={len(pl)}  mean {vals.mean():+.3f}  SD {vals.std(ddof=1):.3f}  |placebo| >= |real {druc0:.3f}|: {int(np.sum(np.abs(vals) >= abs(druc0)))}/{len(pl)}  placebo >= real: {int(np.sum(vals >= druc0))}")
print("  placebos (skipped month -> DiD %):", ", ".join(f"{m}:{pct(v):+.0f}" for m, v in pl))
print("  preregistered April placebos as the study computes them (2026 has only May-Sep in the post window): " + ", ".join(f"{yr}: {pct(did(TR, HV, [pos[idx(yr,m)] for m in (1,2,3)], [pos[idx(yr,m)] for m in (5,6,7,8,9,10) if idx(yr,m) in pos])):+.0f}%" for yr in (2022, 2023, 2025, 2026)))
print("  policy events inside placebo windows: treated/HEV/ICE by month")
for i in [idx(2022, m) for m in (2, 3, 4, 5)] + [idx(2023, m) for m in (5, 6, 7, 8)] + [idx(2026, m) for m in (1, 2, 3, 4, 5)]:
    j = pos[i]; print(f"    {lab(i)}: plug-in {TR[j]:6,.0f}  HEV {HV[j]:6,.0f}  ICE {IC[j]:6,.0f}  plug-in share {sh_tr[j]:5.1f}%")

print("\n== Recovery / share claims")
sb = 100 * A("BEV") / TOT
for m, (y, mo) in {"Nov 2023": (2023, 11), "Dec 2023": (2023, 12), "Jan 2024": (2024, 1), "Feb 2024": (2024, 2)}.items():
    j = pos[idx(y, mo)]; print(f"  {m}: plug-in share {sh_tr[j]:.1f}%  BEV share {sb[j]:.1f}%  ICE {IC[j]:,.0f}  total {TOT[j]:,.0f}")
def mean_share(y0, m0, y1, m1): js = [pos[i] for i in range(idx(y0, m0), idx(y1, m1) + 1)]; return sh_tr[js].mean(), sb[js].mean(), TR[js].sum(), A("BEV")[js].sum()
for nm, args in {"2023 Jan-Sep": (2023, 1, 2023, 9), "2023 Apr-Sep (mid-2023)": (2023, 4, 2023, 9), "2023 full": (2023, 1, 2023, 12), "2024 May-Dec": (2024, 5, 2024, 12), "2025 full": (2025, 1, 2025, 12),
                 "2026 Jan-Sep": (2026, 1, 2026, 9), "2026 Apr-Sep": (2026, 4, 2026, 9)}.items():
    s1, s2, n1, n2 = mean_share(*args); print(f"  {nm:26s} mean plug-in share {s1:5.1f}%  mean BEV share {s2:5.1f}%  plug-ins {n1:7,.0f}  BEVs {n2:7,.0f}")
js = [pos[i] for i in range(idx(2026, 4), idx(2026, 9) + 1)]; print(f"  2026 Apr-Sep monthly plug-in share range {sh_tr[js].min():.1f}-{sh_tr[js].max():.1f}% (report: 'back to 18-22%')")
print(f"  preprint's window (24 months after Dec 2023 = through Dec 2025): mean plug-in share Jan 2024-Dec 2025 {sh_tr[[pos[i] for i in range(idx(2024,1), idx(2025,12)+1)]].mean():.1f}% vs Jan-Nov 2023 {sh_tr[[pos[i] for i in range(idx(2023,1), idx(2023,11)+1)]].mean():.1f}%")

print("\n== Ute claim (study's series includes trucks >3,500 kg; light-only numbers from the service are in verify_counts.out)")
ute = defaultdict(float)
for r in csv.DictReader(open(RUN / "data" / "registrations.csv")):
    if r["vehicle_type"] == "GOODS VAN/TRUCK/UTILITY" and r["motive_power"] == "DIESEL": ute[idx(int(r["year"]), int(r["month"]))] += float(r["n"])
u = np.array([ute.get(i, 0) for i in months])
print(f"  study series: Oct-Nov 2023 mean {u[[pos[idx(2023,10)],pos[idx(2023,11)]]].mean():,.0f}; Dec 2023 {u[DEC]:,.0f} ({100*u[DEC]/u[[pos[idx(2023,10)],pos[idx(2023,11)]]].mean():.0f}% of Oct-Nov); Jan 2024 {u[pos[idx(2024,1)]]:,.0f}; Feb-Jun 2024 {u[[pos[idx(2024,m)] for m in (2,3,4,5,6)]].astype(int).tolist()}")
print(f"  same pattern at the other fee dates: Mar/Apr 2022 {u[pos[idx(2022,3)]]:,.0f}/{u[pos[idx(2022,4)]]:,.0f}; Jun/Jul 2023 {u[pos[idx(2023,6)]]:,.0f}/{u[pos[idx(2023,7)]]:,.0f}")
print(f"  heavy (>3,500 kg) vehicles in the 'light' universe: see verify_counts.out (36,295 diesel; ~37,300 total of {int(TOT.sum()):,})")
