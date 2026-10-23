"""Graphs (plan section 1).

  build.py VERSION        data/raw/v{VERSION}_interactions.tsv.gz (+ refuted) -> data/interim/edges_v{VERSION}.parquet
                          (cls, s, t, n_records, n_citations, top_namespace, namespaces) and species_v{VERSION}.parquet
                          (species, genus, family, n_citations)

Species-level records only; interaction types mapped to three classes with direction normalised (consumer->resource,
pollinator->plant, parasite/symbiont->host); refuted records removed by (cls, s, t).
"""
import sys
from pathlib import Path

import duckdb

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
INT = RUN / "data" / "interim"
FWD = {"eats": "trophic", "preysOn": "trophic", "pollinates": "pollination", "visitsFlowersOf": "pollination",
       "parasiteOf": "host", "endoparasiteOf": "host", "ectoparasiteOf": "host", "hemiparasiteOf": "host",
       "parasitoidOf": "host", "hyperparasiteOf": "host", "pathogenOf": "host", "hasHost": "host"}
REV = {"eatenBy": "trophic", "preyedUponBy": "trophic", "pollinatedBy": "pollination", "flowersVisitedBy": "pollination",
       "hasParasite": "host", "hostOf": "host", "hasPathogen": "host", "hasParasitoid": "host"}
COLS = ["sourceTaxonSpeciesName", "sourceTaxonGenusName", "sourceTaxonFamilyName", "interactionTypeName",
        "targetTaxonSpeciesName", "targetTaxonGenusName", "targetTaxonFamilyName", "referenceCitation", "sourceNamespace"]


def read(con, path, name):
    sel = ", ".join(f'"{c}"' for c in COLS)
    con.execute(f"""CREATE OR REPLACE TABLE {name} AS SELECT {sel} FROM read_csv('{path}', delim='\t', header=true,
                    quote='', escape='', all_varchar=true, ignore_errors=true, parallel=false)""")
    con.execute(f"SELECT count(*) FROM {name}")


def oriented(con, name):
    fwd = ",".join(f"('{k}','{v}')" for k, v in FWD.items())
    rev = ",".join(f"('{k}','{v}')" for k, v in REV.items())
    con.execute(f"CREATE OR REPLACE TEMP TABLE fwd(t VARCHAR, cls VARCHAR); INSERT INTO fwd VALUES {fwd};")
    con.execute(f"CREATE OR REPLACE TEMP TABLE rev(t VARCHAR, cls VARCHAR); INSERT INTO rev VALUES {rev};")
    return f"""
      SELECT f.cls, r.sourceTaxonSpeciesName AS s, r.targetTaxonSpeciesName AS t,
             r.sourceTaxonGenusName AS sg, r.sourceTaxonFamilyName AS sf, r.targetTaxonGenusName AS tg,
             r.targetTaxonFamilyName AS tf, r.referenceCitation AS cit, r.sourceNamespace AS ns
        FROM {name} r JOIN fwd f ON r.interactionTypeName = f.t
      UNION ALL
      SELECT v.cls, r.targetTaxonSpeciesName, r.sourceTaxonSpeciesName,
             r.targetTaxonGenusName, r.targetTaxonFamilyName, r.sourceTaxonGenusName, r.sourceTaxonFamilyName,
             r.referenceCitation, r.sourceNamespace
        FROM {name} r JOIN rev v ON r.interactionTypeName = v.t"""


def main(version):
    INT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    read(con, RAW / f"v{version}_interactions.tsv.gz", "rec")
    read(con, RAW / f"v{version}_refuted-interactions.tsv.gz", "ref")
    con.execute(f"CREATE OR REPLACE TABLE o AS {oriented(con, 'rec')}")
    con.execute(f"CREATE OR REPLACE TABLE oref AS {oriented(con, 'ref')}")
    con.execute("""CREATE OR REPLACE TABLE o2 AS SELECT * FROM o
                   WHERE s IS NOT NULL AND t IS NOT NULL AND s <> '' AND t <> '' AND s <> t""")
    con.execute("""CREATE OR REPLACE TABLE refpairs AS SELECT DISTINCT cls, s, t FROM oref
                   WHERE s IS NOT NULL AND t IS NOT NULL""")
    con.execute("""CREATE OR REPLACE TABLE o3 AS SELECT o2.* FROM o2 ANTI JOIN refpairs r
                   ON o2.cls = r.cls AND o2.s = r.s AND o2.t = r.t""")
    con.execute(f"""COPY (
        WITH g AS (SELECT cls, s, t, count(*) AS n_records, count(DISTINCT cit) AS n_citations FROM o3 GROUP BY 1, 2, 3),
             nsc AS (SELECT cls, s, t, ns, count(*) AS c FROM o3 GROUP BY 1, 2, 3, 4),
             top AS (SELECT cls, s, t, arg_max(ns, c) AS top_namespace, string_agg(DISTINCT ns, '|') AS namespaces
                     FROM nsc GROUP BY 1, 2, 3)
        SELECT g.*, top.top_namespace, top.namespaces FROM g JOIN top USING (cls, s, t))
        TO '{INT / f"edges_v{version}.parquet"}' (FORMAT parquet)""")
    if True:                                   # species table for every version (rolling origins use their own)
        con.execute(f"""COPY (
            WITH sp AS (SELECT s AS species, sg AS genus, sf AS family, cit FROM o3
                        UNION ALL SELECT t, tg, tf, cit FROM o3),
                 gm AS (SELECT species, mode(genus) AS genus, mode(family) AS family, count(DISTINCT cit) AS n_citations
                        FROM sp GROUP BY 1)
            SELECT * FROM gm) TO '{INT / f"species_v{version}.parquet"}' (FORMAT parquet)""")
    n = con.execute("SELECT count(*) FROM rec").fetchone()[0]
    m = con.execute("SELECT cls, count(*) FROM o3 GROUP BY 1").fetchall()
    print(version, "records", n, "class records after filters", m, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
