#!/usr/bin/env python
"""Load the NWSS influenza A sample data (data.cdc.gov ymmh-divb; State_Territory, CDC_Verily and WastewaterSCAN
sources), downloaded as 50,000-row pages, into data/processed/ww_samples.parquet with parsed dates."""
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC = RUN / "data" / "raw", RUN / "data" / "processed"


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    df = pd.concat([pd.read_csv(p, dtype=str) for p in sorted((RAW / "flua_pages").glob("p*.csv"))], ignore_index=True)
    assert df.record_id.is_unique, "duplicate records across pages"
    for c in ("population_served", "flow_rate", "lod_sewage", "pcr_target_avg_conc_lin", "pcr_target_flowpop_lin"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["collect"] = pd.to_datetime(df.sample_collect_date.str[:10], errors="coerce")
    df["updated"] = pd.to_datetime(df.date_updated.str[:10], errors="coerce")
    df.to_parquet(PROC / "ww_samples.parquet", index=False)
    print(len(df), "samples;", df.site.nunique(), "sites;", df.state_territory.nunique(), "jurisdictions;",
          df.collect.min().date(), "to", df.collect.max().date())


if __name__ == "__main__":
    sys.exit(main())
