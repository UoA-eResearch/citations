"""Reproduce the frozen forecast into cache/ and compare its sha256; probe leakage and the scoring rule."""
import hashlib, json, sys, re
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
sys.path.insert(0, str(RUN/"code"))
from forecast import features, at_risk   # pure functions; main() is not called
from analysis import load
d, cutoff = load()
X, y, snaps = [], [], []
for yr in range(2012, 2025):
    snap = pd.Timestamp(f"{yr}-11-01")
    if snap + pd.DateOffset(months=12) > cutoff: continue
    r = at_risk(d, snap); X.append(features(r, snap)); yy = (r.t3.notna() & (r.t3 <= snap + pd.DateOffset(months=12))).astype(int); y.append(yy)
    snaps.append(dict(snap=str(snap.date()), n=len(r), pos=int(yy.sum()), pos_hml_start=int(((r.t3 == "2013-10-01") & (yy == 1)).sum())))
X, y = pd.concat(X), pd.concat(y)
print("training snapshots:"); print(pd.DataFrame(snaps).to_string(index=False))
m = LogisticRegression(C=1.0, max_iter=2000).fit(X, y)
r = at_risk(d, cutoff); p = m.predict_proba(features(r, cutoff))[:, 1]
f = pd.DataFrame(dict(substance=r.substance, t0=r.t0.dt.date, t2=r.t2.dt.date, p_funded_12m=np.round(p, 4)))
f["base_rate"] = round(float(y.mean()), 4); f["forecast_origin"] = str(cutoff.date()); f["score_after"] = str((cutoff + pd.DateOffset(months=12)).date())
out = RUN/"review/reviewer_checks/cache/forecast_repro.csv"
f.sort_values("p_funded_12m", ascending=False).to_csv(out, index=False)
h = hashlib.sha256(out.read_bytes()).hexdigest(); want = (RUN/"results/forecast_2026.sha256").read_text().split()[0]
print("\nreproduced sha256:", h, "\nfrozen     sha256:", want, "\nMATCH" if h == want else "MISMATCH")
fro = pd.read_csv(RUN/"results/forecast_2026.csv")
mm = fro.merge(f, on="substance", suffixes=("_frozen", "_repro")); print("max |dp| vs frozen:", float((mm.p_funded_12m_frozen - mm.p_funded_12m_repro).abs().max()), "n", len(mm))
# scoring rule vs linking rule: forecast substances whose match_names differ from the bare substance name
lk = pd.read_csv(RUN/"data/linked.csv")[["substance", "match_names", "consent_ended"]]
z = fro.merge(lk, on="substance"); diff = z[z.match_names != z.substance]
print("\nforecast substances with match_names != substance (score_forecast.py would only use the bare name):", len(diff)); print(diff[["substance", "match_names", "p_funded_12m"]].to_string(index=False))
print("forecast substances whose consent has ended (lapsed/revoked):", int(z.consent_ended.notna().sum()))
# feature range: year feature at origin vs training
print("\nyear feature: training range", int(X.year.min()), "..", int(X.year.max()), "; origin", cutoff.year - 2018)
print("yrs_t2 at origin: min", float(((cutoff - r.t2).dt.days / 365.25).min()), "max", float(((cutoff - r.t2).dt.days / 365.25).max()))
# leakage probe: does any feature use information after the snapshot? au_listed uses t3_au <= snap (ok). t2 may be the later full consent -> risk set defined with post-snapshot info
print("\nat-risk set uses t2 (latest consent). Provisional-route substances excluded from early snapshots by a late t2 would be a risk-set leak; see provisional list in recompute.py")
# Scoring: in-sample Brier of the model vs base rate on training data (optimism check)
pt = m.predict_proba(X)[:, 1]; bs = np.mean((pt - y) ** 2); bb = np.mean((y.mean() - y) ** 2)
print(f"in-sample Brier model {bs:.4f} vs base {bb:.4f}; skill {1 - bs/bb:.3f}")
# leave-one-year-out skill
sk = []
for s in snaps:
    yr = int(s["snap"][:4]); mask = (X.year == yr - 2018).values
    if mask.sum() == 0 or y[~mask].sum() == 0: continue
    mm_ = LogisticRegression(C=1.0, max_iter=2000).fit(X[~mask], y[~mask]); pp = mm_.predict_proba(X[mask])[:, 1]
    b0 = float(y[~mask].mean()); bs_ = np.mean((pp - y[mask]) ** 2); bb_ = np.mean((b0 - y[mask]) ** 2)
    sk.append(dict(year=yr, n=int(mask.sum()), pos=int(y[mask].sum()), skill=round(1 - bs_ / bb_, 3) if bb_ > 0 else None))
print("leave-one-snapshot-out Brier skill (vs training base rate):"); print(pd.DataFrame(sk).to_string(index=False))
