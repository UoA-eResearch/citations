"""Reviewer check 3/4: independent recomputation of 20 eligible signals with my own SQL (not the pipeline's functions):
window by file quarter; latest version per case; primary-suspect role; the drug matched (i) as the pipeline does
(ingredient, RxNorm brands, paper's string, word-bounded regex on prod_ai or drugname) and (ii) by a stricter rule
(prod_ai token begins with the ingredient, or drugname begins with the ingredient/brand) and (iii) excluding
combination products (prod_ai with a backslash); the event as the exact PT. Also a cross-boundary deduplication that
treats legacy CASE n and FAERS caseid n as the same case. Compared with data/recomputed.csv.
Read-only on data/faers.duckdb; temp tables only. Writes recompute_independent.csv."""
import re, sys, time
from pathlib import Path
import duckdb, numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import rxnorm
OUT = Path(__file__).resolve().parent
db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True); db.execute("SET threads TO 8")
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
r = pd.read_csv(RUN / "data" / "recomputed.csv", dtype={"paper": str})
d = e.merge(r.drop(columns=["ingredient", "win"]), on=["paper", "k"])
# a spread of signals: legacy-era windows, prod_ai-era windows, brand-heavy drugs, ADCs, the pipeline-check outliers, zero cells, tiny-a survivors
want = [("39759530", "hydroxychloroquine", "PEMPHIGUS"), ("40437077", "lanreotide", "CHOLELITHIASIS"), ("39696617", "cetirizine", "SOMNOLENCE"),
        ("40828435", "tenofovir", "VITAMIN D DEFICIENCY"), ("38552079", "ipilimumab", "HYPOPHYSITIS"), ("38878281", "teprotumumab", "EYELID RETRACTION"),
        ("37536976", "ponatinib", "GALLBLADDER OEDEMA"), ("40438599", "baclofen", "BASAL GANGLION DEGENERATION"), ("39081961", "lisinopril", "ANGIOEDEMA"),
        ("40567936", "ruxolitinib", "MYELOSUPPRESSION"), ("36637688", "alogliptin", "ACUTE KIDNEY INJURY")]
sel = pd.concat([d[(d.paper == p) & (d.ingredient == i) & (d.event_pt == pt)].head(1) for p, i, pt in want])
rest = d[~d.index.isin(sel.index)]
extra = pd.concat([rest[rest.ingredient.isin(["levonorgestrel", "doxycycline", "trastuzumab", "triamcinolone", "pyrimethamine", "oxybate"])].groupby("ingredient").head(1),
                   rest[rest.win.str[:4] <= "2004"].sample(3, random_state=7), rest[rest.win.str[:6] >= "2015Q1"].sample(3, random_state=7)])
sel = pd.concat([sel, extra]).drop_duplicates(["paper", "k"]).head(22)
print(len(sel), "signals selected", flush=True)

def terms(ing, drug):
    t = {ing} | set(rxnorm.brands(ing)) | {rxnorm.clean(drug).lower()}
    return sorted({x.upper() for x in t if x and len(x) >= 4})

def esc(s): return s.replace("'", "''")
wins = {}
def window(start, end, mode):
    key = (start, end, mode)
    if key in wins: return wins[key]
    name = f"rw{len(wins)}"
    if mode == "pipeline":      # latest version per (prefixed) caseid in the window
        db.execute(f"""CREATE TEMP TABLE {name} AS SELECT rid FROM (SELECT rid, row_number() OVER (PARTITION BY caseid ORDER BY version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) rn
                       FROM demo WHERE quarter BETWEEN '{start}' AND '{end}') WHERE rn = 1""")
    else:                       # cross-boundary: the case number without the L/F prefix; FAERS versions rank above legacy ones
        db.execute(f"""CREATE TEMP TABLE {name} AS SELECT rid FROM (SELECT rid, row_number() OVER (PARTITION BY substr(caseid, 2) ORDER BY src DESC, version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) rn
                       FROM demo WHERE quarter BETWEEN '{start}' AND '{end}') WHERE rn = 1""")
    n = db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
    wins[key] = (name, n); return wins[key]

