"""G2 stages after the TIC match: light curves per star (D1: TESS-SPOC only in the primary) and the classification.

  coverage_lc.py -> results/tables/coverage.json (stages "light_curves", "classification")
"""
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

st = pd.read_parquet(D / "stars.parquet"); m = st[st.tic.notna()]
sp = pd.read_parquet(D / "sector_periods.parquet")
spoc = set(sp[(sp["product"] == "tess-spoc") & (sp.n > 0)].tic); anylc = set(sp[sp.n > 0].tic)
c = Coverage("light_curves", T / "coverage.json")
c.add_counts(ok=int(m.tic.isin(spoc).sum()), drops={"QLP only (excluded from the primary, D1)": int((m.tic.isin(anylc) & ~m.tic.isin(spoc)).sum()),
                                                    "no FFI light curve": int((~m.tic.isin(anylc)).sum())})
c.save()
w = st[st.cls.isin(["detected", "inconsistent", "pulsator", "ellipsoidal_or_double_spot", "possible_beaming", "no_detection"])]
c = Coverage("classification", T / "coverage.json")
c.add_counts(ok=int((w.cls == "detected").sum()), drops={k: int(v) for k, v in w[w.cls != "detected"].cls.value_counts().items()})
c.save()
print("ok")
