"""G2 coverage stages and G3 hand traces (written after the results).
Three stars (a recovered known system, a candidate, a random eligible star) are re-fetched from IRSA and the
short-dip statistics recomputed with plain loops, independently of detect.py's vectorised code.
-> results/tables/coverage.json (stages light_curves, eligible), results/tables/handtrace.json"""
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T, D = RUN / "results" / "tables", RUN / "data"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

s = pd.read_parquet(D / "sample.parquet")
d = pd.read_parquet(T / "detect.parquet")
c = Coverage("light_curves", T / "coverage.json")
c.add_counts(ok=int(len(d)), drops={"no ZTF object or no good epochs within 2 arcsec": int(len(s) - len(d) - 13), "query failed": 13})
c.save()
c2 = Coverage("eligible", T / "coverage.json")
c2.add_counts(ok=int((d.n_epochs >= 100).sum()), drops={"fewer than 100 good epochs": int((d.n_epochs < 100).sum())})
c2.save()
k = pd.read_csv(T / "known_systems.csv")
cand = pd.read_csv(T / "candidates.csv")
rng = np.random.default_rng(3)
e = d[(d.n_epochs >= 100)]
picks = {"known: WD 1145+017": int(k[k.name == "WD 1145+017"].gaia_dr3_source_id_in_sample.iloc[0]),
         "candidate (largest excess)": int(cand.sort_values("excess").source_id.iloc[-1]),
         "random eligible star": int(e.source_id.iloc[rng.integers(len(e))])}
out = {}
for lab, sid in picks.items():
    r = s[s.source_id == sid].iloc[0]
    url = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{r.ra2019:.6f}%20{r.dec2019:.6f}%200.000556&FORMAT=csv"
    x = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=300).read().decode()))
    x = x[(x.catflags == 0) & (x.magerr < 0.25)]
    faint = bright = 0
    nights = set()
    n = 0
    for f, g in x.groupby("filtercode"):
        best = g.groupby("oid").size().idxmax()
        g = g[g.oid == best]
        vals = sorted(g.mag.tolist())
        med = vals[len(vals) // 2] if len(vals) % 2 else 0.5 * (vals[len(vals) // 2 - 1] + vals[len(vals) // 2])
        dev = sorted(abs(v - med) for v in vals)
        mad = dev[len(dev) // 2] if len(dev) % 2 else 0.5 * (dev[len(dev) // 2 - 1] + dev[len(dev) // 2])
        sig = 1.4826 * mad
        for m_, t_ in zip(g.mag, g.mjd):
            n += 1
            if m_ > med + 3 * sig:
                faint += 1; nights.add(int(np.floor(t_)))
            elif m_ < med - 3 * sig:
                bright += 1
    row = d[d.source_id == sid].iloc[0]
    out[lab] = {"source_id": str(sid), "hand": {"epochs": n, "faint": faint, "bright": bright, "excess": faint - bright, "faint_nights": len(nights)},
                "pipeline": {"epochs": int(row.n_epochs), "faint": int(row.faint), "bright": int(row.bright), "excess": int(row.excess),
                             "faint_nights": int(row.faint_nights), "short": bool(row.short), "long": bool(row.long)}}
    print(lab, out[lab], flush=True)
(T / "handtrace.json").write_text(json.dumps(out, indent=1) + "\n")
