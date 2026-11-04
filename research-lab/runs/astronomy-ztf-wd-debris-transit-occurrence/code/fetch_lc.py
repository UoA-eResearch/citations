"""ZTF DR light curves for the sample (plan section 1), one IRSA API query per white dwarf: a 2-arcsec cone at the
epoch-2019.0 position, all filters. Per filter, the ZTF object with the most good epochs (catflags = 0,
magerr < 0.25) is kept. Shards of 2,000 stars are written to data/lc/; finished shards are skipped on restart.

  fetch_lc.py [workers] [limit] -> data/lc/shard_NNNN.parquet (source_id, filt, mjd, mag, magerr), data/lc/shard_NNNN.done
"""
import io
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{ra:.6f}%20{dec:.6f}%200.000556&FORMAT=csv"
SHARD = 2000


def one(r):
    for attempt in range(4):
        try:
            txt = urllib.request.urlopen(URL.format(ra=r.ra2019, dec=r.dec2019), timeout=120).read().decode()
            break
        except Exception:
            time.sleep(10 * (attempt + 1))
    else:
        return r.source_id, None
    if not txt.startswith("oid"):
        return r.source_id, pd.DataFrame()
    x = pd.read_csv(io.StringIO(txt), usecols=["oid", "mjd", "mag", "magerr", "catflags", "filtercode"])
    x = x[(x.catflags == 0) & (x.magerr < 0.25)]
    if x.empty:
        return r.source_id, x
    best = x.groupby(["filtercode", "oid"]).size().reset_index(name="n").sort_values("n", ascending=False).drop_duplicates("filtercode")
    x = x.merge(best[["filtercode", "oid"]], on=["filtercode", "oid"])
    return r.source_id, x.assign(source_id=r.source_id).rename(columns={"filtercode": "filt"})[["source_id", "filt", "mjd", "mag", "magerr"]]


def main(workers=8, limit=0):
    s = pd.read_parquet(D / "sample.parquet").sort_values("source_id").reset_index(drop=True)
    if limit:
        s = s.head(limit)
    (D / "lc").mkdir(exist_ok=True)
    for k in range(0, len(s), SHARD):
        done = D / "lc" / f"shard_{k // SHARD:04d}.done"
        if done.exists():
            continue
        part = s.iloc[k:k + SHARD]
        with ThreadPoolExecutor(workers) as ex:
            res = list(ex.map(one, part.itertuples(index=False)))
        frames = [x for _, x in res if x is not None and len(x)]
        failed = [sid for sid, x in res if x is None]
        (pd.concat(frames) if frames else pd.DataFrame(columns=["source_id", "filt", "mjd", "mag", "magerr"])).to_parquet(D / "lc" / f"shard_{k // SHARD:04d}.parquet")
        done.write_text(f"{len(part)} queried, {len(failed)} failed\n" + "\n".join(map(str, failed)))
        print(time.strftime("%H:%M:%S"), "shard", k // SHARD, len(part), "stars,", len(failed), "failed", flush=True)


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
