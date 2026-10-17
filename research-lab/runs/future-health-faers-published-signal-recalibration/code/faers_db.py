"""Build the FAERS DuckDB database from the quarterly ASCII extracts (plan section 3).

Tables (data/faers.duckdb):
  demo(rid, src, caseid, version, fda_dt, quarter)   rid = 'L'||ISR (legacy AERS) or 'F'||primaryid (FAERS)
  drug(rid, role, drugname, prod_ai)                  upper-cased, trimmed; prod_ai is null before 2014Q3
  reac(rid, pt)                                       upper-cased PT
Legacy AERS has no case version: the ISR orders versions (a later ISR is a later version)."""
import shutil
import sys
import zipfile
from pathlib import Path

import duckdb

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw" / "faers"
TXT = RUN / "data" / "raw" / "faers_txt"


def members(z, kind):
    return [n for n in z.namelist() if Path(n).name.upper().startswith(kind) and n.upper().endswith(".TXT")]


def rd(path):
    return (f"read_csv('{path}', delim='$', header=true, all_varchar=true, quote='', escape='', null_padding=true, "
            f"ignore_errors=true, normalize_names=true)")


def main():
    db = duckdb.connect(str(RUN / "data" / "faers.duckdb"))
    db.execute("CREATE TABLE IF NOT EXISTS demo(rid VARCHAR, src VARCHAR, caseid VARCHAR, version BIGINT, fda_dt VARCHAR, quarter VARCHAR)")
    db.execute("CREATE TABLE IF NOT EXISTS drug(rid VARCHAR, role VARCHAR, drugname VARCHAR, prod_ai VARCHAR)")
    db.execute("CREATE TABLE IF NOT EXISTS reac(rid VARCHAR, pt VARCHAR)")
    done = {r[0] for r in db.execute("SELECT DISTINCT quarter FROM demo").fetchall()}
    for z in sorted(RAW.glob("*_ascii_*.zip")):
        kind, q = z.name.split("_")[0], z.stem.split("_")[-1].upper()        # aers/faers, 2004Q1
        if q in done:
            continue
        d = TXT / q; d.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as zz:
            paths = {}
            for k in ("DEMO", "DRUG", "REAC"):
                m = members(zz, k)
                assert m, f"{z.name}: no {k}"
                paths[k] = d / Path(m[0]).name
                with zz.open(m[0]) as src, open(paths[k], "wb") as dst:
                    shutil.copyfileobj(src, dst)
        if kind == "aers":
            db.execute(f"INSERT INTO demo SELECT 'L'||isr, 'L', 'L'||_case, TRY_CAST(isr AS BIGINT), fda_dt, '{q}' FROM {rd(paths['DEMO'])}")
            db.execute(f"INSERT INTO drug SELECT 'L'||isr, upper(trim(role_cod)), upper(trim(drugname)), NULL FROM {rd(paths['DRUG'])}")
            db.execute(f"INSERT INTO reac SELECT 'L'||isr, upper(trim(pt)) FROM {rd(paths['REAC'])}")
        else:
            db.execute(f"INSERT INTO demo SELECT 'F'||primaryid, 'F', 'F'||caseid, TRY_CAST(caseversion AS BIGINT), fda_dt, '{q}' FROM {rd(paths['DEMO'])}")
            cols = [r[0] for r in db.execute(f"DESCRIBE SELECT * FROM {rd(paths['DRUG'])}").fetchall()]
            pa = "upper(trim(prod_ai))" if "prod_ai" in cols else "NULL"
            db.execute(f"INSERT INTO drug SELECT 'F'||primaryid, upper(trim(role_cod)), upper(trim(drugname)), {pa} FROM {rd(paths['DRUG'])}")
            db.execute(f"INSERT INTO reac SELECT 'F'||primaryid, upper(trim(pt)) FROM {rd(paths['REAC'])}")
        shutil.rmtree(d)
        n = db.execute(f"SELECT count(*) FROM demo WHERE quarter='{q}'").fetchone()[0]
        print(q, kind, n, "reports", flush=True)
    for t in ("demo", "drug", "reac"):
        print(t, db.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
    db.close()


if __name__ == "__main__":
    sys.exit(main())
