"""D8: analyses requested by the independent review (review/review.md), all after the outcomes; none changes the
preregistered verdict. Writes results/tables/review/:

  header_fingerprint.csv  ProofNet port's per-textbook `open` lines reproduced in extracted outputs, by model, condition,
                          item set (with / without a twin) and split (review issues 1, 6)
  header_by_textbook.csv  which textbook's header Kimina emits, by the item's textbook (originals)
  per_item_OTP.csv        defect copies per item on O, T and P (59 primary items): three primary models pooled, and by model
                          (issues 2, 3)
  near_D_other.csv        "other" outputs whose normalised statement is close (difflib ratio >= 0.9) to the condition's
                          defective reference, by model and condition (issue 7)
  both_equivalent.csv     outputs certified equivalent to both D and C (plan 5: logged, counted as "other"; issue 9)
  review.json             O vs P by model on the 59 items; O vs P without uninformative references (D6 applied to the
                          129-item set); greedy and verbatim counts on the 59 items for P; the normalised-recheck
                          sensitivity (recheck_near.py) when its output exists, with plan 5's both-references rule
                          applied from recheck_near_C.jsonl (issues 3, 7, 9, 11; confirmation pass)"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
CAT, TAB = RUN / "results" / "catalogue", RUN / "results" / "tables"
OUT = TAB / "review"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import lean_check as L  # noqa: E402
from classify import extract, refs, verbatim_key  # noqa: E402

norm = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731


def texts(model):
    """(key, idx) -> extracted statement (or None), for every output."""
    out = {}
    for s in map(json.loads, open(RUN / "data" / "samples" / f"{model}.jsonl")):
        for i, o in enumerate(s["outputs"] or []):
            out[(s["key"], str(i))] = extract(o["text"])
        for o in s["greedy"] or []:
            out[(s["key"], "g")] = extract(o["text"])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fz = pd.read_json(CAT / "frozen.jsonl", lines=True)
    split = pd.read_json(CAT / "all_pairs.jsonl", lines=True).set_index("item").split
    prim = fz[fz.role == "primary"]
    inc = prim[prim.set == "included"]
    inc_tw = sorted(inc[inc.N_twin.notna()].item)
    inc_p = sorted(inc[inc.paraphrase.notna()].item)
    df = pd.concat([A.outcomes(m) for m in A.MODELS])
    T = {m: texts(m) for m in A.MODELS}
    rev = {}

    # 1. header fingerprint (ProofNet items; the miniF2F header is common to many datasets and is not a fingerprint)
    pn = inc[inc.source == "proofnet"].set_index("item")
    want = {i: {norm(x) for x in L.opens_of(r.D_header)} for i, r in pn.iterrows()}
    rows = []
    for m in A.MODELS:
        for (key, idx), code in T[m].items():
            item, cond = key.rsplit("|", 1)
            if item not in pn.index or idx == "g" or code is None:
                continue
            have = {norm(x) for x in L.opens_of(code.split("theorem")[0])}
            rows.append(dict(model=m, cond=cond, twin_item=pn.loc[item].N_twin is not None and pd.notna(pn.loc[item].N_twin),
                             split=split[item], header=want[item] <= have))
    h = pd.DataFrame(rows)
    hf = h.groupby(["model", "twin_item", "cond", "split"]).header.agg(["size", "sum"]).rename(columns={"size": "extracted", "sum": "with_port_header"})
    hf["share"] = hf.with_port_header / hf.extracted
    hf.to_csv(OUT / "header_fingerprint.csv")
    # which textbook's header Kimina emits (originals), by the item's textbook
    book = lambda i: i.split("/")[1].split("|")[0]  # noqa: E731
    first = {}
    for i, r in pn.iterrows():
        ln = [norm(x) for x in L.opens_of(r.D_header) if "scoped" not in x]
        if ln:
            first.setdefault(book(i), ln[0])
    conf = []
    for (key, idx), code in T["kimina"].items():
        item, cond = key.rsplit("|", 1)
        if item not in pn.index or cond != "O" or idx == "g" or code is None:
            continue
        have = [norm(x) for x in L.opens_of(code.split("theorem")[0]) if "scoped" not in x]
        hit = [b for b, ln in first.items() if ln in have]
        conf.append(dict(item_textbook=book(item), header_of=hit[0] if hit else "none of the port's"))
    pd.DataFrame(conf).groupby(["item_textbook", "header_of"]).size().unstack(fill_value=0).to_csv(OUT / "header_by_textbook.csv")

    # 2. per-item O / T / P on the 59 primary items
    per = pd.DataFrame(dict(item=inc_tw))
    for c in "OTP":
        per[c] = A.counts(df, inc_tw, A.PRIMARY, c)
    for m in A.PRIMARY:
        for c in "OTP":
            per[f"{m}_{c}"] = A.counts(df, inc_tw, [m], c)
    per = per.merge(inc[["item", "source", "category"]], on="item")
    per["split"] = per.item.map(split)
    per[(per.O + per["T"] + per.P) > 0].sort_values(["O", "T"], ascending=False).to_csv(OUT / "per_item_OTP.csv", index=False)

    # 3. O vs P by model on the 59 items; D6 applied to the 129-item O vs P set
    rev["O_vs_P_twin_items_by_model"] = {m: A.ratio(A.counts(df, inc_tw, [m], "O"), A.counts(df, inc_tw, [m], "P"), 1)
                                         for m in A.MODELS}
    rc = pd.read_json(CAT / "refcheck.jsonl", lines=True).drop_duplicates(["item", "ref"], keep="last")
    bad = set(rc[(rc.ref == "D") & (rc.proved.astype(bool) | rc.refuted.astype(bool))].item)
    inf_p = [i for i in inc_p if i not in bad]
    rev["O_vs_P_informative_refs"] = dict(A.ratio(A.counts(df, inf_p, A.PRIMARY, "O"), A.counts(df, inf_p, A.PRIMARY, "P"), 3),
                                          excluded=sorted(set(inc_p) & bad))

    # 4. greedy and verbatim counts on the 59 items, all three conditions
    rev["greedy_twin_items"] = {c: dict(copies=int(A.counts(df, inc_tw, A.PRIMARY, c, greedy=True).sum()), n=len(inc_tw) * 3)
                                for c in "OTP"}
    rev["verbatim_twin_items"] = {c: int(A.counts(df, inc_tw, A.PRIMARY, c, "verbatim").sum()) for c in "OTP"}

    # 5. outputs certified equivalent to both references
    both = []
    for m in A.MODELS:
        cl = {json.loads(x)["uid"]: json.loads(x) for x in open(RUN / "data" / "classified" / f"{m}.jsonl")}
        for o in map(json.loads, open(RUN / "data" / "classified" / f"{m}_outputs.jsonl")):
            c = cl.get(o.get("uid"), {})
            if c.get("copy") and c.get("correct"):
                both.append(dict(model=m, item=o["key"].rsplit("|", 1)[0], cond=o["key"].rsplit("|", 1)[1], uid=o["uid"],
                                 greedy=o["idx"] == "g"))
    b = pd.DataFrame(both)
    if len(b):
        b.groupby(["item", "model"]).agg(outputs=("uid", "size"), unique=("uid", "nunique")).to_csv(OUT / "both_equivalent.csv")
    rev["both_equivalent"] = dict(outputs=len(b), unique=int(b.uid.nunique()) if len(b) else 0,
                                  items=sorted(b.item.unique()) if len(b) else [],
                                  in_primary_set=int(b.item.isin(inc_tw).sum()) if len(b) else 0)

    # 6. near-D "other" outputs (temperature samples, 59 items)
    R = refs()
    vk = {k: verbatim_key(v["D"]) for k, v in R.items()}
    d = df[df.item.isin(inc_tw) & (df.idx != "g") & (df.cls == "other")].copy()
    d["near"] = [SequenceMatcher(None, verbatim_key(T[m][(k, i)]), vk[k], autojunk=False).ratio() >= 0.9
                 for m, k, i in zip(d.model, d.key, d.idx)]
    d.groupby(["model", "cond"]).near.agg(["size", "sum"]).rename(columns={"size": "other", "sum": "near_D"}).to_csv(OUT / "near_D_other.csv")

    # 7. sensitivity: outputs that the normalising portfolio certifies as equivalent to D count as copies
    rn = OUT / "recheck_near.jsonl"
    if rn.exists():
        r = pd.read_json(rn, lines=True)
        new = set(r[r.copy_norm.fillna(False).astype(bool)].uid)
        rc_c = OUT / "recheck_near_C.jsonl"  # plan 5: an output equivalent to both references counts as "other"
        both_c = set(pd.read_json(rc_c, lines=True).query("correct_norm == True").uid) if rc_c.exists() else set()
        rev["recheck_near"] = dict(checked=len(r), errors=int(r.error.notna().sum()) if "error" in r else 0,
                                   newly_certified=len(new), also_equivalent_to_C=len(both_c) if rc_c.exists() else None)
        new -= both_c
        uid = []
        for m in A.MODELS:
            uid += [f"{m}:{json.loads(x).get('uid')}" for x in open(RUN / "data" / "classified" / f"{m}_outputs.jsonl")]
        df2 = df.copy()
        df2["full"] = uid  # outcomes() preserves the order of <model>_outputs.jsonl
        df2.loc[df2.full.isin(new) & (df2.cls == "other"), "cls"] = "copy"
        newly = df2[df2.full.isin(new) & df2.item.isin(inc_tw) & (df2.idx != "g") & df2.model.isin(A.PRIMARY)]
        rev["recheck_near"]["newly_copies_primary_by_cond"] = newly.groupby("cond").size().astype(int).to_dict()
        rev["recheck_near"]["primary"] = A.ratio(A.counts(df2, inc_tw, A.PRIMARY, "O"), A.counts(df2, inc_tw, A.PRIMARY, "T"), 3)
        rev["recheck_near"]["O_vs_P_twin_items"] = A.ratio(A.counts(df2, inc_tw, A.PRIMARY, "O"),
                                                           A.counts(df2, inc_tw, A.PRIMARY, "P"), 3)
    json.dump(rev, open(OUT / "review.json", "w"), indent=1, default=float)
    print(hf.to_string())
    print(json.dumps({k: v for k, v in rev.items() if k != "O_vs_P_twin_items_by_model"}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