rows = []
for s in sel.itertuples():
    t0 = time.time()
    T = terms(s.ingredient, s.drug); ing = s.ingredient.upper()
    pat = "(^|[^A-Z0-9])(" + "|".join(re.escape(x) for x in T) + ")([^A-Z0-9]|$)"
    m = re.match(r"(\d{4})Q(\d)-(\d{4})Q(\d)", s.win); start, end = f"{m[1]}Q{m[2]}", f"{m[3]}Q{m[4]}"
    if start < "2004Q1": start = "2004Q1"
    # drug rows (PS) for this ingredient under three matching rules
    strict_name = "(^|[^A-Z0-9])(" + "|".join(re.escape(x) for x in T) + ")"   # name begins with the term (after a boundary) - same as pipeline minus trailing boundary
    db.execute("DROP TABLE IF EXISTS rd")
    db.execute(f"""CREATE TEMP TABLE rd AS
        SELECT rid,
               bool_or(regexp_matches(coalesce(prod_ai,''), '{esc(pat)}') OR regexp_matches(coalesce(drugname,''), '{esc(pat)}')) AS m_pipe,
               bool_or(list_has_any(list_transform(string_split(coalesce(prod_ai,''), '\\'), x -> trim(x) LIKE '{esc(ing)}%'), [true])
                       OR trim(coalesce(drugname,'')) LIKE '{esc(ing)}%'
                       OR {" OR ".join(f"trim(coalesce(drugname,'')) LIKE '{esc(b)}%'" for b in T)}) AS m_strict,
               bool_or((regexp_matches(coalesce(prod_ai,''), '{esc(pat)}') AND NOT contains(prod_ai, '\\'))
                       OR (coalesce(prod_ai,'') = '' AND regexp_matches(coalesce(drugname,''), '{esc(pat)}'))) AS m_nocombo
        FROM drug WHERE role = 'PS' GROUP BY rid""")
    db.execute("DROP TABLE IF EXISTS re_")
    db.execute(f"CREATE TEMP TABLE re_ AS SELECT DISTINCT rid FROM reac WHERE pt = '{esc(s.event_pt)}'")
    out = dict(paper=s.paper, k=s.k, ingredient=s.ingredient, drug=s.drug, event_pt=s.event_pt, win=s.win, n_terms=len(T),
               pl_a=s.primary_a, pl_b=s.primary_b, pl_c=s.primary_c, pl_d=s.primary_d, pl_ror=s.primary_ror, published=s.estimate)
    for mode in ("pipeline", "crossboundary"):
        w, n = window(start, end, mode)
        for rule in (("pipe", "m_pipe"), ("strict", "m_strict"), ("nocombo", "m_nocombo")):
            if mode == "crossboundary" and rule[0] != "pipe": continue
            a, nd, ne = db.execute(f"""SELECT (SELECT count(*) FROM rd JOIN {w} USING (rid) JOIN re_ USING (rid) WHERE {rule[1]}),
                                              (SELECT count(*) FROM rd JOIN {w} USING (rid) WHERE {rule[1]}),
                                              (SELECT count(*) FROM re_ JOIN {w} USING (rid))""").fetchone()
            b, c, dd = nd - a, ne - a, n - nd - ne + a
            ror = (a / b) / (c / dd) if min(a, b, c, dd) > 0 else np.nan
            tag = f"{mode}_{rule[0]}" if mode == "crossboundary" else rule[0]
            out.update({f"{tag}_a": a, f"{tag}_b": b, f"{tag}_c": c, f"{tag}_n": n, f"{tag}_ror": ror})
    rows.append(out); print(s.ingredient, s.event_pt, s.win, "pipeline a:", out["pl_a"], "mine:", out["pipe_a"], "strict:", out["strict_a"], "nocombo:", out["nocombo_a"], "xb:", out["crossboundary_pipe_a"], f"{time.time()-t0:.0f}s", flush=True)
res = pd.DataFrame(rows); res.to_csv(OUT / "recompute_independent.csv", index=False)
res["match_a"] = res.pl_a == res.pipe_a; print("a identical to pipeline:", int(res.match_a.sum()), "of", len(res))
pd.set_option("display.width", 250)
print(res[["ingredient", "event_pt", "win", "pl_a", "pl_b", "pl_ror", "pipe_a", "pipe_b", "pipe_c", "pipe_ror", "strict_a", "strict_b", "strict_ror", "nocombo_a", "nocombo_b", "nocombo_ror",
           "crossboundary_pipe_a", "crossboundary_pipe_b", "crossboundary_pipe_n", "crossboundary_pipe_ror", "published"]].round(2).to_string(index=False))
