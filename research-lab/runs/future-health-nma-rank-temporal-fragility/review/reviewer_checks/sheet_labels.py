"""Extract, for every eligible network: catalogue direction label, the sheet's own direction label(s) (header or cell
'Harmful'/'Beneficial'/'Harm'/'Benefit'), the sheet's 'Outcome:' text, catalogue outcome fields, treatment names,
and a data-driven direction cue: mean outcome in placebo/control-like arms vs other arms."""
import json, re, pandas as pd, numpy as np
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
cat = pd.read_csv(f"{RUN}/data/raw/catalog.csv", sep=";", dtype=str).set_index("Record ID")
dr = pd.read_csv(f"{RUN}/results/tables/direction.csv", dtype={"record": str}).set_index("record")
ss = pd.read_csv(f"{RUN}/data/std_summary.csv", dtype={"record": str}).set_index("record")
hold = pd.read_csv(f"{RUN}/data/holdouts.csv", dtype={"record": str})
CTRL = re.compile(r"placebo|sham|no treat|no-treat|usual care|standard care|control|waitlist|wait-list|wait list|untreated|observation|supportive|no intervention|conventional|best supportive", re.I)
rows = []
for rec in hold.record:
    raw = pd.read_excel(f"{RUN}/data/raw/datasets/{rec}.xlsx")
    hdr = [str(c).strip() for c in raw.columns]
    labels = set(); outcome_txt = []
    for h in hdr:
        hl = h.lower()
        if hl.startswith("harm") or hl.startswith("benef"): labels.add(h)
        if hl.startswith("outcome"): outcome_txt.append(h)
    for col in raw.columns:
        for v in raw[col].dropna():
            if isinstance(v, str):
                vl = v.strip().lower()
                if vl.startswith("harm") or vl.startswith("benef"): labels.add(v.strip()[:80])
                if vl.startswith("outcome"): outcome_txt.append(v.strip()[:160])
    # outcome text may also be in the cell to the right of an 'Outcome:' header
    for j, h in enumerate(hdr):
        if h.lower().startswith("outcome") and j + 1 < len(hdr):
            v = raw.iloc[0, j + 1] if len(raw) else None
            if isinstance(v, str): outcome_txt.append(v[:160])
    trt = json.load(open(f"{RUN}/data/std/{rec}.trt.json"))
    d = pd.read_csv(f"{RUN}/data/std/{rec}.csv", dtype={"study": str})
    cue = ""
    if "t" in d and trt:
        ctrl = {int(k) for k, v in trt.items() if CTRL.search(v)}
        if ctrl:
            d["is_ctrl"] = d.t.astype(int).isin(ctrl)
            if "y" in d:
                g = d.groupby("is_ctrl").y.mean()
            elif "time" in d:
                d["rate"] = d.r / d.time; g = d.groupby("is_ctrl").rate.mean()
            else:
                d["p"] = d.r / d.n; g = d.groupby("is_ctrl").p.mean()
            if True in g.index and False in g.index:
                cue = f"ctrl={g[True]:.3g} active={g[False]:.3g} ({'ctrl lower' if g[True] < g[False] else 'ctrl higher'})"
            ctrl_names = "; ".join(trt[str(k)] for k in sorted(ctrl))
        else:
            ctrl_names = ""
    else:
        ctrl_names = ""
    rows.append(dict(record=rec, format=ss.loc[rec, "format"], type=ss.loc[rec, "type"], measure=ss.loc[rec, "measure"],
                     catalogue=dr.loc[rec, "catalogue"], small_values=dr.loc[rec, "small_values"], confidence=dr.loc[rec, "confidence"],
                     sheet_labels=" | ".join(sorted(labels)), sheet_outcome=" | ".join(dict.fromkeys(outcome_txt)),
                     cat_primary_outcome=cat.loc[rec, "Primary Outcome"], cat_outcome_desc=cat.loc[rec, "Description of the outcome(s)"],
                     cat_control=cat.loc[rec, "Control intervetion"], eff_safety=cat.loc[rec, "Effectiveness-Safety"],
                     title=cat.loc[rec, "Title"], ctrl_arms=ctrl_names, data_cue=cue,
                     trts="; ".join(f"{k}={v[:30]}" for k, v in sorted(trt.items(), key=lambda x: int(x[0])))[:400]))
df = pd.DataFrame(rows)
df.to_csv(f"{RUN}/review/reviewer_checks/sheet_labels.csv", index=False)
print(len(df), "eligible networks")
def sheet_dir(s):
    s = s.lower()
    h = "harm" in s; b = "benef" in s
    return "both" if h and b else "harmful" if h else "beneficial" if b else "none"
df["sheet_dir"] = df.sheet_labels.map(sheet_dir)
print(pd.crosstab([df.format, df.catalogue], df.sheet_dir))
dis = df[(df.sheet_dir != "none") & (df.sheet_dir != "both") & (df.sheet_dir != df.catalogue.str.lower())]
print("\ncatalogue vs sheet label disagreements:", len(dis))
print(dis[["record", "format", "type", "catalogue", "sheet_dir", "small_values", "cat_primary_outcome"]].to_string())
