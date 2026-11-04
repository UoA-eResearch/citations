"""G4 visual audit (plan section 4): 30 random classified stars (detected, ellipsoidal, beaming, pulsator), each
light curve from its best TESS-SPOC sector folded at the pipeline's period, with P_orb marked, in one image.

  g4_visual.py -> results/figures/g4_folded.png, results/tables/g4_visual_sample.csv
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import periods as PS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T, F = RUN / "data", RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
st = pd.read_parquet(D / "stars.parquet")
s = st[st.cls.isin(["detected", "ellipsoidal_or_double_spot", "possible_beaming", "pulsator"])].sample(30, random_state=20261105)
sp = pd.read_parquet(D / "sector_periods.parquet"); sp = sp[(sp["product"] == "tess-spoc") & (sp.fap < 1e-5)]
ix = pd.read_parquet(D / "lc_index.parquet")
fig, ax = plt.subplots(6, 5, figsize=(20, 22)); rows = []
for a, r in zip(ax.flat, s.itertuples()):
    b = sp[sp.tic == r.tic].sort_values("power", ascending=False).iloc[0]
    path = ix[(ix.tic == r.tic) & (ix.sector == b.sector) & (ix["product"] == "tess-spoc")].path.iloc[0]
    t, f = PS.load(D / "lc" / path, "tess-spoc")
    ph = (t % r.p_rot) / r.p_rot
    bins = np.linspace(0, 1, 41); mid = 0.5 * (bins[1:] + bins[:-1])
    med = [np.median(f[(ph >= lo) & (ph < hi)]) if ((ph >= lo) & (ph < hi)).any() else np.nan for lo, hi in zip(bins[:-1], bins[1:])]
    a.plot(ph, f * 1e3, ",", color="0.6"); a.plot(mid, np.array(med) * 1e3, "-", color="C3", lw=2)
    a.set_title(f"{len(rows) + 1}: TIC {int(r.tic)} {r.cls[:12]} {r.sync_state}\nP_rot {r.p_rot:.2f} d, P_orb {r.period:.2f} d, s{int(b.sector)}", fontsize=9)
    lo, hi = np.nanpercentile(f * 1e3, [1, 99]); a.set_ylim(lo, hi)
    rows.append((len(rows) + 1, int(r.tic), r.cls, r.sync_state, round(r.p_rot, 3), round(r.period, 3), int(b.sector)))
plt.tight_layout(); plt.savefig(F / "g4_folded.png", dpi=55)
pd.DataFrame(rows, columns=["panel", "tic", "class", "state", "p_rot", "p_orb", "sector"]).to_csv(T / "g4_visual_sample.csv", index=False)
print("ok")
