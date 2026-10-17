"""Data-driven screen of the direction call for every arm-level network: find the sheet's treatment-name table with a
more tolerant search (the study's parser left many .trt.json files empty), identify placebo/control-like arms, and
compare the pooled outcome in control arms with that in the other arms. Under the call, control should usually look
worse on efficacy outcomes. Flags are for human re-adjudication, not verdicts."""
import json, re, pandas as pd, numpy as np
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
dr = pd.read_csv(f"{RUN}/results/tables/direction.csv", dtype={"record": str}).set_index("record")
hold = pd.read_csv(f"{RUN}/data/holdouts.csv", dtype={"record": str})
ss = pd.read_csv(f"{RUN}/data/std_summary.csv", dtype={"record": str}).set_index("record")
cat = pd.read_csv(f"{RUN}/data/raw/catalog.csv", sep=";", dtype=str).set_index("Record ID")
CTRL = re.compile(r"placebo|plb|pbo|sham|no treat|no-treat|usual care|standard care|^control|waitlist|wait-list|wait list|untreated|observation|supportive care|no intervention|no therapy|^none$|^nil", re.I)

def trt_table(raw):
    """Any cell equal to 'treatments' (or a header), then (number, name) pairs below/right; else any column pair of
    small integers next to strings in the unnamed area."""
    g = raw.copy(); g.columns = range(g.shape[1])
    out = {}
    cells = [(i, j) for j in range(g.shape[1]) for i, v in g[j].items() if isinstance(v, str) and v.strip().lower().rstrip(":") in ("treatments", "treatment", "treatments:")]
    cells += [(-1, j) for j, c in enumerate(raw.columns) if str(c).strip().lower().rstrip(":") in ("treatments", "treatment")]
    for i, j in cells:
        for dj in (1, 0):
            if j + dj + 1 >= g.shape[1]: continue
            for k in range(max(i + (1 if dj == 0 else 0), 0), len(g)):
                a = pd.to_numeric(pd.Series([g.iat[k, j + dj]]), errors="coerce").iat[0]; b = g.iat[k, j + dj + 1]
                if pd.notna(a) and isinstance(b, str) and float(a).is_integer(): out[int(a)] = b.strip()
                elif out: break
            if out: return out
    return out

rows = []
for rec in hold.record:
    if ss.loc[rec, "format"] == "iv": continue
    raw = pd.read_excel(f"{RUN}/data/raw/datasets/{rec}.xlsx")
    trt = trt_table(raw)
    old = json.load(open(f"{RUN}/data/std/{rec}.trt.json"))
    d = pd.read_csv(f"{RUN}/data/std/{rec}.csv", dtype={"study": str})
    ctrl = {k for k, v in trt.items() if CTRL.search(v)}
    cue = ""; ctrl_val = act_val = np.nan
    if ctrl:
        isc = d.t.astype(int).isin(ctrl)
        if "y" in d:
            # pooled mean weighted by n
            w = d.n.fillna(0); ctrl_val = np.average(d.y[isc].fillna(0), weights=w[isc]) if w[isc].sum() else np.nan; act_val = np.average(d.y[~isc].fillna(0), weights=w[~isc]) if w[~isc].sum() else np.nan
        elif "time" in d:
            ctrl_val = d.r[isc].sum() / d.time[isc].sum(); act_val = d.r[~isc].sum() / d.time[~isc].sum()
        else:
            ctrl_val = d.r[isc].sum() / d.n[isc].sum(); act_val = d.r[~isc].sum() / d.n[~isc].sum()
    sv = dr.loc[rec, "small_values"]
    # under the call, is control worse than active?
    if ctrl and np.isfinite(ctrl_val) and np.isfinite(act_val):
        ctrl_better = (ctrl_val < act_val) if sv == "good" else (ctrl_val > act_val)
        cue = "CONTROL LOOKS BETTER THAN ACTIVE UNDER THE CALL" if ctrl_better else "consistent"
    rows.append(dict(record=rec, type=ss.loc[rec, "type"], measure=ss.loc[rec, "measure"], catalogue=dr.loc[rec, "catalogue"], small_values=sv,
                     eff_safety=cat.loc[rec, "Effectiveness-Safety"], n_trt_names=len(trt), old_trt_names=len(old),
                     ctrl_arms="; ".join(trt[k][:25] for k in sorted(ctrl)), ctrl_val=ctrl_val, act_val=act_val, screen=cue,
                     primary_outcome=str(cat.loc[rec, "Primary Outcome"])[:80], outcome_desc=str(cat.loc[rec, "Description of the outcome(s)"])[:120],
                     trts="; ".join(f"{k}={v[:20]}" for k, v in sorted(trt.items()))[:300]))
df = pd.DataFrame(rows)
df.to_csv(f"{RUN}/review/reviewer_checks/arm_direction_screen.csv", index=False)
print("arm-level networks:", len(df), "; with treatment names (mine):", (df.n_trt_names > 0).sum(), "; (study's parser):", (df.old_trt_names > 0).sum())
print("with an identifiable control arm:", (df.ctrl_arms != "").sum())
print(df.screen.value_counts())
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 200)
print(df[df.screen.str.startswith("CONTROL")][["record", "type", "measure", "catalogue", "small_values", "eff_safety", "ctrl_arms", "ctrl_val", "act_val", "primary_outcome", "outcome_desc"]].to_string())
