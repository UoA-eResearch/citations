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
    old = json.load(open(TAB / "secondary.json")) if (TAB / "secondary.json").exists() else {}
    old.update(out)
    A.save(old, "secondary.json")
    print(json.dumps({k: (v if k != "support" else v["fits"]) for k, v in out.items()},
                     indent=1, default=float)[:4000])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
