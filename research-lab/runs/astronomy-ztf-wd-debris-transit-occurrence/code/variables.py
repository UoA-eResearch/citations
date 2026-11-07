"""Gaia DR3 vari_classifier_result for the flagged stars (plan section 0: remove ECL, CV, RS, SOLAR_LIKE).
-> results/tables/flagged_gaia_vari.csv"""
import time
from pathlib import Path

import pandas as pd
from astroquery.gaia import Gaia

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
d = pd.read_parquet(T / "detect.parquet")
f = d[(d.n_epochs >= 100) & (d.short.fillna(False) | d.long.fillna(False))].source_id.astype(int).tolist()
rows = []
for i in range(0, len(f), 300):
    ids = ",".join(str(x) for x in f[i:i + 300])
    q = f"SELECT source_id, best_class_name, best_class_score FROM gaiadr3.vari_classifier_result WHERE source_id IN ({ids})"
    for attempt in range(8):                     # the archive rejects synchronous jobs when overloaded
        try:
            rows.append(Gaia.launch_job_async(q).get_results().to_pandas())
            break
        except Exception as ex:
            print("retry", attempt, str(ex)[:80], flush=True)
            time.sleep(30 * (attempt + 1))
    else:
        raise SystemExit("Gaia archive unavailable")
v = pd.concat(rows) if rows else pd.DataFrame(columns=["source_id", "best_class_name", "best_class_score"])
v.to_csv(T / "flagged_gaia_vari.csv", index=False)
print(len(f), "flagged;", len(v), "with a Gaia DR3 classification"); print(v.best_class_name.value_counts().to_string())
