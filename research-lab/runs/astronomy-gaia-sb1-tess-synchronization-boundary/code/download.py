"""Download the indexed light curves: one file per star and sector, TESS-SPOC where it exists, otherwise QLP (plan
section 1). Files go under data/lc/<MAST path>; existing complete files are skipped. Eight parallel connections.

  download.py [limit] [product] -> data/lc/..., results/tables/download_<product>.json
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"


def chosen():
    ix = pd.read_parquet(D / "lc_index.parquet")
    ix["rank"] = (ix["product"] != "tess-spoc").astype(int)       # TESS-SPOC first
    return ix.sort_values(["tic", "sector", "rank"]).drop_duplicates(["tic", "sector"]).drop(columns="rank")


def get(row):
    out = D / "lc" / row.path
    if out.exists() and out.stat().st_size > 2880:
        with open(out, "rb") as fh:
            if fh.read(6) == b"SIMPLE":
                return "skip", out.stat().st_size
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl", "-s", "-f", "--retry", "4", "--retry-delay", "5", "--max-time", "300", "-o", str(out), row.url])
    if r.returncode or not out.exists():
        return "fail", 0
    with open(out, "rb") as fh:
        ok = fh.read(6) == b"SIMPLE"
    if not ok:
        out.unlink(); return "fail", 0
    return "ok", out.stat().st_size


def main(limit=None, product=None):
    c = chosen()
    if product:
        c = c[c["product"] == product]
    if limit and int(limit) > 0:
        c = c.sample(int(limit), random_state=1)
    rows = list(c.itertuples(index=False))
    stat = {"ok": 0, "skip": 0, "fail": 0}; size = 0
    with ThreadPoolExecutor(8) as ex:
        for i, (s, b) in enumerate(ex.map(get, rows)):
            stat[s] += 1; size += b
            if (i + 1) % 2000 == 0:
                print(i + 1, "of", len(rows), stat, f"{size / 1e9:.1f} GB", flush=True)
    out = {"chosen_files": len(rows), **stat, "gb": round(size / 1e9, 2), "by_product": c["product"].value_counts().to_dict()}
    if not (limit and int(limit) > 0):
        (T / f"download_{product or 'all'}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
