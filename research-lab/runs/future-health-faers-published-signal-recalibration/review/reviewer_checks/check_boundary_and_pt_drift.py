"""Reviewer check 4/3: (a) case overlap across the 2012Q3/2012Q4 legacy->FAERS boundary (the pipeline prefixes caseid
with L/F so the same case number is never deduplicated across it); (b) MedDRA PT version drift: first and last quarter
each signal PT appears in reac, against the signal's window. Read-only on data/faers.duckdb."""
import re, sys
from pathlib import Path
import duckdb, pandas as pd
RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True)
db.execute("SET threads TO 8")
# (a) boundary overlap
r = db.execute("""
WITH L AS (SELECT DISTINCT substr(caseid, 2) AS cno FROM demo WHERE src='L'),
     F AS (SELECT DISTINCT substr(caseid, 2) AS cno FROM demo WHERE src='F')
SELECT (SELECT count(*) FROM L), (SELECT count(*) FROM F), (SELECT count(*) FROM L JOIN F USING (cno))""").fetchone()
print("legacy distinct cases", r[0], "| FAERS distinct cases", r[1], "| case numbers in both", r[2])
# how many legacy cases (latest legacy version) have a FAERS continuation, by legacy quarter of the latest version
rows = db.execute("""
WITH L AS (SELECT caseid, substr(caseid,2) cno, max(quarter) lastq FROM demo WHERE src='L' GROUP BY 1,2),
     F AS (SELECT DISTINCT substr(caseid, 2) AS cno FROM demo WHERE src='F')
SELECT lastq, count(*) n, sum(CASE WHEN F.cno IS NOT NULL THEN 1 ELSE 0 END) overlap FROM L LEFT JOIN F USING (cno) GROUP BY 1 ORDER BY 1""").fetchall()
df = pd.DataFrame(rows, columns=["legacy_last_quarter", "legacy_cases", "with_faers_continuation"])
df["share"] = (df.with_faers_continuation / df.legacy_cases).round(4)
print(df.tail(12).to_string(index=False))
df.to_csv(OUT / "boundary_overlap_by_quarter.csv", index=False)
# (b) PT drift for the signal PTs
s = pd.read_csv(RUN / "results" / "tables" / "signals_results.csv", dtype={"paper": str})
pts = sorted(set(s.event_pt))
db.execute("CREATE TEMP TABLE sigpt AS SELECT * FROM (VALUES " + ",".join("('" + p.replace("'", "''") + "')" for p in pts) + ") t(pt)")
rows = db.execute("""SELECT r.pt, min(d.quarter) firstq, max(d.quarter) lastq, count(*) n,
   count(DISTINCT d.quarter) nq FROM reac r JOIN sigpt USING (pt) JOIN demo d USING (rid) GROUP BY 1 ORDER BY 1""").fetchall()
pt = pd.DataFrame(rows, columns=["pt", "firstq", "lastq", "n_rows", "n_quarters"])
nq_total = db.execute("SELECT count(DISTINCT quarter) FROM demo").fetchone()[0]
m = s[["paper", "k", "ingredient", "event_pt", "win", "primary_a", "primary_c", "primary_ror", "primary_survive_mle", "estimate"]].merge(pt, left_on="event_pt", right_on="pt", how="left")
m["win_start"] = m.win.str[:6].str.replace(r"^(19|200[0-3]).*", "2004Q1", regex=True)
m["win_end"] = m.win.str[-6:]
m["pt_first_after_start"] = m.firstq > m.win_start
m["pt_last_before_end"] = m.lastq < m.win_end
m["pt_quarters_missing"] = nq_total - m.n_quarters
print("\nsignal PTs:", len(pts), "| PT first appears after window start:", int(m.pt_first_after_start.sum()),
      "| PT last appears before window end:", int(m.pt_last_before_end.sum()), "| PT present in <80 of 90 quarters:", int((m.n_quarters < 80).sum()))
cols = ["paper", "ingredient", "event_pt", "win", "firstq", "lastq", "n_quarters", "primary_a", "primary_c", "primary_ror", "estimate", "primary_survive_mle"]
print(m[m.pt_first_after_start | m.pt_last_before_end | (m.n_quarters < 80)][cols].sort_values("n_quarters").to_string(index=False))
m[cols + ["pt_first_after_start", "pt_last_before_end"]].to_csv(OUT / "pt_version_drift.csv", index=False)
