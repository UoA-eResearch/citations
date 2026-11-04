"""G3: three binaries traced from the Gaia orbit through each TESS sector's periodogram to their class (one per
outcome: synchronized, sub-synchronous, ellipsoidal-or-double-spot), chosen as the first by Gaia source_id among
cool stars (4,000-6,200 K) with P_orb < 10 d and at least two detecting sectors.

  g3_traces.py -> results/tables/g3_traces.json
"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
st = pd.read_parquet(D / "stars.parquet"); sp = pd.read_parquet(D / "sector_periods.parquet")
sp = sp[sp["product"] == "tess-spoc"]
pool = st[st.teff.between(4000, 6200) & (st.period < 10) & (st.n_sectors_det >= 2)].sort_values("source_id")
picks = {"synchronized": pool[pool.sync_state == "synchronized"], "sub-synchronous": pool[pool.sync_state == "sub"],
         "ellipsoidal_or_double_spot": pool[pool.cls == "ellipsoidal_or_double_spot"]}
out = {}
for k, c in picks.items():
    r = c.iloc[0]; s = sp[sp.tic == r.tic].sort_values("sector")
    out[k] = {"gaia_source_id": int(r.source_id), "tic": int(r.tic), "teff": round(float(r.teff)), "Tmag": round(float(r.Tmag), 2),
              "P_orb_d": round(float(r.period), 4), "e": None if pd.isna(r.eccentricity) else round(float(r.eccentricity), 3),
              "K1_kms": round(float(r.semi_amplitude_primary), 1), "P_ps_d": round(float(r.p_ps), 4),
              "sectors": [{"sector": int(x.sector), "P_ls": round(float(x.p_ls), 3), "P_after_acf": round(float(x.p), 3), "fap": float(f"{x.fap:.1e}"),
                           "amp_ppt": round(float(x.amp) * 1e3, 2), "n_pulse": int(x.n_pulse)} for x in s.itertuples()],
              "star_P_rot_d": round(float(r.p_rot), 3), "amp_ppt": round(float(r.amp) * 1e3, 2), "beaming_ppt": round(float(r.beam_amp) * 1e3, 3),
              "class": r.cls, "state": r.sync_state}
(T / "g3_traces.json").write_text(json.dumps(out, indent=1) + "\n")
for k, v in out.items():
    print(k, {a: b for a, b in v.items() if a != "sectors"}, "| sectors:", [(x["sector"], x["P_ls"], x["fap"]) for x in v["sectors"]][:6])
