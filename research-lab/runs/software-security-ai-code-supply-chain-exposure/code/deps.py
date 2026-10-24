"""Resolved dependency graphs of each top package's latest version from deps.dev v3 (plan section 3)
-> data/interim/graphs.parquet (root eco, root name, node name, node version; one row per node, root included)."""
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
SYS = {"npm": "npm", "pypi": "pypi"}


def graph(args):
    eco, name, ver = args
    url = (f"https://api.deps.dev/v3/systems/{SYS[eco]}/packages/{urllib.parse.quote(name, safe='')}"
           f"/versions/{urllib.parse.quote(str(ver), safe='')}:dependencies")
    for k in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                d = json.load(r)
            return eco, name, [(n["versionKey"]["name"], n["versionKey"]["version"]) for n in d.get("nodes", [])], None
        except urllib.error.HTTPError as e:
            if e.code in (404, 400):
                return eco, name, None, e.code
            time.sleep(2 ** k)
        except Exception:
            time.sleep(2 ** k)
    return eco, name, None, "error"


if __name__ == "__main__":
    P = pd.read_parquet(INT / "packages.parquet")
    jobs = [(r.eco, r.name, r.latest) for r in P.itertuples() if r.latest]
    rows, status = [], []
    with ThreadPoolExecutor(8) as ex:
        for k, (eco, name, nodes, err) in enumerate(ex.map(graph, jobs), 1):
            status.append({"eco": eco, "name": name, "ok": nodes is not None, "err": str(err) if err else ""})
            for nn, nv in nodes or []:
                rows.append({"eco": eco, "root": name, "node": nn, "node_version": nv})
            if k % 2000 == 0:
                print(k, flush=True)
    pd.DataFrame(rows).to_parquet(INT / "graphs.parquet", index=False)
    pd.DataFrame(status).to_parquet(INT / "graph_status.parquet", index=False)
    s = pd.DataFrame(status)
    print(s.groupby("eco").ok.agg(["sum", "size"]).to_string())
