"""Reviewer check 1: data assembly. Independent re-parse of the raw files (does not import code/series.py).
Writes review/reviewer_checks/out_series.json and prints a summary."""
import csv
import datetime as dt
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
RAW = RUN / "data" / "raw"
OUT = Path(__file__).resolve().parent / "out_series.json"
NZ = ZoneInfo("Pacific/Auckland")
out = {}

s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)

# ---------- 1. generation: independent parse of two years, unit and fuel codes, duplicates ----------
def parse_date(x):
    x = x.strip()
    if "/" in x:
        d, m, y = x.split("/")
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return x[:10]

fuel_by_unit_year = defaultdict(Counter)
dup_rows = Counter()
annual = {}
tp_count_by_date = {}
for y in (2017, 2024):
    agg = defaultdict(float)
    for mth in range(1, 13):
        f = RAW / "generation" / f"{y}{mth:02d}.csv"
        with open(f, newline="") as fh:
            r = csv.reader(fh)
            hdr = next(r)
            hl = [h.lower() for h in hdr]
            ig, ifu, idt = hl.index("gen_code"), hl.index("fuel_code"), hl.index("trading_date")
            tpcols = [(i, int(h[2:])) for i, h in enumerate(hdr) if re.fullmatch(r"TP\d+", h)]
            seen = Counter()
            for row in r:
                d = parse_date(row[idt]); u = row[ig]; fu = row[ifu]
                fuel_by_unit_year[u][(y, fu)] += 1
                seen[(u, d)] += 1
                n = 0
                for i, tp in tpcols:
                    v = row[i].strip() if i < len(row) else ""
                    if v != "":
                        agg[(fu.lower(), tp <= 48)] += float(v) / 1000.0
                        n += 1
                tp_count_by_date.setdefault(d, Counter())[n] += 1
            for k, c in seen.items():
                if c > 1:
                    dup_rows[(y, k[0])] += 1
    annual[y] = {f"{fu}{'' if ok else '_TP49_50'}": round(v / 1000, 1) for (fu, ok), v in agg.items()}  # GWh
out["annual_raw_GWh"] = annual
ser = {y: (s[s.year == y][["hydro", "wind", "geo", "solar", "coal", "gas", "diesel", "wood", "D"]].sum() / 1000).round(1).to_dict() for y in (2017, 2024)}
out["annual_series_GWh"] = ser
# units with more than one row per trading date (same Gen_Code, different POC?) in the two years
out["units_with_multiple_rows_per_date"] = {f"{y}:{u}": c for (y, u), c in dup_rows.items()}
# fuel code by thermal unit and year (all years), to check the Huntly coding and any code changes
th_units = {}
for f in sorted(glob.glob(str(RAW / "generation" / "*.csv"))):
    d = pd.read_csv(f, usecols=lambda c: c.lower() in ("gen_code", "fuel_code", "tech_code"))
    d.columns = [c.lower() for c in d.columns]
    y = Path(f).stem[:4]
    for (u, fu, te), n in d.groupby(["gen_code", "fuel_code", "tech_code"]).size().items():
        if fu.lower() in ("coal", "gas", "diesel", "wood") or "huntly" in u.lower():
            th_units.setdefault(u, {}).setdefault(y, set()).add(f"{fu}/{te}")
out["thermal_unit_fuel_codes_by_year"] = {u: {y: sorted(v) for y, v in sorted(yy.items())} for u, yy in th_units.items()}
# number of populated TPs on DST dates
dst_dates = ["2017-04-02", "2017-09-24", "2024-04-07", "2024-09-29", "2024-07-01"]
out["populated_TPs_on_sample_dates"] = {d: dict(tp_count_by_date.get(d, {})) for d in dst_dates}
out["half_hours_per_date_in_series"] = s.groupby("date").size().value_counts().to_dict()

# ---------- 2. UTC mapping on DST days: TP k on date d should be local midnight + (k-1)*30 min, and hh should follow local clock ----------
def check_day(d):
    g = s[s.date == d]
    loc = g.ts.dt.tz_convert(NZ)
    return dict(n=len(g), first_utc=str(g.ts.iloc[0]), first_local=str(loc.iloc[0]), last_local=str(loc.iloc[-1]),
                hh_seq=g.hh.tolist()[:10] + ["..."] + g.hh.tolist()[-4:], consecutive_30min=bool((g.ts.diff().dropna() == pd.Timedelta("30min")).all()))
out["dst_days"] = {d: check_day(d) for d in ["2024-04-07", "2024-09-29"]}

