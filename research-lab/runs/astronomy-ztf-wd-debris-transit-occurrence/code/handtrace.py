"""G2 coverage stages and G3 hand traces (written after the results).
Stars are re-fetched from IRSA and the rule statistics recomputed with plain loops, independently of detect.py's
vectorised code: two chosen stars (a recovered known system and the largest-excess candidate) and two random ones (a
random eligible star and a random long-only candidate, whose long-rule low bins are also traced).
D3 (after the confirmation pass): g and r only, as the pipeline since D2 (the first traces used every filter; kept as
handtrace_v1_allfilters.json); the failed-query count is read from the fetch logs (.done files), not hard-coded; the
long-only candidate is added.
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
failed = sum(int(f.read_text().split("\n")[0].split(", ")[1].split()[0]) for f in sorted((D / "lc").glob("shard_*.done")))
c = Coverage("light_curves", T / "coverage.json")
c.add_counts(ok=int(len(d)), drops={"no ZTF g/r object or no good g/r epochs within 2 arcsec": int(len(s) - len(d) - failed),
                                    "query failed": failed})
c.save()
c2 = Coverage("eligible", T / "coverage.json")
c2.add_counts(ok=int((d.n_epochs >= 100).sum()), drops={"fewer than 100 good epochs": int((d.n_epochs < 100).sum())})
c2.save()
k = pd.read_csv(T / "known_systems.csv")
cand = pd.read_csv(T / "candidates.csv")
rng = np.random.default_rng(3)
e = d[(d.n_epochs >= 100)]
longonly = cand[cand.long & ~cand.short].sort_values("source_id")
picks = {"chosen - known: WD 1145+017": int(k[k.name == "WD 1145+017"].gaia_dr3_source_id_in_sample.iloc[0]),
         "chosen - candidate (largest excess)": int(cand.sort_values("excess").source_id.iloc[-1]),
         "random eligible star": int(e.source_id.iloc[rng.integers(len(e))]),
         "random long-only candidate": int(longonly.source_id.iloc[np.random.default_rng(20261110).integers(len(longonly))])}
out = {}
for lab, sid in picks.items():
    r = s[s.source_id == sid].iloc[0]
    url = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{r.ra2019:.6f}%20{r.dec2019:.6f}%200.000556&FORMAT=csv"
    x = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=300).read().decode()))
    x = x[(x.catflags == 0) & (x.magerr < 0.25) & x.filtercode.isin(["zg", "zr"])]
    faint = bright = 0
    nights = set()
    n = 0
    kept = []
    for f, g in x.groupby("filtercode"):
        best = g.groupby("oid").size().idxmax()
        g = g[g.oid == best]
        kept.append(g)
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
    # long rule with plain loops: flux relative to each filter's median, pooled median, 30-day bins from the first epoch
    g = pd.concat(kept)
    meds = {}
    for f in g.filtercode.unique():
        v = sorted(g[g.filtercode == f].mag.tolist())
        meds[f] = v[len(v) // 2] if len(v) % 2 else 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2])
    rel = [10 ** (-0.4 * (m_ - meds[f])) for m_, f in zip(g.mag, g.filtercode)]
    rs = sorted(rel)
    gmed = rs[len(rs) // 2] if len(rs) % 2 else 0.5 * (rs[len(rs) // 2 - 1] + rs[len(rs) // 2])
    t0 = min(g.mjd)
    bins = {}
    for r_, t_ in zip(rel, g.mjd):
        bins.setdefault(int((t_ - t0) // 30), []).append(r_)
    low = []
    for b_, xs in sorted(bins.items()):
        if len(xs) < 5:
            continue
        mu = sum(xs) / len(xs)
        se = (sum((v - mu) ** 2 for v in xs) / (len(xs) - 1)) ** 0.5 / len(xs) ** 0.5
        xs2 = sorted(xs)
        med = xs2[len(xs2) // 2] if len(xs2) % 2 else 0.5 * (xs2[len(xs2) // 2 - 1] + xs2[len(xs2) // 2])
        if gmed - med > 5 * se and gmed - med >= 0.05:
            low.append({"bin": b_, "epochs": len(xs), "depth": round(gmed - med, 4), "z": round((gmed - med) / se, 1)})
    row = d[d.source_id == sid].iloc[0]
    out[lab] = {"source_id": str(sid), "hand": {"epochs": n, "faint": faint, "bright": bright, "excess": faint - bright, "faint_nights": len(nights),
                                                "low_bins": len(low), "low_bin_detail": low},
                "pipeline": {"epochs": int(row.n_epochs), "faint": int(row.faint), "bright": int(row.bright), "excess": int(row.excess),
                             "faint_nights": int(row.faint_nights), "low_bins": int(row.low_bins),
                             "short": bool(row.short), "long": bool(row.long)}}
    print(lab, out[lab], flush=True)
(T / "handtrace.json").write_text(json.dumps(out, indent=1) + "\n")
print("failed queries from .done files:", failed)
