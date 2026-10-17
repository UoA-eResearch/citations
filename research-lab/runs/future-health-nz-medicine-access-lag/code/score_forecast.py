"""Score the frozen forecast (H4) after the 12-month horizon: re-run fetch_xml.py and pharmac.py to extend the
listing archive, then this script. Funded = the substance appears (link.has rule) in a community Schedule or HML
edition dated after the forecast origin and on or before origin + 12 months. Brier skill against the frozen base
rate, with a substance bootstrap. Checks the forecast file's sha256 first."""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import norm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    f = RUN / "results" / "forecast_2026.csv"
    want = (RUN / "results" / "forecast_2026.sha256").read_text().split()[0]
    assert hashlib.sha256(f.read_bytes()).hexdigest() == want, "forecast file changed since it was frozen"
    fc = pd.read_csv(f)
    # D8: score with the match names in force when the forecast was frozen (aliases and the first-word rule),
    # from a companion file frozen before any later Schedule was read
    mf = RUN / "results" / "forecast_2026_match_names.csv"
    want_m = (RUN / "results" / "forecast_2026_match_names.sha256").read_text().split()[0]
    assert hashlib.sha256(mf.read_bytes()).hexdigest() == want_m, "match-names file changed since it was frozen"
    mn = pd.read_csv(mf).set_index("substance").match_names.to_dict()
    L = pd.read_csv(RUN / "data" / "pharmac_listings.csv", dtype=str)
    L["ed"] = pd.to_datetime(L.edition); L["text"] = (L.chemical.fillna("") + " " + L.formulations.fillna("")).map(norm)
    o, end = pd.Timestamp(fc.forecast_origin[0]), pd.Timestamp(fc.score_after[0])
    assert L.ed.max() >= end, f"archive ends {L.ed.max().date()}, before the horizon {end.date()}"
    W = L[(L.ed > o) & (L.ed <= end) & ((L.source == "HML") | (L.section == "B"))]
    pat = lambda s: "|".join(r"(?<![a-z0-9])" + re.escape(x) + r"(?![a-z0-9])" for x in str(mn.get(s, s)).split("|"))
    fc["funded"] = [int(W.text.str.contains(pat(s)).any()) for s in fc.substance]
    bs = lambda x: float(np.mean((x.p_funded_12m - x.funded) ** 2))
    bb = lambda x: float(np.mean((x.base_rate - x.funded) ** 2))
    skill = lambda x: 1 - bs(x) / bb(x) if bb(x) > 0 else None
    rng = np.random.default_rng(20271101)
    v = [skill(fc.iloc[rng.integers(0, len(fc), len(fc))]) for _ in range(2000)]
    v = [x for x in v if x is not None]
    lo, hi = np.percentile(v, [2.5, 97.5])
    s = skill(fc)
    res = dict(n=len(fc), funded=int(fc.funded.sum()), brier=bs(fc), brier_base=bb(fc), skill=s, ci=[float(lo), float(hi)],
               verdict="Supported" if lo > 0 else "Refuted" if hi < 0 else "Inconclusive")
    json.dump(res, open(RUN / "results" / "tables" / "forecast_score.json", "w"), indent=1)
    print(res)


if __name__ == "__main__":
    sys.exit(main())
