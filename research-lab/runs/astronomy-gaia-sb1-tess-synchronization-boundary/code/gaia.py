"""Gaia DR3 SB1/SB1C orbits with photometry, astrophysics and DR2 neighbours (plan section 1).

The archive caps a job at 50,000 rows, so each query runs in K slices by MOD(source_id, K) and every slice must
return fewer than 50,000 rows. Slices use gaia_source.random_index: source_id exceeds double precision, so MOD on
it is unreliable server-side; random_index (0 to 1,811,709,770, uniform) is cut into K equal ranges.
Results are fetched as plain VOTable: the default compressed format returned 19,100 of 22,784 rows for the first
slice without error. Every slice's row count is checked against a COUNT(*) of the same filter.

  gaia.py -> data/gaia_sb1.parquet, data/gaia_dr2_neighbours.parquet
"""
from pathlib import Path

import time

import pandas as pd
from astroquery.gaia import Gaia

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
Gaia.ROW_LIMIT = -1

MAIN = """
SELECT n.source_id, n.nss_solution_type, n.period, n.period_error, n.eccentricity, n.eccentricity_error,
       n.semi_amplitude_primary, n.semi_amplitude_primary_error, n.t_periastron, n.arg_periastron,
       n.significance, n.goodness_of_fit,
       g.ra, g.dec, g.parallax, g.parallax_over_error, g.phot_g_mean_mag, g.bp_rp, g.ruwe, g.grvs_mag,
       g.vbroad, g.vbroad_error, g.vbroad_nb_transits,
       a.ag_gspphot, a.ebpminrp_gspphot, a.teff_gspphot, a.radius_gspphot, a.radius_flame
FROM gaiadr3.nss_two_body_orbit AS n
JOIN gaiadr3.gaia_source AS g ON g.source_id = n.source_id
LEFT JOIN gaiadr3.astrophysical_parameters AS a ON a.source_id = n.source_id
WHERE n.nss_solution_type IN ('SB1', 'SB1C') AND g.random_index >= {lo} AND g.random_index < {hi}
"""
NB = """
SELECT d.dr3_source_id, d.dr2_source_id, d.angular_distance, d.magnitude_difference
FROM gaiadr3.dr2_neighbourhood AS d
JOIN gaiadr3.nss_two_body_orbit AS n ON n.source_id = d.dr3_source_id
JOIN gaiadr3.gaia_source AS g ON g.source_id = n.source_id
WHERE n.nss_solution_type IN ('SB1', 'SB1C') AND g.random_index >= {lo} AND g.random_index < {hi}
"""
K, CAP = 8, 50000
STEP = 1_811_709_771 // K + 1

for q, out in ((MAIN, "gaia_sb1.parquet"), (NB, "gaia_dr2_neighbours.parquet")):
    parts = []
    for k in range(K):
        lo, hi = k * STEP, (k + 1) * STEP
        sq = q.format(lo=lo, hi=hi)
        for attempt in range(6):
            try:
                n = int(Gaia.launch_job_async("SELECT COUNT(*) AS c FROM (" + sq + ") AS s").get_results()["c"][0])
                x = Gaia.launch_job_async(sq, output_format="votable_plain").get_results().to_pandas()
                break
            except Exception as e:                       # the archive returns sporadic HTTP 500s
                print("retry", k, attempt, str(e)[:80], flush=True); time.sleep(60 * (attempt + 1))
        assert len(x) == n, f"slice {k}: {len(x)} rows, COUNT says {n}"
        assert len(x) < CAP, f"slice {k} hit the row cap"
        print(out, "slice", k, len(x), flush=True)
        parts.append(x)
    t = pd.concat(parts, ignore_index=True)
    t.columns = [c.lower() for c in t.columns]
    t.to_parquet(D / out)
    print(out, len(t), "rows")
