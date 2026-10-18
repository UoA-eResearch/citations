"""Confirmation pass on commit c3516ec (D4). (a) Eligibility: the 26 known-wrong signals are gone; what the two new
mapping rules removed, including correctly mapped conjugates and abbreviations they also catch; counts 443/370/132.
(b) Independent re-run of H1, the null-propagated bootstrap and the FAERS-only variant from data/recomputed.csv.
(c) SQL spot check of two faersonly 2x2 cells. (d) Known-wrong signals from my adjudication vs the new eligible set."""
import json, re, sys, time
from pathlib import Path
import duckdb, numpy as np, pandas as pd
from scipy import optimize, stats
RUN = Path(__file__).resolve().parents[2]; OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN / "code"))
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
a = pd.read_csv(RUN / "data" / "signals_all.csv", dtype={"paper": str})
r = pd.read_csv(RUN / "data" / "recomputed.csv", dtype={"paper": str})
s = pd.read_csv(RUN / "results" / "tables" / "signals_results.csv", dtype={"paper": str})
old = pd.read_csv(OUT / "fresh_sample_adjudication.csv", dtype={"paper": str})
prim = json.load(open(RUN / "results" / "tables" / "primary.json"))
print("== (a) eligibility ==")
print("signals_all rows", len(a), "| reasons:", a.reason.fillna("ELIGIBLE").value_counts().to_dict())
print("eligible", int(a.reason.isna().sum()), "| capped", len(e), "| papers", e.paper.nunique(), "| results rows", len(s), "| status", s.status.value_counts().to_dict())
wrong = old[(old.extraction_correct == 0) | (old.mapping_ok == 0)][["paper", "k"]].drop_duplicates()
still = wrong.merge(e[["paper", "k"]], on=["paper", "k"])
print("known-wrong (26) still in the capped set:", len(still))
rev = a[a.reason == "found wrong in review"]; print("removed as 'found wrong in review':", len(rev), "signals in", rev.paper.nunique(), "papers")
ab = a[a.reason == "abbreviation, not mapped"]; print("removed as abbreviation:", len(ab), ab.drug.value_counts().to_dict())
cj = a[a.reason == "conjugate mapped to its antibody"]; print("removed as conjugate:", len(cj), cj.drug.value_counts().to_dict())
# what else changed vs the reviewed eligible set
import subprocess
old_elig = pd.read_csv(pd.io.common.StringIO(subprocess.run(["git", "-C", "/mnt/citations", "show", "d62a942:research-lab/runs/future-health-faers-published-signal-recalibration/results/tables/signals_results.csv"], capture_output=True, text=True).stdout), dtype={"paper": str})  # the reviewed 406 (data/ is not tracked)
k_old, k_new = set(zip(old_elig.paper, old_elig.k)), set(zip(e.paper, e.k))
print("reviewed capped set", len(k_old), "| new capped set", len(k_new), "| common", len(k_old & k_new), "| dropped", len(k_old - k_new), "| new", len(k_new - k_old))
dropped = old_elig.set_index(["paper", "k"]).loc[list(k_old - k_new)]
print("dropped by reason (from new signals_all):")
dr = a.set_index(["paper", "k"]).reindex(list(k_old - k_new)).reason.fillna("still eligible, lost the redraw").value_counts(); print(dr.to_string())
# correctly-mapped signals the new rules also removed (over-exclusion)
over = a[a.reason.isin(["abbreviation, not mapped", "conjugate mapped to its antibody"]) & a.drug.isin(["CsA", "Sacituzumab govitecan", "Sacituzumab Govitecan", "enfortumab vedotin", "brentuximab vedotin", "belantamab mafodotin", "inotuzumab ozogamicin"])]
print("correctly-mapped drugs removed by the new rules:", over.drug.value_counts().to_dict(), "| of which in the reviewed capped set:", len(set(zip(over.paper, over.k)) & k_old))
print("conjugates kept:", e[e.drug.str.contains("vedotin|mafodotin|ozogamicin|govitecan|deruxtecan|emtansine", case=False)].drug.value_counts().to_dict())
print()
print("== (b) H1 / null-propagated / FAERS-only, independently ==")
nc = pd.read_csv(RUN / "data" / "negative_controls_computed.csv"); v = nc[(nc.status == "ok") & (nc.a >= 1) & np.isfinite(nc.se)]
lr, se = np.log(v.ror.values), v.se.values
def mle(l, s_):
    def nll(p):
        s2 = np.exp(2 * p[1]) + s_ ** 2; return 0.5 * np.sum(np.log(2 * np.pi * s2) + (l - p[0]) ** 2 / s2)
    rr = optimize.minimize(nll, [l.mean(), np.log(max(l.std(), .05))], method="Nelder-Mead"); return rr.x[0], np.exp(rr.x[1])