# ---------- 3. Tiwai and HVDC signs ----------
def long_tp(f):
    d = pd.read_csv(f); d.columns = [c.lower() for c in d.columns]
    d["trading_date"] = d.trading_date.astype(str).map(parse_date)
    tps = [c for c in d.columns if re.fullmatch(r"tp\d+", c)]
    m = d.melt(id_vars=["poc", "flow_direction", "trading_date"], value_vars=tps, var_name="tp", value_name="kwh").dropna(subset=["kwh"])
    m["tp"] = m.tp.str[2:].astype(int)
    return m
hv = pd.concat([long_tp(f) for f in sorted(glob.glob(str(RAW / "hvdc" / "*.csv")))])
piv = hv.pivot_table(index=["trading_date", "tp"], columns=["poc", "flow_direction"], values="kwh", aggfunc="sum").fillna(0)
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
# BEN X (leaving grid at Benmore = northward) should match HAY I (arriving at Haywards) less losses; BEN I should match HAY X
out["hvdc_direction_consistency"] = dict(
    corr_BENX_HAYI=float(piv.BEN2201_X.corr(piv.HAY2201_I)), ratio_HAYI_over_BENX=float(piv.HAY2201_I.sum() / piv.BEN2201_X.sum()),
    corr_BENI_HAYX=float(piv.BEN2201_I.corr(piv.HAY2201_X)), ratio_BENI_over_HAYX=float(piv.BEN2201_I.sum() / piv.HAY2201_X.sum()),
    share_periods_both_directions_nonzero=float(((piv.BEN2201_X > 0) & (piv.BEN2201_I > 0)).mean()),
    mean_MW_north_series=float(s.hvdc_north.mean() * 2), share_north_positive=float((s.hvdc_north > 0).mean()))
tw = pd.concat([long_tp(f) for f in sorted(glob.glob(str(RAW / "tiwai" / "*.csv")))])
out["tiwai"] = dict(flow_directions=tw.flow_direction.value_counts().to_dict(), mean_MW=float(tw.kwh.mean() / 500), n_dates=int(tw.trading_date.nunique()),
                    nat_dates=int(pd.to_datetime(tw.trading_date, errors="coerce").isna().sum()), series_mean_MW=float(s.tiwai.mean() * 2))

# ---------- 4. storage: specific energy, per-lake maxima vs capacity, previous-day alignment, gap filling ----------
capf = glob.glob(str(RAW / "hmd" / "1_InfrastructureAndHydroConstraintAttributes" / "DerivedSeriesForStorageCapacityAndSpecificEnergy" / "20241231_*.csv"))[0]
cap = pd.read_csv(capf)
cap["se"] = cap.ActiveStorageCapacityScheme_GigaWattHours / cap.ActiveStorageCapacityScheme_MillionCubicMeters
se_hist = {}
for site, g in cap.groupby("SiteCode"):
    g = g.sort_values("Date")
    vals = g.dropna(subset=["se"])
    se_hist[site] = dict(distinct_se=sorted(set(vals.se.round(5))), last_nonnull_date=str(vals.Date.iloc[-1]) if len(vals) else None,
                         last_date=str(g.Date.iloc[-1]), n_null=int(g.se.isna().sum()),
                         se_2015_2024=sorted(set(vals[(vals.Date >= "2015-01-01") & (vals.Date <= "2024-12-31")].se.round(5))),
                         cap_gwh_last=float(vals.ActiveStorageCapacityScheme_GigaWattHours.iloc[-1]) if len(vals) else None)
out["specific_energy_by_site"] = se_hist
se_used = {k: v["distinct_se"][-1] for k, v in se_hist.items()}   # what groupby.last() picks (last non-null)
lakes = {}
for f in glob.glob(str(RAW / "hmd" / "3_StorageAndSpill_20241231" / "3_1_Storage" / "*_Storage_*.csv")):
    site = Path(f).name.split("_")[1]
    d = pd.read_csv(f)
    d["date"] = pd.to_datetime(d.iloc[:, 0]).dt.date
    d = d[(d.date >= dt.date(2014, 12, 1)) & (d.date <= dt.date(2024, 12, 31))]
    col3 = d.columns[3]
    mm3 = d.iloc[:, 3]
    gwh = mm3 * se_used[site]
    dates = pd.Series(sorted(set(d.date)))
    gaps = (pd.to_datetime(dates).diff().dt.days.dropna() - 1)
    lakes[site] = dict(column_used=col3, n_days=int(len(d)), missing_days=int(gaps.sum()), max_gap=int(gaps.max()) if len(gaps) else 0,
                       max_gwh=float(gwh.max()), cap_gwh=se_hist[site]["cap_gwh_last"], max_over_cap=float(gwh.max() / se_hist[site]["cap_gwh_last"]),
                       min_gwh=float(gwh.min()), n_dup_dates=int(d.date.duplicated().sum()))
