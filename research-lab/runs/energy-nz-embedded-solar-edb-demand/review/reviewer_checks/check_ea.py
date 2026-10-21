"""Reviewer check: EA installed-DG CSVs - segment sums, uptake precision, excluded participants, farms."""
import io, pandas as pd
from pathlib import Path
RAW = Path("/mnt/data/edb-solar/raw/ea")
def ea(name):
    lines = (RAW/name).read_text().splitlines()
    i = next(k for k,l in enumerate(lines) if l.startswith("Month end,"))
    x = pd.read_csv(io.StringIO("\n".join(lines[i:])))
    x["month"] = pd.to_datetime(x["Month end"], dayfirst=True)
    return x.rename(columns={"Region ID":"pid","Total capacity installed (MW)":"mw","ICP count":"icp","ICP uptake rate (%)":"up"})
seg = {s: ea(f"solar_{s}_All_Total.csv") for s in ("All","Res","Com","Ind","SME")}
a = seg["All"][["pid","month","mw","icp","up"]]
for s in ("Res","Com","Ind","SME"):
    a = a.merge(seg[s][["pid","month","mw"]].rename(columns={"mw":s}), on=["pid","month"], how="left")
a = a.fillna(0)
a["rci"] = a.Res + a.Com + a.Ind
print("uptake % sample values:", a.up.dropna().astype(str).head(8).tolist())
print("decimals in uptake:", a.up.dropna().astype(str).str.split(".").str[-1].str.len().value_counts().to_dict())
print("Res+Com+Ind vs All (ratio) quantiles:", (a.rci/a.mw.replace(0,float('nan'))).describe().round(3).to_dict())
last = a[a.month==a.month.max()]
print("latest month:", a.month.max().date(), "national All MW:", round(last.mw.sum(),1), "Res/Com/Ind/SME:", [round(last[s].sum(),1) for s in ("Res","Com","Ind","SME")])
PART = {"ALPE","DUNE","BUEL","CHBP","COUP","EASH","ELEC","ELIN","EAST","HEDL","MPOW","MARL","NELS","TASM","WATA","NPOW","ORON","OTPO","POCO","SCAN","LINE","TPCO","TOPE","HAWK","VECT","WAIK","WAIP","CKHK","WPOW"}
ex = last[~last.pid.isin(PART)][["pid","mw","icp"]].sort_values("mw", ascending=False)
print("excluded participants latest MW:", ex.round(2).values.tolist(), "total", round(ex.mw.sum(),1))
print("Ind MW latest, top:", last.sort_values("Ind", ascending=False)[["pid","Ind","Com","Res","mw","icp","up"]].head(8).round(2).values.tolist())
for p in ("EASH","TOPE","HEDL","MARL","NPOW"):
    s = a[(a.pid==p)].set_index("month").Ind.diff().abs().sort_values(ascending=False).head(3)
    print(p, "largest Ind monthly steps:", [(d.strftime("%Y-%m"), round(v,1)) for d,v in s.items()])
# derived ICPs: registry count = icp/up*100 ; rounding noise
a["icps_reg"] = a.icp/(a.up/100)
for p in ("VECT","EASH","TOPE","WPOW","OTPO"):
    s = a[a.pid==p].set_index("month").icps_reg
    print(p, "registry ICPs: ", {y: int(v) for y,v in s[s.index.month==3].items()})
