"""Reviewer check 5 (exploratory): an event-matched pseudo-null. The 119 OHDSI negative-control drugs are paired with
the 231 PTs of the published signals (pairs that are, for the great majority, unrelated drug-event pairs), computed
with the pipeline's protocol over 2004Q1-2025Q4, and the systematic-error distribution is fitted as in analysis.py.
Block 1 is the cross-product of the control drugs with the OHDSI outcome PTs (all pairs, not only the 332 designated
ones); block 2 the cross-product with the published signals' PTs. Both cross-products include true associations and
indication-as-event pairs, so the fit is also shown with the top decile trimmed, and the median is reported.
property of the PS-role ROR in FAERS, not of the control outcomes. A minority of these pairs are true associations, so
the fit is also shown after trimming the upper tail, and the median is reported. Read-only; temp tables only."""
import re, sys, time, json
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from scipy import optimize
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import rxnorm
from recompute import terms_for, pattern
OUT = Path(__file__).resolve().parent
db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True); db.execute("SET threads TO 8")
t0 = time.time()
db.execute("""CREATE TEMP TABLE W AS SELECT rid FROM (SELECT rid, row_number() OVER (PARTITION BY caseid ORDER BY version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) rn
              FROM demo WHERE quarter BETWEEN '2004Q1' AND '2025Q4') WHERE rn = 1""")
N = db.execute("SELECT count(*) FROM W").fetchone()[0]
db.execute("CREATE TEMP TABLE PS AS SELECT DISTINCT d.rid, coalesce(d.prod_ai,'') prod_ai, coalesce(d.drugname,'') drugname FROM drug d JOIN W USING (rid) WHERE d.role = 'PS'")
print("window reports", N, "| PS rows", db.execute("SELECT count(*) FROM PS").fetchone()[0], f"{time.time()-t0:.0f}s", flush=True)
s = pd.read_csv(RUN / "results" / "tables" / "signals_results.csv", dtype={"paper": str})
nc = pd.read_csv(RUN / "data" / "negative_controls.csv")
pts = sorted(set(s.event_pt)); ohdsi_pts = sorted(set(nc.pt.str.upper()))
allpts = sorted(set(pts) | set(ohdsi_pts))
db.execute("CREATE TEMP TABLE SP AS SELECT * FROM (VALUES " + ",".join("('" + p.replace("'", "''") + "')" for p in allpts) + ") t(pt)")
db.execute("CREATE TEMP TABLE EV AS SELECT DISTINCT r.rid, r.pt FROM reac r JOIN SP USING (pt) JOIN W USING (rid)")
ne = dict(db.execute("SELECT pt, count(*) FROM EV GROUP BY pt").fetchall())
print("event rows", db.execute("SELECT count(*) FROM EV").fetchone()[0], f"{time.time()-t0:.0f}s", flush=True)
db.execute("CREATE TEMP TABLE CD (rid VARCHAR, drug VARCHAR)")
drugs = sorted(nc.drug.unique())
for i, dr in enumerate(drugs):
    p = pattern(terms_for(dr, dr)).replace("'", "''")
    db.execute(f"INSERT INTO CD SELECT DISTINCT rid, '{dr.replace(chr(39), chr(39)*2)}' FROM PS WHERE regexp_matches(prod_ai, '{p}') OR regexp_matches(drugname, '{p}')")
    if i % 20 == 0: print(i, dr, f"{time.time()-t0:.0f}s", flush=True)
nd = dict(db.execute("SELECT drug, count(*) FROM CD GROUP BY drug").fetchall())
pairs = db.execute("SELECT c.drug, e.pt, count(*) a FROM CD c JOIN EV e USING (rid) GROUP BY 1, 2").fetchall()
A = {(d_, p_): a for d_, p_, a in pairs}
rows = []
for dr in drugs:
    for pt in allpts:
        a = A.get((dr, pt), 0); b = nd.get(dr, 0) - a; c = ne.get(pt, 0) - a; dd = N - a - b - c
        if a >= 1 and min(b, c, dd) > 0:
            lr = np.log((a / b) / (c / dd)); se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / dd)
            rows.append(dict(drug=dr, pt=pt, a=a, b=b, c=c, d=dd, logror=lr, se=se, set="signal_pt" if pt in pts else "ohdsi_pt"))
