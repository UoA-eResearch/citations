"""G2 coverage for the graph build (added in D2): the build's filter chain re-run as counts only, per snapshot.
Every record read is kept (class record) or dropped with the first filter it fails.
-> results/tables/coverage.json stages build_v0.6, build_v0.11"""
import sys
from pathlib import Path

import duckdb

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parents[1] / "tools"))
import build as Bd  # noqa: E402
from coverage import Coverage  # noqa: E402

for v in ("0.6", "0.11"):
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    Bd.read(con, Bd.RAW / f"v{v}_interactions.tsv.gz", "rec")
    Bd.read(con, Bd.RAW / f"v{v}_refuted-interactions.tsv.gz", "ref")
    n = con.execute("SELECT count(*) FROM rec").fetchone()[0]
    con.execute(f"CREATE OR REPLACE TABLE o AS {Bd.oriented(con, 'rec')}")
    con.execute(f"CREATE OR REPLACE TABLE oref AS {Bd.oriented(con, 'ref')}")
    n_o = con.execute("SELECT count(*) FROM o").fetchone()[0]
    n_o2 = con.execute("SELECT count(*) FROM o WHERE s IS NOT NULL AND t IS NOT NULL AND s <> '' AND t <> '' AND s <> t").fetchone()[0]
    n_o3 = con.execute("""SELECT count(*) FROM o WHERE s IS NOT NULL AND t IS NOT NULL AND s <> '' AND t <> '' AND s <> t
                          AND NOT EXISTS (SELECT 1 FROM oref r WHERE r.cls = o.cls AND r.s = o.s AND r.t = o.t)""").fetchone()[0]
    cov = Coverage(f"build_v{v}", RUN / "results" / "tables" / "coverage.json")
    cov.add_counts(ok=n_o3, drops={"interaction type outside the three classes": n - n_o,
                                   "no species-level name on a side, or a self-loop": n_o - n_o2,
                                   "pair in the refuted set": n_o2 - n_o3})
    cov.save()
    print(v, n, n_o, n_o2, n_o3, flush=True)
