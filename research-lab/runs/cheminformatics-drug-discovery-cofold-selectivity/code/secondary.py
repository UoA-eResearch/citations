"""Secondary arms (plan.md §5.2-§5.6): decoy proteins, promiscuity probe, affinity sampling, and the
training-support gradient. Writes results/tables/secondary.json plus a few CSVs.
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import assemble as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
DB = ("/mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cliff-noise-ceiling/"
      "data/chembl_37/chembl_37_sqlite/chembl_37.db")


def decoys(d):
    """P6: per ligand, the predicted affinity against each decoy protein against its kinome spread."""
    pred, prob, _, accs, cids = S.matrices("panel", d)
    dp = S.preds("decoy")
    dp["acc"] = dp.protein.str.replace("_decoy", "", regex=False)
    piv = dp.pivot_table(index="cid", columns="acc", values="pred", aggfunc="last").reindex(cids)
    pivp = dp.pivot_table(index="cid", columns="acc", values="affinity_probability_binary",
                          aggfunc="last").reindex(cids)
    kin_mean, kin_sd = np.nanmean(pred, 1), np.nanstd(pred, 1)
    kin_max = np.nanmax(pred, 1)
    rows = []
    for a in piv.columns:
        v = piv[a].to_numpy(float)
        rows.append(dict(decoy=a, median_pred=float(np.nanmedian(v)),
                         median_gap_vs_kinase_mean=float(np.nanmedian(v - kin_mean)),
                         median_gap_vs_kinase_max=float(np.nanmedian(v - kin_max)),
                         median_gap_in_kinome_sd=float(np.nanmedian((v - kin_mean) / kin_sd)),
                         share_above_kinase_mean=float(np.nanmean(v > kin_mean)),
                         share_above_kinase_max=float(np.nanmean(v > kin_max)),
                         median_prob=float(np.nanmedian(pivp[a].to_numpy(float)))))
    out = dict(per_decoy=rows, kinome_sd_median=float(np.nanmedian(kin_sd)),
               kinome_mean_median=float(np.nanmedian(kin_mean)),
               kinase_prob_median=float(np.nanmedian(prob)))
    pd.DataFrame(rows).to_csv(TAB / "decoy_summary.csv", index=False)
    return out


def promiscuity(d):
    """Recompute P1 on the 40-kinase union (panel + the 8 least promiscuous eligible kinases)."""
    extra = json.load(open(RUN / "data" / "promisc_kinases.json"))
    accs = [k["acc"] for k in d["panel"]["kinases"]] + [k["acc"] for k in extra]
    pred_u, _, meas_u, accs_u, cids_u = S.matrices(["panel", "promisc"], d, accs=accs)
    pred_e, _, meas_e, accs_e, _ = S.matrices("promisc", d, accs=[k["acc"] for k in extra])
    return dict(union=dict(shape=[len(cids_u), len(accs_u)], P1=A.primary(pred_u, meas_u),
                           P3=A.med(A.within_kinase(pred_u, meas_u))),
                extra_only=dict(shape=list(pred_e.shape), P1=A.primary(pred_e, meas_e),
                                n_ligands_defined=int(A.primary(pred_e, meas_e)["n_ligands"]),
                                mean_n_unc=float((meas_e > A.CENSOR_PKD).sum(1).mean())),
                extra_kinases=[(k["davis_name"], k["group"], k["n_unc"]) for k in extra])


def sampling(d):
    """Same sub-rectangle at default and heavy affinity sampling."""
    sub = json.load(open(RUN / "data" / "sampling_subset.json"))
    k_by_name = {k["davis_name"]: k for k in d["panel"]["kinases"]}
    accs = [k_by_name[n]["acc"] for n in sub["kinases"]]
    cids = sub["ligands"]
    out = {}
    for arm in ("panel", "sampling"):
        pred, prob, meas, a2, c2 = S.matrices(arm, d, accs=accs, cids=cids)
        out[arm] = dict(shape=[len(c2), len(a2)], P1=A.primary(pred, meas, nboot=1000),
                        P1_probability=A.primary(prob, meas, nboot=1000),
                        P3=A.med(A.within_kinase(pred, meas)))
    pa, _, meas, _, _ = S.matrices("panel", d, accs=accs, cids=cids)
    pb, _, _, _, _ = S.matrices("sampling", d, accs=accs, cids=cids)
    out["pairwise"] = dict(pearson_between_settings=float(np.corrcoef(pa.ravel(), pb.ravel())[0, 1]),
                           mean_abs_change=float(np.nanmean(np.abs(pa - pb))),
                           diff=A.paired_difference(pb, meas, pa, nboot=1000))
    return out


def postcut():
    """Arm 5.3: the same within-ligand question on 11 compounds first published in 2025 or later.

    Three things make this a check rather than a replication, and all three are reported: the measurements
    are ChEMBL pActivity pooled over mixed assay types (IC50 and Ki, some records right-censored at '>'),
    not Davis Kd from one assay; each compound covers only 6-12 kinases, so a per-compound Spearman is
    noisy; and the kinase sets differ between compounds, so there is no rectangle and no clean analogue of
    the panel's promiscuity baseline. The within-arm baseline below uses each kinase's mean measured
    pActivity over the *other* compounds, and is only defined for kinases appearing in at least three.
    """
    t = pd.read_csv(TAB / "postcut_pairs.csv")
    pr = S.preds("postcut")
    pr["acc"] = pr.protein.str.replace("_pc", "", regex=False)
    m = t.merge(pr[["acc", "cid", "pred", "affinity_probability_binary"]].rename(
        columns={"cid": "chembl_id"}), on=["acc", "chembl_id"], how="inner")
    # both directions are bounds, not values: 3 pairs are ">" (inactive at the top concentration) and 5
    # are "<" (more potent than the assay could resolve). The first draft counted only ">".
    m["censored"] = m.rels.astype(str).str.contains(">|<", regex=True)
    m["censored_upper"] = m.rels.astype(str).str.contains(">")
    # each kinase's mean over the other compounds (the B1 analogue, where it is defined at all)
    counts = m.groupby("acc").chembl_id.nunique()
    rows, per = [], []
    for cid, g in m.groupby("chembl_id"):
        base = []
        for _, r in g.iterrows():
            others = m[(m.acc == r.acc) & (m.chembl_id != cid)]
            base.append(others.pact.mean() if counts.get(r.acc, 0) >= 3 else np.nan)
        rho_m = A.rho(g.pred.to_numpy(float), g.pact.to_numpy(float))
        rho_p = A.rho(g.affinity_probability_binary.to_numpy(float), g.pact.to_numpy(float))
        rho_b = A.rho(np.asarray(base, float), g.pact.to_numpy(float))
        unc = g[~g.censored]
        rho_u = (A.rho(unc.pred.to_numpy(float), unc.pact.to_numpy(float))
                 if len(unc) >= A.MIN_UNC_P2 else np.nan)
        per.append(dict(chembl_id=cid, n_kinases=len(g), n_censored=int(g.censored.sum()),
                        rho=rho_m, rho_probability=rho_p, rho_baseline=rho_b, rho_uncensored=rho_u,
                        pact_range=float(g.pact.max() - g.pact.min())))
        rows.append((rho_m, rho_b))
    p = pd.DataFrame(per)
    p.to_csv(TAB / "postcut_per_compound.csv", index=False)
    a = p.rho.to_numpy(float)
    b = p.rho_baseline.to_numpy(float)
    rng = np.random.default_rng(A.SEED)
    draws = A.boot_ligand(lambda idx: A.med(a[idx]), len(a), rng)
    lo, hi = A.ci(draws)
    # The promiscuity analogue needs kinases measured across several compounds, and this arm has 61
    # kinases of which only 8 appear in three or more. The baseline is therefore defined for 4 compounds
    # and spans 3-6 kinases each, and two of those four share all six kinases - so their "mean over the
    # other compounds" is essentially the other compound's own measurements, and both score exactly 1.0.
    # That is an artefact of the overlap, not a baseline, so it is reported as not computable.
    n_base = int(np.isfinite(b).sum())
    enough = (p.rho_baseline.notna() & (p.n_kinases >= 5)).sum() >= 5
    baseline = (dict(computable=False, n_compounds_defined=n_base,
                     reason="only 8 of 61 kinases appear in 3 or more compounds; the baseline is defined "
                            "for 4 compounds over 3-6 kinases each and is dominated by overlapping pairs")
                if not enough else dict(computable=True, point=A.med(b), n=n_base))
    return dict(n_compounds=len(p), n_pairs=int(len(m)),
                kinases_per_compound=[int(p.n_kinases.min()), int(p.n_kinases.max())],
                censored_share=float(m.censored.mean()),
                censored_share_upper_only=float(m.censored_upper.mean()),
                P1=dict(point=A.med(a), lo=lo, hi=hi),
                P1_probability=dict(point=A.med(p.rho_probability.to_numpy(float))),
                P1_uncensored=dict(point=A.med(p.rho_uncensored.to_numpy(float)),
                                   n=int(np.isfinite(p.rho_uncensored).sum())),
                baseline_within_arm=baseline,
                per_compound=per)


def kinase_concordance(pred, meas):
    """Per kinase: share of within-ligand pairwise comparisons involving that kinase that the model
    orders the same way as the measurement (ties in either dropped)."""
    n, k = pred.shape
    num = np.zeros(k)
    den = np.zeros(k)
    for i in range(n):
        p, y = pred[i], meas[i]
        dp = np.sign(p[:, None] - p[None, :])
        dy = np.sign(y[:, None] - y[None, :])
        ok = (dp != 0) & (dy != 0) & np.isfinite(dp) & np.isfinite(dy)
        agree = ok & (dp == dy)
        num += agree.sum(1)
        den += ok.sum(1)
    return num / np.maximum(den, 1), den


def support(d):
    """Training-support proxy: distinct compounds with Kd/Ki/IC50 per kinase in pre-2024 ChEMBL docs."""
    accs = [k["acc"] for k in d["panel"]["kinases"]]
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ph = ",".join("?" * len(accs))
    q = f"""
    select cs.accession, count(distinct a.molregno)
    from activities a
    join assays ass on ass.assay_id = a.assay_id
    join target_dictionary td on td.tid = ass.tid
    join target_components tc on tc.tid = td.tid
    join component_sequences cs on cs.component_id = tc.component_id
    join docs d on d.doc_id = a.doc_id
    where cs.accession in ({ph}) and a.standard_type in ('Kd','Ki','IC50')
      and a.standard_units = 'nM' and a.standard_value > 0
      and td.target_type = 'SINGLE PROTEIN' and ass.confidence_score >= 8 and d.year < 2024
    group by cs.accession
    """
    sup = dict(c.execute(q, accs))
    pred, _, meas, accs2, cids = S.matrices("panel", d)
    wk = A.within_kinase(pred, meas)
    conc, den = kinase_concordance(pred, meas)
    mae = np.nanmean(np.abs(pred - meas), axis=0)
    rows = []
    for j, a in enumerate(accs2):
        k = next(x for x in d["panel"]["kinases"] if x["acc"] == a)
        rows.append(dict(acc=a, kinase=k["davis_name"], group=k["group"], support=sup.get(a, 0),
                         log_support=float(np.log10(sup.get(a, 0) + 1)), within_kinase_rho=float(wk[j]),
                         concordance=float(conc[j]), n_comparisons=int(den[j]), mae=float(mae[j]),
                         n_unc=int((meas[:, j] > A.CENSOR_PKD).sum())))
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "support_gradient.csv", index=False)
    fits = {}
    for y in ("within_kinase_rho", "concordance", "mae"):
        m = np.isfinite(t[y])
        fits[y] = dict(spearman=float(A.rho(t.log_support[m].to_numpy(), t[y][m].to_numpy())),
                       slope=float(np.polyfit(t.log_support[m], t[y][m], 1)[0]))
    return dict(per_kinase=rows, fits=fits, support_range=[int(t.support.min()), int(t.support.max())])


def main(which="all"):
    d = S.davis()
    out = {}
    if which in ("all", "decoy"):
        out["decoy"] = decoys(d)
    if which in ("all", "promisc"):
        out["promiscuity"] = promiscuity(d)
    if which in ("all", "sampling"):
        out["sampling"] = sampling(d)
    if which in ("all", "support"):
        out["support"] = support(d)
    if which in ("all", "postcut") and (TAB / "postcut_pairs.csv").exists() \
            and not S.preds("postcut").empty:
        out["postcut"] = postcut()
    old = json.load(open(TAB / "secondary.json")) if (TAB / "secondary.json").exists() else {}
    old.update(out)
    A.save(old, "secondary.json")
    print(json.dumps({k: (v if k != "support" else v["fits"]) for k, v in out.items()},
                     indent=1, default=float)[:4000])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
