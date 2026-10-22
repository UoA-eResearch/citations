"""D3 secondary: H1 and H2 models on the slip-sized exposure (exposure_slips.csv). Writes results/tables/slips.json."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402


def main():
    d = A.load()
    sl = pd.read_csv(A.T / "exposure_slips.csv")
    d = d.merge(sl, on="site_id")
    W = A.weights(d.estuary.nunique())
    r1 = A.h1(d, W, tcol="tercile_slip")
    r2 = A.h2(d, W, ecol="E_slip_route_5")
    iqr = float(sl.E_slip_route_5.quantile(0.75) - sl.E_slip_route_5.quantile(0.25))
    out = {"H1_model": r1, "H1_rule_reading": A.verdict_h1(r1), "H2_model": r2, "E_slip_iqr": round(iqr, 6),
           "delta_per_iqr": round(r2["E_2023"]["estimate"] * iqr, 3),
           "delta_per_iqr_wild_ci": [round(v * iqr, 3) for v in r2["E_2023"]["wild_ci"]],
           "H2_rule_reading": A.verdict_h2(r2, iqr)}
    json.dump(out, open(A.T / "slips.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
