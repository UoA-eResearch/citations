"""Confirmation pass: run the revised score_forecast.py unchanged on the sealed 2019-20 vintage with SEASON set to
1 Nov 2019 - 30 Apr 2020, writing its outputs to review/reviewer_checks/dryrun_tab/ (not results/tables/)."""
import sys, time
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RUN / "code"))
import score_forecast as S
S.TAB = Path(__file__).parent / "dryrun_tab"
S.SEASON = (pd.Timestamp("2019-11-01"), pd.Timestamp("2020-04-30 23:59"))
t = time.time()
S.main(str(RUN / "data/raw"), str(RUN / "data/processed"))
print(f"elapsed {time.time()-t:.0f}s")
print(pd.read_csv(S.TAB / "forecast_scored.csv").round(3).to_string(index=False))
