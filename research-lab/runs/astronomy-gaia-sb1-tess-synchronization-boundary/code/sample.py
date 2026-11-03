"""Main-sequence SB1 sample (plan section 0).

parallax_over_error > 10; dereddened M_G within -1.0 to +0.75 mag of the Pecaut & Mamajek dwarf sequence at the
dereddened BP-RP; Teff from the dereddened colour through the same table. Dereddening uses GSP-Phot's E(BP-RP)
and A_G where present, otherwise none (flagged).

  sample.py -> data/sample.parquet, results/tables/coverage.json (section "orbits")
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402


def mamajek():
    rows, cols = [], None
    for line in (D / "ref" / "EEM_dwarf_UBVIJHK_colors_Teff.txt").read_text().splitlines():
        if line.startswith("#SpT"):
            if cols is not None:
                break                                          # the first table ends where the second header starts
            cols = line[1:].split(); continue
        if cols and line.strip() and not line.startswith("#"):
            rows.append(line.split()[:len(cols)])
    t = pd.DataFrame(rows, columns=cols[:len(rows[0])])
    t = t[["Teff", "Bp-Rp", "M_G"]].replace("...", np.nan).apply(pd.to_numeric, errors="coerce").dropna()
    return t.sort_values("Bp-Rp").drop_duplicates("Bp-Rp")


def main():
    g = pd.read_parquet(D / "gaia_sb1.parquet").drop_duplicates("source_id")
    m = mamajek()
    c = Coverage("orbits", T / "coverage.json")
    n0 = len(g)
    g = g[g.parallax_over_error > 10]
    n1 = len(g)
    has = g.ebpminrp_gspphot.notna() & g.ag_gspphot.notna()
    g = g.assign(dereddened=has, bp_rp0=g.bp_rp - g.ebpminrp_gspphot.fillna(0),
                 mg0=g.phot_g_mean_mag + 5 * np.log10(g.parallax / 100) - g.ag_gspphot.fillna(0))
    g = g[g.bp_rp0.between(m["Bp-Rp"].min(), m["Bp-Rp"].max())]
    n2 = len(g)
    g["ms_offset"] = g.mg0 - np.interp(g.bp_rp0, m["Bp-Rp"], m["M_G"])
    g = g[g.ms_offset.between(-1.0, 0.75)]
    g["teff"] = np.interp(g.bp_rp0, m["Bp-Rp"], m["Teff"])
    g["dist_pc"] = 1000 / g.parallax
    c.add_counts(ok=len(g), drops={"parallax_over_error <= 10": n0 - n1,
                                   "dereddened colour outside the dwarf table": n1 - n2,
                                   "outside the main-sequence band": n2 - len(g)})
    c.save()
    g.to_parquet(D / "sample.parquet")
    print(len(g), "main-sequence SB1 |", int((g.period < 12).sum()), "with P < 12 d |", int((g.period < 10).sum()), "with P < 10 d")


if __name__ == "__main__":
    main()
