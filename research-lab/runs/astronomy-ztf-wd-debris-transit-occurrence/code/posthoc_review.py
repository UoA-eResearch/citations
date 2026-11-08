"""Post hoc checks after the independent review (D2). -> results/tables/posthoc_review.json
  1. tiered lower rates: confirmed transiters only (WD 1145+017, ZTF J0139+5245, ZTF J0328-1219), plus the Guidry 2021
     candidates, and all published systems and candidates (the preregistered "known systems");
  2. long-dip flags: low 30-day bins coincident in g and r, and calendar clustering (the share of flagged stars with a
     low bin in the ten most crowded 30-day windows; the same windows' median depth in 2,000 random unflagged stars);
  3. SBSS 1232+563: a fresh IRSA query keeping every object and flag, to see where the 2023 epochs went.
"""
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import detect as Dt  # noqa: E402

T, D = RUN / "results" / "tables", RUN / "data"
p = json.load(open(T / "primary.json"))
S = p["rates"]["combined"]["sum_completeness"]
k = pd.read_csv(T / "known_systems.csv")
det = pd.read_parquet(T / "detect.parquet")
rec = set(det[(det.short.fillna(False) | det.long.fillna(False))].source_id)
k["recovered"] = k.gaia_dr3_source_id_in_sample.isin(rec)


def ci(n):
    return [(chi2.ppf(0.025, 2 * n) / 2 if n else 0) / S, chi2.ppf(0.975, 2 * (n + 1)) / 2 / S]


confirmed = {"WD 1145+017", "ZTF J0139+5245", "ZTF J0328-1219"}
guidry = {"SDSS J0107+2107", "ZTF J0347-1802", "ZTF J0923+4236", "SBSS 1232+563"}
tiers = {}
for lab, names in (("confirmed_only", confirmed), ("confirmed_plus_guidry_candidates", confirmed | guidry), ("all_published", set(k.name))):
    n = int(k[k.name.isin(names) & k.recovered].shape[0])
    tiers[lab] = {"recovered": n, "rate": n / S, "ci": ci(n)}
# 2. long-dip flags: g/r coincidence and calendar clustering
cand = pd.read_csv(T / "candidates.csv")
longc = set(cand[cand.long & ~cand.short].source_id) | set(cand[cand.long & cand.short].source_id)
lows, coinc, nboth = {}, 0, 0
quiet = det[(det.n_epochs >= 100) & ~(det.short.fillna(False) | det.long.fillna(False))].sample(2000, random_state=1).source_id.tolist()
qdepth = {}
for f in sorted((D / "lc_v2").glob("shard_*.parquet")):
    t = pd.read_parquet(f)
    t = t[t.filt.isin(["zg", "zr"])]
    for sid, g in t.groupby("source_id"):
        if sid not in longc and sid not in quiet:
            continue
        rel = np.empty(len(g))
        for fl in g.filt.unique():
            m = (g.filt == fl).to_numpy()
            rel[m] = 10 ** (-0.4 * (g.mag.to_numpy()[m] - np.median(g.mag.to_numpy()[m])))
        b = np.floor(g.mjd.to_numpy() / 30).astype(int)
        gmed = np.median(rel)
        if sid in quiet:
            for v in np.unique(b):
                x = rel[b == v]
                if len(x) >= 5:
                    qdepth.setdefault(int(v), []).append(gmed - np.median(x))
            continue
        lb = []
        for v in np.unique(b):
            m = b == v
            x = rel[m]
            if len(x) < 5:
                continue
            se = x.std(ddof=1) / np.sqrt(len(x))
            if (gmed - np.median(x)) > 5 * se and (gmed - np.median(x)) >= 0.05:
                lb.append(int(v))
                fg = g.filt.to_numpy()[m]
                xg, xr = x[fg == "zg"], x[fg == "zr"]
                if len(xg) >= 3 and len(xr) >= 3:
                    nboth += 1
                    coinc += (gmed - np.median(xg) > 0.025) and (gmed - np.median(xr) > 0.025)
        lows[sid] = lb
counts = pd.Series([v for lb in lows.values() for v in set(lb)]).value_counts()
top10 = set(counts.index[:10])
in_top = sum(1 for lb in lows.values() if set(lb) & top10)
qd = {v: float(np.median(qdepth.get(v, [np.nan]))) for v in top10}
allq = float(np.median([d for v in qdepth.values() for d in v]))
out = {"tiered_lower_rates": tiers,
       "long_flag_candidates": len(lows), "low_bins_with_3g_3r": nboth, "low_bins_low_in_both_bands": int(coinc),
       "candidates_with_a_low_bin_in_top10_windows": in_top, "top10_windows_mjd_start": sorted(int(v) * 30 for v in top10),
       "largest_window_candidates": int(counts.iloc[0]), "largest_window_mjd_start": int(counts.index[0]) * 30,
       "quiet_star_median_depth_in_top10_windows": qd, "quiet_star_median_depth_overall": allq}
# 3. SBSS 1232+563
r = k[k.name == "SBSS 1232+563"].iloc[0]
s = pd.read_parquet(D / "sample.parquet").set_index("source_id").loc[int(r.gaia_dr3_source_id_in_sample)]
url = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{s.ra2019:.6f}%20{s.dec2019:.6f}%200.000556&FORMAT=csv"
x = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=300).read().decode()))
x["era"] = np.where(x.mjd >= 60068, "2023+", "before")
out["sbss"] = {"objects": int(x.oid.nunique()), "epochs_all": int(len(x)),
               "by_object": x.groupby(["oid", "filtercode"]).size().reset_index(name="n").to_dict("records"),
               "epochs_2023_plus_all": int((x.era == "2023+").sum()),
               "epochs_2023_plus_good": int(((x.era == "2023+") & (x.catflags == 0) & (x.magerr < 0.25)).sum()),
               "catflags_2023_plus": x[x.era == "2023+"].catflags.value_counts().head(5).to_dict()}
(T / "posthoc_review.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
print(json.dumps({k_: v for k_, v in out.items() if k_ != "sbss"}, indent=1, default=float)); print(json.dumps(out["sbss"], default=float)[:900])
