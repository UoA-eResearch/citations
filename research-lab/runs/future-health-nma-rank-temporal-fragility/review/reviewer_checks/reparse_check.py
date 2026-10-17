"""Independent re-parse of a random sample of included networks (plus every label-year and NATURAL network in the
sample frame) from the raw xlsx, compared with data/std/<record>.csv: studies, arms (rows), treatments, years, values.
Written from the raw sheet layout without reusing standardise.py."""
import re, json, random, numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility"
nr = pd.read_csv(f"{RUN}/results/tables/network_results.csv", dtype={"record": str})
inc = sorted(nr[nr.included == True].record) if nr.included.dtype == bool else sorted(nr[nr.included.astype(str) == "True"].record)
ss = pd.read_csv(f"{RUN}/data/std_summary.csv", dtype={"record": str}).set_index("record")
rnd = random.Random(2026)
sample = rnd.sample(inc, 22)
ly = [r for r in inc if "D1" in str(ss.loc[r, "issues"])]
sample += rnd.sample([r for r in ly if r not in sample], 6)
sample += [r for r in ["479757", "501200", "479629", "501220"] if r not in sample]
YEAR_RX = re.compile(r"(?<!\d)((?:19[5-9]|20[0-2])\d)(?!\d)")
rows = []
for rec in sample:
    raw = pd.read_excel(f"{RUN}/data/raw/datasets/{rec}.xlsx")
    std = pd.read_csv(f"{RUN}/data/std/{rec}.csv", dtype={"study": str})
    lc = {str(c).strip().lower(): c for c in raw.columns}
    idc = lc["id"]
    ycol = next((lc[k] for k in lc if k in ("year", "study year", "pub. year", "publication year")), None)
    labc = next((lc[k] for k in lc if k in ("study", "study name", "study (name)", "study (author)", "author", "study id")), None)
    fmt = ss.loc[rec, "format"]
    ids = pd.to_numeric(raw[idc], errors="coerce")
    # my own year per study: from the year column (first year in the cell) else from every year in the label (last one)
    yr = {}
    for i, sid in ids.items():
        if pd.isna(sid): continue
        v = raw.at[i, ycol] if ycol is not None else None
        y = None
        if v is not None and pd.notna(v):
            m = YEAR_RX.search(str(v)); y = int(m.group(1)) if m else None
        if y is None and ycol is None and labc is not None and pd.notna(raw.at[i, labc]):
            ms = YEAR_RX.findall(str(raw.at[i, labc])); y = int(ms[-1]) if ms else None
        if y is not None and int(sid) not in yr: yr[int(sid)] = y
    std_yr = std.groupby("study").year.first()
    std_yr = {int(float(k)): (int(v) if pd.notna(v) else None) for k, v in std_yr.items()}
    my_studies = set(int(s) for s in ids.dropna())
    year_mismatch = [s for s in my_studies if yr.get(s) != std_yr.get(s)]
    if fmt in ("long", "wide"):
        t = pd.to_numeric(raw[lc["t"]], errors="coerce")
        valid = ids.notna() & t.notna()
        my_arms = int(valid.sum()); my_trts = set(t[valid].astype(int))
        cols = [k for k in ("r", "n", "y", "sd", "time") if k in lc and k in std.columns]
        # value comparison: join on (study, t)
        mine = pd.DataFrame({"study": ids[valid].astype(int), "t": t[valid].astype(int)})
        for k in cols: mine[k] = pd.to_numeric(raw.loc[valid, lc[k]], errors="coerce").values
        mine = mine.dropna(subset=cols, how="all")
        theirs = std.copy(); theirs["study"] = theirs.study.astype(float).astype(int); theirs["t"] = theirs.t.astype(int)
        m = mine.merge(theirs, on=["study", "t"], how="outer", suffixes=("_me", "_std"), indicator=True)
        unmatched = int((m._merge != "both").sum())
        vdiff = 0
        for k in cols:
            a, b = m[f"{k}_me"], m[f"{k}_std"]
            if isinstance(a, pd.DataFrame): a = a.iloc[:, 0]
            if isinstance(b, pd.DataFrame): b = b.iloc[:, 0]
            vdiff += int((((a - b).abs() > 1e-9) & ~(a.isna() & b.isna())).sum())
        std_trts = set(std.t.astype(int))
        rows.append(dict(record=rec, format=fmt, label_year=rec in ly, studies_me=len(my_studies), studies_std=std.study.nunique(),
                         arms_me=len(mine), arms_std=len(std), trts_me=len(my_trts), trts_std=len(std_trts), trts_equal=my_trts == std_trts,
                         rows_unmatched=unmatched, value_diffs=vdiff, year_mismatches=len(year_mismatch), year_mismatch_ids=str(year_mismatch[:5]),
                         years_me=f"{min(v for v in yr.values() if v) if yr else ''}-{max(v for v in yr.values() if v) if yr else ''}", undated_me=len(my_studies - set(yr))))
    else:
        t1 = pd.to_numeric(raw[lc["t1"]], errors="coerce"); t2 = pd.to_numeric(raw[lc["t2"]], errors="coerce")
        eff = pd.to_numeric(raw[lc["effect"]], errors="coerce"); se = pd.to_numeric(raw[lc["se"]], errors="coerce")
        valid = ids.notna() & t1.notna() & t2.notna() & eff.notna()
        mine = pd.DataFrame({"study": ids[valid].astype(int), "t1": t1[valid].astype(int), "t2": t2[valid].astype(int), "TE": eff[valid].values, "seTE": se[valid].values})
        theirs = std.copy(); theirs["study"] = theirs.study.astype(float).astype(int); theirs["t1"] = theirs.t1.astype(int); theirs["t2"] = theirs.t2.astype(int)
        m = mine.merge(theirs, on=["study", "t1", "t2"], how="outer", suffixes=("_me", "_std"), indicator=True)
        unmatched = int((m._merge != "both").sum())
        natural = rec in ("479757", "501200")
        te_diff = int(((np.log(m.TE_me) if natural else m.TE_me) - m.TE_std).abs().gt(1e-6).sum())
        se_diff = int((m.seTE_me - m.seTE_std).abs().gt(1e-6).sum()) if not natural else -1
        rows.append(dict(record=rec, format=fmt, label_year=rec in ly, studies_me=len(my_studies), studies_std=std.study.nunique(), arms_me=len(mine), arms_std=len(std),
                         trts_me=len(set(mine.t1) | set(mine.t2)), trts_std=len(set(theirs.t1) | set(theirs.t2)), trts_equal=(set(mine.t1) | set(mine.t2)) == (set(theirs.t1) | set(theirs.t2)),
                         rows_unmatched=unmatched, value_diffs=te_diff + max(se_diff, 0), year_mismatches=len(year_mismatch), year_mismatch_ids=str(year_mismatch[:5]),
                         years_me=f"{min(v for v in yr.values() if v) if yr else ''}-{max(v for v in yr.values() if v) if yr else ''}", undated_me=len(my_studies - set(yr)), note="natural-scale: TE compared after log; seTE from CI not compared" if natural else ""))
df = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(df.to_string())
df.to_csv(f"{RUN}/review/reviewer_checks/reparse_check.csv", index=False)
print("\nnetworks:", len(df), "; all counts equal:", int(((df.studies_me == df.studies_std) & (df.arms_me == df.arms_std) & df.trts_equal & (df.rows_unmatched == 0) & (df.value_diffs == 0) & (df.year_mismatches == 0)).sum()))