out["storage_by_lake"] = lakes
# previous-day alignment: storage on local date d in the series should equal the sum of lake storage on d-1
st = []
for f in glob.glob(str(RAW / "hmd" / "3_StorageAndSpill_20241231" / "3_1_Storage" / "*_Storage_*.csv")):
    site = Path(f).name.split("_")[1]
    d = pd.read_csv(f, usecols=[0, 3]); d.columns = ["date", "mm3"]; d["date"] = pd.to_datetime(d.date).dt.date
    st.append(d.groupby("date").mm3.last().rename(site) * se_used[site])
nat = pd.concat(st, axis=1).sort_index()
nat_sum = nat.sum(axis=1, min_count=nat.shape[1])
chk = s.groupby("date").storage.first()
test_dates = ["2019-07-15", "2024-07-01", "2021-08-10"]
out["storage_alignment"] = {d: dict(series=float(chk[d]), raw_sum_prev_day=float(nat_sum.get(dt.date.fromisoformat(d) - dt.timedelta(1), np.nan)),
                                     raw_sum_same_day=float(nat_sum.get(dt.date.fromisoformat(d), np.nan))) for d in test_dates}
out["storage_series_range_GWh"] = dict(min=float(s.storage.min()), max=float(s.storage.max()), mean=float(s.storage.mean()),
                                       sum_cap_gwh=float(sum(v["cap_gwh_last"] for v in se_hist.values() if v["cap_gwh_last"])))
# how many national days needed interpolation (any lake missing)
out["storage_days_with_missing_lake_2015_2024"] = int(nat.loc[dt.date(2014, 12, 31):dt.date(2024, 12, 31)].isna().any(axis=1).sum())

# ---------- 5. inflow: hand conversion for one lake-day ----------
f = glob.glob(str(RAW / "hmd" / "2_Flows_20241231" / "NI_TPO_Natural_LakeTaupo_Inflow*.csv"))[0]
d = pd.read_csv(f); d["date"] = pd.to_datetime(d.iloc[:, 0]).dt.date
row = d[d.date == dt.date(2024, 1, 1)]
q = float(row.iloc[0, 2])
out["inflow_hand_check_taupo_2024_01_01"] = dict(q_m3s=q, gwh_day=q * 86400 / 1e6 * se_used["TPO"], se_TPO=se_used["TPO"],
                                                  n_rows_that_date=int(len(row)))
# which inflow files are used and whether any is an Outflow series
out["inflow_files"] = {k: Path(glob.glob(str(RAW / "hmd" / "2_Flows_20241231" / f"{v}*.csv"))[0]).name for k, v in
                       {"TPO": "NI_TPO_Natural_LakeTaupo_Inflow", "WKA": "NI_WKA_Natural_LakeWaikaremoana_Inflow", "TKA": "SI_TEK_Natural_LakeTekapo_Inflow",
                        "PKI": "SI_PKI_Natural_LakePukaki_Inflow", "OHA": "SI_OHU_Natural_LakeOhau_Inflow", "HWE": "SI_HWE_Natural_LakeHawea_Inflow",
                        "WAN": "SI_WAN_Natural_LakeWanaka_Outflow", "MAN": "SI_MAN_Natural_LakeManapouri(NoMararoaSpill)_Inflow", "TAU": "SI_TAU_Natural_LakeTeAnau_Inflow"}.items()}
# inflow "same day": the series' inflow on date d equals that day's natural inflow (not lagged) - the regression lags it by construction
infl_series = s.groupby("date").inflow.first()
out["inflow_series_GWh_day"] = dict(mean=float(infl_series.mean()), min=float(infl_series.min()), max=float(infl_series.max()))

# ---------- 6. temperature: half-hour interpolation and alignment ----------
j = json.load(open(RAW / "temperature" / "auckland.json"))
t = pd.Series(j["hourly"]["temperature_2m"], index=pd.to_datetime(j["hourly"]["time"], utc=True))
# the series' temp at an hourly UTC timestamp should be the population-weighted mean of the five cities' values at that hour
W = {"auckland": 1.70, "hamilton": 0.18, "wellington": 0.42, "christchurch": 0.39, "dunedin": 0.13}
ts0 = pd.Timestamp("2019-07-15 06:00", tz="UTC")
wsum_ = 0.0
for c, w in W.items():
    jj = json.load(open(RAW / "temperature" / f"{c}.json"))
    tt = pd.Series(jj["hourly"]["temperature_2m"], index=pd.to_datetime(jj["hourly"]["time"], utc=True))
    wsum_ += w * tt[ts0]
out["temp_hand_check"] = dict(ts=str(ts0), hand=wsum_ / sum(W.values()), series=float(s.set_index("ts").temp[ts0]))

json.dump(out, open(OUT, "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