def bh(p):
    p = np.asarray(p, float); fin = np.isfinite(p); n = fin.sum(); q = np.full(p.shape, np.nan); o = np.argsort(np.where(fin, p, np.inf))
    ranked = p[o][:n] * n / np.arange(1, n + 1); q[o[:n]] = np.minimum(1, np.minimum.accumulate(ranked[::-1])[::-1]); return q
mu, sg = mle(lr, se); print(f"null mu={mu:.4f} sigma={sg:.4f} (json {prim['null']['mle']['mu']:.4f}, {prim['null']['mle']['sigma']:.4f})")
d = e.merge(r.drop(columns=["ingredient", "win"]), on=["paper", "k"]); assert (d.status == "ok").all() and len(d) == len(e)
lrs, ses, ror = np.log(d.primary_ror.values), d.primary_se.values, d.primary_ror.values
def surv(mu_, sg_, idx):
    q = bh(2 * stats.norm.sf(np.abs((lrs[idx] - mu_) / np.sqrt(sg_ ** 2 + ses[idx] ** 2)))); return np.where(np.isfinite(q), (ror[idx] > 1) & (q < 0.05), False).mean()
allidx = np.arange(len(d)); print("H1 share:", round(surv(mu, sg, allidx), 4), "(json", round(prim["H1"]["share_surviving"], 4), ")  n =", len(d), "survivors", int(round(surv(mu, sg, allidx) * len(d))))
rng = np.random.default_rng(11); papers = d.paper.unique(); gi = {p_: np.where(d.paper.values == p_)[0] for p_ in papers}
# fixed q, paper bootstrap (preregistered)
q0 = bh(2 * stats.norm.sf(np.abs((lrs - mu) / np.sqrt(sg ** 2 + ses ** 2)))); sv0 = np.where(np.isfinite(q0), (ror > 1) & (q0 < 0.05), False)
b1 = [sv0[np.concatenate([gi[p_] for p_ in rng.choice(papers, len(papers))])].mean() for _ in range(2000)]
print("paper bootstrap:", np.round(np.percentile(b1, [2.5, 97.5]), 3), "(json", np.round(prim["H1"]["ci"], 3), ")")
b2 = []
for _ in range(1000):
    j = rng.integers(0, len(lr), len(lr)); m_, s_ = mle(lr[j], se[j]); ii = np.concatenate([gi[p_] for p_ in rng.choice(papers, len(papers))]); b2.append(surv(m_, s_, ii))
print("joint paper+control bootstrap (1000 draws, my seed):", np.round(np.percentile(b2, [2.5, 97.5]), 3), "(json", np.round(prim["H1_null_propagated"]["ci"], 3), ")")
# FAERS-only
fo = d[d.faersonly_status == "ok"]; print("faersonly computable:", len(fo), "| not:", int((d.faersonly_status != "ok").sum()), "(json n", prim["variants"]["faersonly"]["n"], "not", prim["variants"]["faersonly"]["n_not_computable"], ")")
qf = bh(2 * stats.norm.sf(np.abs((np.log(fo.faersonly_ror.values) - mu) / np.sqrt(sg ** 2 + fo.faersonly_se.values ** 2))))
print("faersonly survive:", round(np.where(np.isfinite(qf), (fo.faersonly_ror.values > 1) & (qf < 0.05), False).mean(), 4), "(json", round(prim["variants"]["faersonly"]["survive_mle"], 4), ")")
post = d[d.win.str[:6] >= "2012Q4"]; print("windows starting >= 2012Q4:", len(post), "| faersonly == primary a for them:", int((post.faersonly_a == post.primary_a).sum()))
pre = d[(d.win.str[:6] < "2012Q4") & (d.faersonly_status == "ok")]; print("pre-2012Q4 windows: faersonly_a <= primary_a for", int((pre.faersonly_a <= pre.primary_a).sum()), "of", len(pre))
print("windows starting before 2004:", int((d.win.str[:4].astype(int) < 2004).sum()), "(json", prim.get("windows_starting_before_2004"), ")")
# H2
ratio = d.estimate.values / ror; fin = np.isfinite(ratio) & (ratio > 0); med = np.median(ratio[fin]); print("H2 median", round(med, 4), "n", fin.sum(), "(json", round(prim["H2"]["median_ratio"], 4), prim["H2"]["n"], ")")
# threshold
svb = sv0.astype(bool); print("smallest surviving ROR", round(ror[svb].min(), 3), "| largest non-surviving a>=3", round(np.nanmax(np.where(~svb & (d.primary_a.values >= 3), ror, np.nan)), 3), "| survivors a<3", int((svb & (d.primary_a.values < 3)).sum()), "(json", prim["survival_threshold"], ")")
print("control median ROR", round(float(np.exp(np.median(lr))), 3), "| controls designated", len(nc), "| a==0", int(((nc.status == "ok") & (nc.a == 0)).sum()))
# all-drugs label count, comparison counts, zero cells, non-survivor breakdown
print("comparison:", d.comparison.value_counts().to_dict(), "| zero-cell:", int((~np.isfinite(ror)).sum()), "| a==0:", int((d.primary_a == 0).sum()))
ns = ~svb; finr = np.isfinite(ror)
print("non-survivors", int(ns.sum()), "| zero cell", int((ns & ~finr).sum()), "| ror<=1", int((ns & finr & (ror <= 1)).sum()), "| ror>1 a<3", int((ns & finr & (ror > 1) & (d.primary_a.values < 3)).sum()),
      "| ror>1 a>=3 lo<=1", int((ns & finr & (ror > 1) & (d.primary_a.values >= 3) & (d.primary_lo.values <= 1)).sum()), "| sig uncal lost to calibration", int((ns & d.primary_sig_uncal.values if "primary_sig_uncal" in d else 0).sum()) if "primary_sig_uncal" in d else "n/a")
