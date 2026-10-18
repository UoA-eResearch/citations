"""Checks and descriptives (plan section 6). Writes results/tables/checks.json.
1. Demand measure: total metered generation against 2024 grid export (correlation, ratio).
2. Ledger: quarterly ledger CO2 intensity against MfE quarterly grid factors (2023-2024; a check, not used to fit).
3. Composition (descriptive): the 2SLS response of coal and gas generation separately, at each horizon.
4. Tiwai demand-response episodes (descriptive only): daily Tiwai offtake at least 100 MW below its trailing 30-day
   median for at least 7 consecutive days; thermal generation and AEF in the episode against the 30 days before."""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mef  # noqa: E402
import series  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
    out = {}
    ge = pd.concat([series.long_tp(f, ["POC", "Trading_Date"]) for f in sorted(glob.glob(str(RUN / "data" / "raw" / "grid_export" / "*.csv")))])
    ge["ts"] = series.utc_index(ge.Trading_Date.values, ge.tp.values)
    g = ge.groupby("ts").kwh.sum() / 1000
    j = pd.concat([s.set_index("ts").D, g.rename("gx")], axis=1, join="inner")
    out["demand_vs_grid_export_2024"] = dict(n=int(len(j)), corr=float(j.D.corr(j.gx)), ratio_D_over_export=float(j.D.sum() / j.gx.sum()))
    ef = pd.read_csv(RUN / "data" / "raw" / "mfe" / "emission_factors_2026_v2_long.csv", encoding="utf-8-sig")
    q = ef[(ef.SubSection == "Quarterly Averages") & (ef.GHG == "GHG_CO2_KGCO2_e")]
    mon = {"Mar": 1, "Jun": 2, "Sep": 3, "Dec": 4}
    rows = []
    for lab, v in zip(q.EmissionsFactorLabel, q.EmissionFactor):
        k = lab.split(" - ")[1]; qq, yy = mon[k[:3]], int(k[-4:])
        if yy > 2024:
            continue
        sel = s[(s.year == yy) & (((s.month - 1) // 3 + 1) == qq)]
        rows.append(dict(quarter=f"{yy}Q{qq}", mfe=float(v), ledger=float(sel.E.sum() / sel.D.sum())))
    out["quarterly_check"] = rows
    # composition responses (descriptive, not preregistered)
    s["z"] = mef.instrument(s)
    s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
    for k in range(4):
        s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
    s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1)
    s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
    s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
    di = s.groupby("date").inflow.first()
    s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
    new = {}
    for h in mef.H:
        for v, src in (("D", "D"), ("W", "wind"), ("C", "coal"), ("GS", "gas")):
            new[f"{v}_{h}"] = mef.wsum(s[src].values, h)
    s = pd.concat([s, pd.DataFrame(new)], axis=1)
    idx = np.where(s[["zl4", "Dday", "inflow7", "hvdc_day", "storage", f"D_{max(mef.H)}"]].notna().all(axis=1))[0]
    r = mef.fit(s, idx, mef.H, ("C", "GS"))
    out["composition"] = [dict(label=mef.LAB[h], coal=r[h]["est"]["C"], gas=r[h]["est"]["GS"]) for h in mef.H]
    # Tiwai episodes
    d = s.groupby("date").agg(tiwai=("tiwai", "sum"), thermal=("thermal", "sum"), E=("E", "sum"), D=("D", "sum"))
    d["tw_mw"] = d.tiwai / 24
    base = d.tw_mw.shift(1).rolling(30).median()
    low = (d.tw_mw <= base - 100)
    grp = (low != low.shift()).cumsum()
    eps = []
    for _, gg in d[low].groupby(grp[low]):
        if len(gg) >= 7:
            start = gg.index[0]
            pre = d.loc[:start].iloc[-31:-1]
            eps.append(dict(start=start, end=gg.index[-1], days=len(gg), mw_cut=float(base.loc[start] - gg.tw_mw.mean()),
                            thermal_gwh_day_pre=float(pre.thermal.mean() / 1000), thermal_gwh_day_in=float(gg.thermal.mean() / 1000),
                            aef_pre=float(pre.E.sum() / pre.D.sum()), aef_in=float(gg.E.sum() / gg.D.sum())))
    out["tiwai_episodes"] = eps
    json.dump(out, open(T / "checks.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
