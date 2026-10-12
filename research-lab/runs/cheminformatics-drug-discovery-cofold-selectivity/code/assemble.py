"""Assemble per-pair predictions into tidy tables and matrices, then run the preregistered analysis.

  python code/assemble.py tidy                 -> results/tables/pairs_<arm>.csv for every arm present
  python code/assemble.py primary              -> results/tables/primary.json (plan.md §6 P1-P5 + verdict)
  python code/assemble.py secondary            -> decoy, promiscuity, sampling and support-gradient tables

The measured matrix is Davis pKd = 9 - log10(Kd[nM]); cells at the 10 uM ceiling become exactly 5.0 and are
flagged censored. Predictions are put on a pIC50-like scale with pred = 6 - affinity_pred_value so that
higher means stronger, matching pKd.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from panel import CENSOR_NM, load  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
PRED = RUN / "results" / "predictions.jsonl"


def preds(arm=None):
    rows = [json.loads(l) for l in open(PRED)]
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["arm", "pair_id"], keep="last")
    df["protein"] = df.pair_id.str.split("__").str[0]
    df["cid"] = df.pair_id.str.split("__").str[1]
    df["pred"] = 6.0 - df.affinity_pred_value
    return df[df.arm == arm] if arm else df


def davis():
    Y, prot, lig, uni = load()
    P = json.load(open(RUN / "data" / "panel.json"))
    names = [p[0] for p in prot]
    return dict(Y=Y, panel=P, prot_names=names, lig=dict(lig),
                rows=[c["row"] for c in P["ligands"]], cols=[k["col"] for k in P["kinases"]],
                cids=[c["cid"] for c in P["ligands"]], accs=[k["acc"] for k in P["kinases"]])


def pkd(nm):
    return 9.0 - np.log10(nm)


def matrices(arm, d, accs=None, cids=None):
    """Return (pred, prob, meas, kept_accs, kept_cids) over the rectangle actually predicted."""
    df = preds(arm)
    accs = accs or d["accs"]
    cids = cids or d["cids"]
    pv = df.pivot_table(index="cid", columns="protein", values="pred", aggfunc="last")
    pb = df.pivot_table(index="cid", columns="protein", values="affinity_probability_binary", aggfunc="last")
    accs = [a for a in accs if a in pv.columns]
    cids = [c for c in cids if c in pv.index]
    pred = pv.loc[cids, accs].to_numpy(float)
    prob = pb.loc[cids, accs].to_numpy(float)
    acc2col = {k["acc"]: k["col"] for k in d["panel"]["kinases"]}
    acc2col.update({k["acc"]: k["col"] for k in json.load(open(RUN / "data" / "promisc_kinases.json"))}
                   if (RUN / "data" / "promisc_kinases.json").exists() else {})
    cid2row = {c["cid"]: c["row"] for c in d["panel"]["ligands"]}
    if all(a in acc2col for a in accs):
        meas = pkd(d["Y"][np.ix_([cid2row[c] for c in cids], [acc2col[a] for a in accs])])
    else:
        meas = None
    return pred, prob, meas, accs, cids


def tidy():
    d = davis()
    df = preds()
    k_by_acc = {k["acc"]: k for k in d["panel"]["kinases"]}
    if (RUN / "data" / "promisc_kinases.json").exists():
        k_by_acc.update({k["acc"]: k for k in json.load(open(RUN / "data" / "promisc_kinases.json"))})
    cid2row = {c["cid"]: c["row"] for c in d["panel"]["ligands"]}
    out = []
    for _, r in df.iterrows():
        k = k_by_acc.get(r.protein)
        kd = (d["Y"][cid2row[r.cid], k["col"]] if k and r.cid in cid2row else np.nan)
        out.append(dict(arm=r.arm, pair_id=r.pair_id, protein=r.protein,
                        kinase=k["davis_name"] if k else r.protein, group=k["group"] if k else "decoy",
                        crop_len=k["crop_len"] if k else np.nan, cid=r.cid,
                        kd_nm=kd, pkd=pkd(kd) if np.isfinite(kd) else np.nan,
                        censored=bool(np.isfinite(kd) and kd >= CENSOR_NM),
                        affinity_pred_value=r.affinity_pred_value, pred_pic50=r.pred,
                        prob_binary=r.get("affinity_probability_binary"),
                        confidence_score=r.get("confidence_score"), iptm=r.get("iptm"),
                        ligand_iptm=r.get("ligand_iptm"), complex_plddt=r.get("complex_plddt")))
    t = pd.DataFrame(out)
    TAB.mkdir(parents=True, exist_ok=True)
    for arm, g in t.groupby("arm"):
        g.to_csv(TAB / f"pairs_{arm}.csv", index=False)
        print(f"pairs_{arm}.csv: {len(g)} rows")
    return t


def primary():
    d = davis()
    pred, prob, meas, accs, cids = matrices("panel", d)
    print(f"rectangle {pred.shape}; missing cells {int(np.isnan(pred).sum())}")
    out = A.summarise(pred, meas, "boltz2_affinity_value")
    out["verdict"] = A.verdict(out["P1"], out["P3"])
    out["shape"] = dict(ligands=len(cids), kinases=len(accs))
    out["censored_share"] = float((meas <= A.CENSOR_PKD).mean())
    # secondary read-out: the binary binder probability on the same axis
    out["P1_probability"] = A.primary(prob, meas)
    out["P3_probability"] = dict(point=A.med(A.within_kinase(prob, meas)))
    # baselines (plan.md §7), each compared by a paired ligand bootstrap
    rows, cols = [c["row"] for c in d["panel"]["ligands"]], [k["col"] for k in d["panel"]["kinases"]]
    rows = [r for r, c in zip(rows, d["cids"]) if c in cids]
    Ypkd = pkd(d["Y"])
    smiles = [d["lig"][c] for c in d["cids"]]
    mw = [c["mw"] for c in d["panel"]["ligands"] if c["cid"] in cids]
    bases = dict(B0_ligand_only=A.base_ligand_only(Ypkd, rows, cols),
                 B1_promiscuity=A.base_promiscuity(Ypkd, rows, cols),
                 B2_neighbour=A.base_neighbour(Ypkd, rows, cols, smiles),
                 B3_mw=A.base_mw(mw, len(cols)))
    out["baselines"] = {}
    for name, b in bases.items():
        out["baselines"][name] = dict(P1=A.primary(b, meas), P3=A.med(A.within_kinase(b, meas)),
                                      diff=A.paired_difference(pred, meas, b))
    # confidence-filtered recomputation (plan.md §9.3)
    t = pd.read_csv(TAB / "pairs_panel.csv")
    cut = t.confidence_score.median()
    piv = t.pivot_table(index="cid", columns="protein", values="confidence_score", aggfunc="last")
    conf = piv.reindex(index=[int(c) for c in cids] if piv.index.dtype != object else cids,
                       columns=accs).to_numpy(float)
    hi = np.where(conf >= cut, pred, np.nan)
    out["high_confidence"] = dict(cut=float(cut), P1=A.primary(hi, meas))
    A.save(out, "primary.json")
    print(json.dumps({k: v for k, v in out.items() if k in ("verdict", "shape", "censored_share")}, indent=1))
    print("P1", {k: round(out["P1"][k], 3) for k in ("point", "lo", "hi")},
          " P2", {k: round(out["P2"][k], 3) for k in ("point", "lo", "hi")},
          " P3", round(out["P3"]["point"], 3))
    for n, b in out["baselines"].items():
        print(f"  {n:16s} P1 {b['P1']['point']:.3f} [{b['P1']['lo']:.3f},{b['P1']['hi']:.3f}]"
              f"  diff {b['diff']['point']:+.3f} [{b['diff']['lo']:+.3f},{b['diff']['hi']:+.3f}]")
    return out


if __name__ == "__main__":
    dict(tidy=tidy, primary=primary)[sys.argv[1]]()
