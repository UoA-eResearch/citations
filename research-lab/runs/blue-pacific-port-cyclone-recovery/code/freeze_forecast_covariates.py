"""Write the frozen per-port covariates behind forecast_table.csv, from the sealed 2026 vintage, so the 2027 scorer
uses exactly the covariates and port set the forecast was made with (review issue 10). Deterministic; its output
is identical whenever it is run on data/raw as sealed in VINTAGE.txt."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from events import PICT  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, TAB = RUN / "data" / "raw", RUN / "results" / "tables"

if __name__ == "__main__":
    ports = pd.read_csv(RAW / "portwatch" / "ports.csv")
    act = pd.read_csv(RAW / "portwatch" / "daily.csv", usecols=["portid", "portcalls"]).groupby("portid").portcalls.mean()
    ports["mean_calls"] = ports.portid.map(act)
    pac = ports[ports.ISO3.isin(PICT) & (ports.mean_calls >= 0.5)].copy()
    out = pd.DataFrame(dict(portid=pac.portid, portname=pac.portname, ISO3=pac.ISO3, lat=pac.lat, lon=pac.lon,
                            log_size=np.log(pac.vessel_count_total + 1), log_activity=np.log(pac.mean_calls),
                            share=pac.share_country_maritime_import / 100, sids=1.0))
    out.sort_values("portid").to_csv(TAB / "forecast_port_covariates.csv", index=False, float_format="%.12g")
    ft = pd.read_csv(TAB / "forecast_table.csv")
    assert set(ft.portid) == set(out.portid), "port set differs from the frozen forecast table"
    print(len(out), "ports written")