sr = s.copy(); print("from signals_results: sig_uncal & not survive:", int((sr.primary_sig_uncal & ~sr.primary_survive_mle.fillna(False)).sum()), "| ratio >2:", int((sr.ratio > 2).sum()), "| <0.5:", int((sr.ratio < 0.5).sum()), "| 0.8-1.25:", int(((sr.ratio >= 0.8) & (sr.ratio <= 1.25)).sum()), "| finite ratio:", int(np.isfinite(sr.ratio).sum()))
bands = pd.cut(sr.estimate, [0, 2, 5, 20, np.inf]); print(sr.groupby(bands, observed=True).primary_survive_mle.apply(lambda x: (round(x.fillna(False).mean(), 3), len(x))).to_dict())
recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
sr["year"] = sr.paper.map(lambda p: int(recs[p]["pubYear"])); print(sr.groupby("year").primary_survive_mle.apply(lambda x: (round(x.fillna(False).mean(), 3), len(x))).to_dict())
g = sr.groupby("paper").primary_survive_mle.apply(lambda x: x.fillna(False).mean()); print("papers none", int((g == 0).sum()), "all", int((g == 1).sum()), "of", len(g))
print("n_cases non-null:", int(sr.n_cases.notna().sum()), "| secondary n:", prim["secondary"]["n"], prim.get("secondary_with_cases", {}).get("n"))
print()
print("== (c) SQL spot check of faersonly ==")
db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True); db.execute("SET threads TO 8")
import rxnorm
from recompute import terms_for, pattern
for ing, pt in (("lisinopril", "ANGIOEDEMA"), ("hydroxychloroquine", "PEMPHIGUS")):
    row = d[(d.ingredient == ing) & (d.event_pt == pt)].iloc[0]; m = re.match(r"(\d{4})Q(\d)-(\d{4})Q(\d)", row.win); end = f"{m[3]}Q{m[4]}"
    p = pattern(terms_for(ing, row.drug)).replace("'", "''")
    n, = db.execute(f"SELECT count(*) FROM (SELECT rid, row_number() OVER (PARTITION BY caseid ORDER BY version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) rn FROM demo WHERE quarter BETWEEN '2012Q4' AND '{end}') WHERE rn=1").fetchone()
    aa, = db.execute(f"""WITH W AS (SELECT rid FROM (SELECT rid, row_number() OVER (PARTITION BY caseid ORDER BY version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) rn FROM demo WHERE quarter BETWEEN '2012Q4' AND '{end}') WHERE rn=1),
        D AS (SELECT DISTINCT rid FROM drug WHERE role='PS' AND (regexp_matches(coalesce(prod_ai,''), '{p}') OR regexp_matches(coalesce(drugname,''), '{p}'))),
        E AS (SELECT DISTINCT rid FROM reac WHERE pt='{pt}') SELECT count(*) FROM W JOIN D USING(rid) JOIN E USING(rid)""").fetchone()
    print(ing, pt, row.win, "| pipeline faersonly a,n:", int(row.faersonly_a), int(row.faersonly_a + row.faersonly_b + row.faersonly_c + row.faersonly_d), "| mine:", aa, n, "| primary a:", int(row.primary_a))
