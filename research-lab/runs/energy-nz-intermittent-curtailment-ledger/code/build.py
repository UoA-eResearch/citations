"""Build the plant-period panel of plan section 1 from the fetched offers, metered output and prices.

The unit of analysis is a point of connection (POC) carrying wind or solar: offers and metered output are both
summed over the units or generators at that POC, which avoids matching offer unit codes to generator names.

For each POC, date and trading period:
  P        potential: per offer unit, the potential on the latest submission (highest SubmissionOrder among the
           IsLatestYesNo = Y rows; older tranches keep stale potentials), summed over units at the POC
  offered  sum of offered MW over the latest rows
  maxprice highest price at which any MW was offered
  G        metered output, MW (Generation_MD kWh per half-hour x 2 / 1000), wind and solar generators at the POC
  price    final energy price at the POC

Writes data/panel.parquet and results/tables/build_log.json (matching, coverage, output totals by month).
"""
import glob
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
TAB = RUN / "results" / "tables"
FUELS = {"Wind", "Solar"}


def generation():
    rows = []
    for f in sorted(glob.glob(str(DATA / "gen" / "*_Generation_MD.csv"))):
        x = pd.read_csv(f, dtype={"POC_Code": str, "Gen_Code": str})
        x = x[x.Fuel_Code.isin(FUELS)]
        tps = [c for c in x.columns if c.startswith("TP")]
        m = x.melt(id_vars=["POC_Code", "Gen_Code", "Fuel_Code", "Trading_Date"], value_vars=tps,
                   var_name="tp", value_name="kwh").dropna(subset=["kwh"])
        m["tp"] = m.tp.str[2:].astype(int)
        rows.append(m)
    g = pd.concat(rows, ignore_index=True)
    g["date"] = pd.to_datetime(g.Trading_Date, format="mixed").dt.date
    return g


def offers():
    out = []
    for f in sorted(glob.glob(str(DATA / "offers" / "*.csv.gz"))):
        x = pd.read_csv(f, dtype={"PointOfConnection": str, "Unit": str})
        if x.empty:
            continue
        x["pot"] = pd.to_numeric(x.ForecastOfGenerationPotentialMegawatts, errors="coerce")
        latest = x.loc[x.groupby(["PointOfConnection", "Unit", "TradingPeriod"]).SubmissionOrder.idxmax()]
        p = latest.groupby(["PointOfConnection", "Unit", "TradingPeriod"]).pot.first()
        off = x.groupby(["PointOfConnection", "Unit", "TradingPeriod"]).Megawatts.sum()
        mp = x[x.Megawatts > 0].groupby(["PointOfConnection", "Unit", "TradingPeriod"]).DollarsPerMegawattHour.max()
        u = pd.concat([p.rename("P"), off.rename("offered"), mp.rename("maxprice")], axis=1).reset_index()
        d = u.groupby(["PointOfConnection", "TradingPeriod"]).agg(P=("P", "sum"), offered=("offered", "sum"),
                                                                  maxprice=("maxprice", "max"),
                                                                  units=("Unit", "nunique")).reset_index()
        d["date"] = pd.to_datetime(x.TradingDate.iloc[0], format="mixed").date()
        out.append(d)
    o = pd.concat(out, ignore_index=True).rename(columns={"PointOfConnection": "poc", "TradingPeriod": "tp"})
    return o


def prices(pocs):
    rows = []
    for f in sorted(glob.glob(str(DATA / "prices" / "*_FinalEnergyPrices.csv"))):
        x = pd.read_csv(f, dtype={"PointOfConnection": str})
        x = x[x.PointOfConnection.isin(pocs)]
        rows.append(x)
    p = pd.concat(rows, ignore_index=True)
    p["date"] = pd.to_datetime(p.TradingDate, format="mixed").dt.date
    return p.rename(columns={"PointOfConnection": "poc", "TradingPeriod": "tp", "DollarsPerMegawattHour": "price"})[
        ["poc", "date", "tp", "price"]]


def main():
    log = {}
    o = offers()
    pocs = sorted(o.poc.unique())
    log["offer_pocs"] = pocs
    g = generation()
    gp = g.groupby(["POC_Code", "date", "tp"]).agg(kwh=("kwh", "sum"), fuel=("Fuel_Code", "first")).reset_index()
    gp = gp.rename(columns={"POC_Code": "poc"})
    gp["G"] = gp.kwh * 2 / 1000
    gen_pocs = sorted(gp.poc.unique())
    log["generation_pocs_wind_solar"] = gen_pocs
    log["offer_pocs_without_generation"] = sorted(set(pocs) - set(gen_pocs))
    log["generation_pocs_without_offers"] = sorted(set(gen_pocs) - set(pocs))
    # monthly validation: matched output against all wind and solar output in Generation_MD
    g["month"] = pd.to_datetime(g.date).dt.to_period("M").astype(str)
    tot = g.groupby(["month", "Fuel_Code"]).kwh.sum() / 1e6
    mat = g[g.POC_Code.isin(pocs)].groupby(["month", "Fuel_Code"]).kwh.sum() / 1e6
    v = pd.concat([tot.rename("all_gwh"), mat.rename("matched_gwh")], axis=1).fillna(0).reset_index()
    v.to_csv(TAB / "output_validation_monthly.csv", index=False)
    pr = prices(pocs)
    panel = o.merge(gp[["poc", "date", "tp", "G", "fuel"]], on=["poc", "date", "tp"], how="left") \
             .merge(pr, on=["poc", "date", "tp"], how="left")
    log["panel_rows"] = len(panel)
    log["rows_missing_output"] = int(panel.G.isna().sum())
    log["rows_missing_price"] = int(panel.price.isna().sum())
    log["first_date_with_potential"] = str(min(o.date))
    log["pocs_by_fuel"] = panel.dropna(subset=["fuel"]).groupby("fuel").poc.unique().apply(sorted).to_dict()
    # per-POC check that potential and metered output describe the same plant: a generator at the POC that does not
    # offer (or an offer unit with no metering) shows up as a mean output/potential ratio far from about 0.9-1.0
    chk = panel.dropna(subset=["G"]).groupby("poc").agg(mean_P=("P", "mean"), mean_G=("G", "mean"),
                                                        rows=("P", "size"), units=("units", "max"))
    chk["G_over_P"] = chk.mean_G / chk.mean_P
    log["poc_check"] = chk.round(3).reset_index().to_dict(orient="records")
    panel["date"] = pd.to_datetime(panel.date)
    panel.to_parquet(DATA / "panel.parquet", index=False)
    json.dump(log, open(TAB / "build_log.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in log.items()}, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
