"""Segment x half-year crash panel for the difference-in-differences (plan.md section 4).

Analysis sample: treated and control segments in strata (rca | v0 | reduction half-year | class group) that contain
both, and with at least one crash of the outcome type in the estimation window (zero-only segments carry no
information in a Poisson model with segment fixed effects). Corridor (cluster) = rca + normalised OSM name, or the
OSM way id when the way has no name.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import snap as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PERIODS = [f"{y}H{h}" for y in range(2017, 2027) for h in (1, 2)][1:]  # 2017H2 .. 2026H2


def units():
    d = pd.read_parquet(RUN / "data" / "seg_class.parquet")
    d = d[d.klass.isin(["treated", "control"])].copy()
    both = d.groupby("stratum").klass.agg(lambda k: {"treated", "control"} <= set(k))
    d = d[d.stratum.map(both)].copy()
    nm = d.name.map(S.norm_name)
    d["corridor"] = np.where(nm != "", d.rca + "|" + nm, "way" + d.way.astype(str))
    d["treated"] = d.klass == "treated"
    return d


def panel(crashes, d, outcome="injury", periods=None):
    periods = periods or sorted(crashes.period.unique())
    c = crashes[(crashes.seg >= 0) & crashes.seg.isin(d.seg) & crashes.period.isin(periods)]
    if outcome != "all":
        c = c[c[outcome]]
    y = c.groupby(["seg", "period"]).size().rename("y")
    segs = y.index.get_level_values(0).unique()
    idx = pd.MultiIndex.from_product([segs, periods], names=["seg", "period"])
    p = y.reindex(idx, fill_value=0).reset_index()
    return p.merge(d[["seg", "stratum", "corridor", "treated", "cohort", "ttype", "rca", "v0", "v1", "clsg",
                      "red_half"]], on="seg")
