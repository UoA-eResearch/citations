"""Index of TESS FFI light curves for the matched TIC IDs, from MAST's per-sector bulk download scripts (plan
section 1). Scripts are streamed and filtered, not stored; eight are fetched at once because MAST throttles each
connection (about 12 minutes per script serially). Completed sectors are saved and skipped on restart.

  lc_index.py -> data/lc_index.parquet (tic, sector, product, path, url)
"""
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
BASE = {"tess-spoc": "https://archive.stsci.edu/hlsps/tess-spoc/download_scripts/",
        "qlp": "https://archive.stsci.edu/hlsps/qlp/download_scripts/"}
PAT = {"tess-spoc": r'href="(hlsp_tess-spoc_tess_phot_s(\d{4})_tess_v1_dl-lc\.sh)"',
       "qlp": r'href="(hlsp_qlp_tess_ffi_s(\d{4})_tess_v01_llc-fits\.sh)"'}
LINE = re.compile(r"--output '([^']+)' '([^']+)'")
TICRE = re.compile(r"[_-](\d{16})[-_]")   # SPOC: _<tic>-s0001; QLP: s0006-<tic>_


def listing(product):
    html = subprocess.run(["curl", "-s", "--max-time", "120", BASE[product]], capture_output=True, text=True).stdout
    return sorted(set(re.findall(PAT[product], html)), key=lambda x: int(x[1]))


def main():
    tics = set(pd.read_parquet(D / "tic.parquet").tic.astype("int64"))
    out_f = D / "lc_index.parquet"
    prev = pd.read_parquet(out_f) if out_f.exists() else pd.DataFrame(columns=["tic", "sector", "product", "path", "url"])
    seen = set(zip(prev["product"], prev.sector.astype(int)))
    rows = [prev]
    jobs = [(product, name, sec) for product in ("tess-spoc", "qlp") for name, sec in listing(product) if (product, int(sec)) not in seen]
    print(len(jobs), "sector scripts to fetch", flush=True)

    def fetch(job):
        product, name, sec = job
        p = subprocess.run(["curl", "-s", "--max-time", "7200", "--retry", "3", BASE[product] + name], capture_output=True, text=True)
        hits = []
        for line in p.stdout.splitlines():
            m = LINE.search(line)
            if not m:
                continue
            t = TICRE.search(m.group(1))
            if t and int(t.group(1)) in tics:
                hits.append((int(t.group(1)), int(sec), product, m.group(1), m.group(2)))
        return product, sec, p.returncode, len(p.stdout), pd.DataFrame(hits, columns=["tic", "sector", "product", "path", "url"])

    with ThreadPoolExecutor(8) as ex:
        for product, sec, rc, nbytes, df in ex.map(fetch, jobs):
            if rc or nbytes == 0:
                print(product, sec, "FAILED rc", rc, flush=True); continue
            rows.append(df); pd.concat(rows).to_parquet(out_f)
            print(product, sec, len(df), "light curves", flush=True)
    x = pd.concat(rows)
    print(len(x), "light curves for", x.tic.nunique(), "stars")


if __name__ == "__main__":
    main()