df = pd.DataFrame(rows); df.to_csv(OUT / "pseudo_null_pairs.csv", index=False)
def mle(lr, se):
    def nll(p):
        s2 = np.exp(2 * p[1]) + se ** 2; return 0.5 * np.sum(np.log(2 * np.pi * s2) + (lr - p[0]) ** 2 / s2)
    r = optimize.minimize(nll, [lr.mean(), np.log(max(lr.std(), .05))], method="Nelder-Mead"); return float(r.x[0]), float(np.exp(r.x[1]))
out = {}
for name, sub in (("ohdsi_pt_crossproduct (control drugs x OHDSI outcome PTs, all pairs, not only the 332 designated)", df[df.set == "ohdsi_pt"]), ("signal_pt_pairs (control drugs x published-signal PTs)", df[df.set == "signal_pt"])):
    mu, sg = mle(sub.logror.values, sub.se.values)
    # trimmed: drop the top 10% of log RORs (true associations and notoriety) before the fit
    q90 = sub.logror.quantile(0.9); tr = sub[sub.logror <= q90]; mu_t, sg_t = mle(tr.logror.values, tr.se.values)
    out[name] = dict(n_pairs=int(len(sub)), n_pairs_with_a0_excluded=True, mle_mu=mu, mle_sigma=sg, median_logror=float(sub.logror.median()),
                     share_lo_gt1=float(((sub.logror - 1.96 * sub.se) > 0).mean()), trimmed90_mu=mu_t, trimmed90_sigma=sg_t)
    print(name, json.dumps(out[name], indent=1), flush=True)
# by-PT medians for the signal PTs: how many signal PTs have a pseudo-null centre above 0?
g = df[df.set == "signal_pt"].groupby("pt").agg(n=("logror", "size"), med=("logror", "median"), mean=("logror", "mean"))
g = g[g.n >= 5]; out["signal_pts_with_ge5_pairs"] = int(len(g)); out["share_signal_pts_median_above_0"] = float((g.med > 0).mean())
out["signal_pt_median_of_pt_medians"] = float(g.med.median())
g.to_csv(OUT / "pseudo_null_by_pt.csv")
# survival under the signal-PT pseudo-null (MLE and trimmed), same BH rule
from analysis import bh, calibrated_p
lr_s, se_s = np.log(s.primary_ror.values), s.primary_se.values
for lab, (mu, sg) in (("pseudo_mle", (out["signal_pt_pairs (control drugs x published-signal PTs)"]["mle_mu"], out["signal_pt_pairs (control drugs x published-signal PTs)"]["mle_sigma"])),
                      ("pseudo_trimmed", (out["signal_pt_pairs (control drugs x published-signal PTs)"]["trimmed90_mu"], out["signal_pt_pairs (control drugs x published-signal PTs)"]["trimmed90_sigma"]))):
    q = bh(calibrated_p(lr_s, se_s, mu, sg)); out[f"H1_share_under_{lab}"] = float(((s.primary_ror.values > 1) & (q < 0.05)).mean())
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, dict)}, indent=1))
json.dump(out, open(OUT / "pseudo_null.json", "w"), indent=1)
print("done", f"{time.time()-t0:.0f}s")
# H1 if each signal is calibrated against its own event's pseudo-null centre (PT median over control drugs), pooled sigma
g2 = g.copy(); mu_pool = out["signal_pt_pairs (control drugs x published-signal PTs)"]["mle_mu"]; sg_pool = out["signal_pt_pairs (control drugs x published-signal PTs)"]["mle_sigma"]
mu_pt = s.event_pt.map(g2.med).fillna(mu_pool).values
q = bh(calibrated_p(lr_s, se_s, mu_pt, sg_pool)); out["H1_share_event_specific_centres"] = float(((s.primary_ror.values > 1) & (q < 0.05)).mean())
out["signals_with_event_specific_centre"] = int(s.event_pt.isin(g2.index).sum())
print("H1 share with event-specific centres:", out["H1_share_event_specific_centres"], "| signals with a centre:", out["signals_with_event_specific_centre"])
json.dump(out, open(OUT / "pseudo_null.json", "w"), indent=1)
