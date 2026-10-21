"""Reviewer check: EMI grid flow files - directions, types, duplicates, zeros, coverage, HAM0331."""
import pandas as pd, sys
from pathlib import Path
RAW = Path("/mnt/data/edb-solar/raw/emi")
def load(kind, ym):
    x = pd.read_csv(RAW / kind / f"{ym}_{kind}.csv", dtype=str)
    x.columns = [c.upper() for c in x.columns]
    return x
for ym in ("201501", "202001", "202501", "202512"):
    for kind in ("Grid_export", "Grid_import"):
        x = load(kind, ym)
        tps = [f"TP{k}" for k in range(25, 31)]
        x["mid"] = x[tps].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        print(f"\n== {ym} {kind}: rows={len(x)} GENTYPE={x.GENERATION_TYPE.value_counts().to_dict()} UNIT={x.UNIT_MEASURE.value_counts().to_dict()} FLOW={x.FLOW_DIRECTION.value_counts().to_dict()} STATUS={x.STATUS.value_counts().to_dict()}")
        g = x[(x.UNIT_MEASURE.str.lower()=="kwh") & (x.GENERATION_TYPE=="GN")]
        dup = g.duplicated(["POC","NWK_CODE","TRADING_DATE"]).sum()
        print(f"   GN kWh rows={len(g)} dup(POC,NWK,date)={dup} POCs={g.POC.nunique()} ; zero-midday share={((g.mid==0).mean()):.3f}")
        if dup:
            d = g[g.duplicated(["POC","NWK_CODE","TRADING_DATE"], keep=False)]
            print("   dup sample:", d[["POC","NWK_CODE","TRADER","STATUS","TRADING_DATE","mid"]].head(6).to_dict("records"))
        h = g[g.POC=="HAM0331"]
        print(f"   HAM0331 GN kWh: n={len(h)} nwk={h.NWK_CODE.unique().tolist()} mean mid kWh/day={h.mid.mean():.0f}")
        if kind=="Grid_import":
            top = g.groupby(["POC","NWK_CODE"]).mid.sum().sort_values(ascending=False).head(8)
            print("   top import GN POCs (kWh midday, month):", {f"{a}/{b}": int(v) for (a,b),v in top.items()})
        # non-GN types present in export files
        if kind=="Grid_export":
            oth = x[x.GENERATION_TYPE!="GN"].groupby("GENERATION_TYPE").POC.nunique().to_dict()
            print("   non-GN POC counts:", oth, "; sample:", x[x.GENERATION_TYPE!="GN"][["POC","NWK_CODE","GENERATION_TYPE"]].drop_duplicates().head(5).values.tolist())
# zero-midday rows in detail for Grid_export 202512 by network
x = load("Grid_export", "202512"); tps=[f"TP{k}" for k in range(25,31)]
x["mid"] = x[tps].apply(pd.to_numeric, errors="coerce").sum(axis=1)
g = x[(x.UNIT_MEASURE.str.lower()=="kwh")&(x.GENERATION_TYPE=="GN")]
z = g.assign(z=g.mid==0).groupby("NWK_CODE").z.mean().sort_values(ascending=False)
print("\nshare of zero-midday POC-days by network, 202512:", z.round(3).to_dict())
# POC-days per network per file (coverage drift)
cov = {}
for ym in ("201412","201712","202012","202312","202512"):
    g = load("Grid_export", ym); g = g[(g.UNIT_MEASURE.str.lower()=="kwh")&(g.GENERATION_TYPE=="GN")]
    cov[ym] = g.groupby("NWK_CODE").POC.nunique()
print("\nGN POCs per network by Dec file:\n", pd.DataFrame(cov).fillna(0).astype(int).to_string())
