"""G4 (plan section 4, adapted in D2): our TESS rotation periods against an independent catalogue. VizieR is not
reachable from this machine, so the comparison uses Gaia DR3's own rotation-modulation periods
(gaiadr3.vari_rotation_modulation.best_rotation_period, from Gaia photometry), for every sample SB1 in that table.
Agreement: within 10%, at half or double (within 10%), or neither; the denominator is every star with both a TESS
period from our pipeline (any class with a period) and a Gaia period.

  g4_check.py -> results/tables/g4_gaia_rotation.csv, results/tables/g4_check.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from astroquery.gaia import Gaia

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
q = """SELECT r.source_id, r.best_rotation_period, r.num_segments
FROM gaiadr3.vari_rotation_modulation AS r
JOIN gaiadr3.nss_two_body_orbit AS n ON n.source_id = r.source_id
WHERE n.nss_solution_type IN ('SB1', 'SB1C')"""
import time
for attempt in range(6):
    try:
        g = Gaia.launch_job(q).get_results().to_pandas(); break      # 257 rows: a synchronous job suffices
    except Exception as e:                                   # sporadic HTTP 500s from the archive
        print("retry", attempt, str(e)[:60]); time.sleep(60 * (attempt + 1))
g.columns = [c.lower() for c in g.columns]
st = pd.read_parquet(D / "stars.parquet")
m = st[st.p_rot.notna()].merge(g, on="source_id")
r = m.p_rot / m.best_rotation_period
m["agree"] = np.select([np.abs(r - 1) < 0.1, np.abs(r - 0.5) < 0.05, np.abs(r - 2) < 0.2], ["same", "half", "double"], "neither")
m[["source_id", "tic", "cls", "teff", "period", "p_rot", "best_rotation_period", "agree"]].to_csv(T / "g4_gaia_rotation.csv", index=False)
det = m[m.cls == "detected"]
out = {"gaia_rotation_rows_for_sb1": len(g), "with_a_tess_period": len(m), "agreement_all": m.agree.value_counts().to_dict(),
       "detected_class": {"n": len(det), **det.agree.value_counts().to_dict()},
       "share_same_or_harmonic_all": round(float((m.agree != "neither").mean()), 3) if len(m) else None}
(T / "g4_check.json").write_text(json.dumps(out, indent=1) + "\n")
print(out)
