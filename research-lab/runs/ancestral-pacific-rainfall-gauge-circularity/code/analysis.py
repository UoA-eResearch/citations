"""Primary analysis (plan sections 1, 3, 4) for the CHIRP/CHIRPS pair, and the secondary PERSIANN/PERSIANN-CDR pair.
Reads data/gauge_daily.csv.gz, data/labels.csv, data/extract/chirp*.csv and chirps*.csv (worker part files, D1), and for
the secondary pair data/extract/persiann_daily.csv and data/labels_gpcc.csv. Writes results/tables/primary.json,
results/tables/station_skill.csv, results/tables/station_skill_secondary.csv and results/tables/benchmark_stations.csv."""
import glob
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
B = 2000
MIN_PENTADS, MIN_STRATUM = 100, 30


def pentad_id(dates):
    k = np.minimum((dates.dt.day - 1) // 5 + 1, 6)
    return dates.dt.strftime("%Y.%m.") + k.astype(str)


def gauge_pentads(daily, shift):
    """Pentad totals with the gauge series shifted by `shift` days (value reported on t+shift assigned to t); only
    complete pentads (every day valid)."""
    s = daily.set_index("date").prcp_mm.asfreq("D")
    s = s.shift(-shift)
    df = s.to_frame("p").reset_index()
    df["pentad"] = pentad_id(df.date)
    g = df.groupby("pentad").agg(p=("p", "sum"), valid=("p", lambda x: x.notna().sum()), days=("p", "size"))
    return g[g.valid == g.days].p


def kge(sim, obs):
    r = np.corrcoef(sim, obs)[0, 1]
    b = sim.mean() / obs.mean() if obs.mean() > 0 else np.nan
    g = (sim.std() / sim.mean()) / (obs.std() / obs.mean()) if sim.mean() > 0 and obs.mean() > 0 else np.nan
    return 1 - np.sqrt((r - 1) ** 2 + (b - 1) ** 2 + (g - 1) ** 2), r, b, g


def metrics(df):
    rm_a = np.sqrt(((df.chirp - df.obs) ** 2).mean()); rm_b = np.sqrt(((df.chirps - df.obs) ** 2).mean())
    ka = kge(df.chirp.values, df.obs.values); kb = kge(df.chirps.values, df.obs.values)
    return dict(n=len(df), rmse_chirp=rm_a, rmse_chirps=rm_b, gain=1 - rm_b / rm_a if rm_a > 0 else np.nan,
                kge_chirp=ka[0], kge_chirps=kb[0], dkge=kb[0] - ka[0], r_chirp=ka[1], r_chirps=kb[1],
                beta_chirp=ka[2], beta_chirps=kb[2], gamma_chirp=ka[3], gamma_chirps=kb[3])


def stratum(km, lo, hi):
    return np.where(km <= lo, "supported", np.where(km > hi, "independent", "intermediate"))


def summarise(sk, rng):
    """H1 ratio and H2 mean dKGE with a station-block bootstrap."""
    sup = sk[sk.stratum == "supported"].set_index("station"); ind = sk[sk.stratum == "independent"].set_index("station")
    stations = sorted(set(sup.index) | set(ind.index))
    def stat(sel):
        s = sup.reindex([x for x in sel if x in sup.index]); i = ind.reindex([x for x in sel if x in ind.index])
        gs, gi = s.gain.mean(), i.gain.mean()
        return gs, gi, (gi / gs if gs and np.isfinite(gs) else np.nan), i.dkge.mean()
    gs, gi, R, dk = stat(stations)
    bs = [stat(list(rng.choice(stations, len(stations)))) for _ in range(B)]
    q = lambda k: [float(np.nanpercentile([b[k] for b in bs], 2.5)), float(np.nanpercentile([b[k] for b in bs], 97.5))]
    return dict(n_stations_supported=int(len(sup)), n_stations_independent=int(len(ind)), gain_supported=float(gs), gain_supported_ci=q(0),
                gain_independent=float(gi), gain_independent_ci=q(1), ratio=float(R), ratio_ci=q(2), dkge_independent=float(dk), dkge_independent_ci=q(3))


def verdicts(p):
    lo, hi = p["ratio_ci"]
    if p["gain_supported_ci"][0] <= 0:
        p["H1_verdict"] = "Inconclusive (no gain to shrink)"
    else:
        p["H1_verdict"] = "Supported" if hi < 0.5 else "Refuted" if lo >= 0.5 else "Inconclusive"
    l2, u2 = p["dkge_independent_ci"]
    p["H2_verdict"] = "Supported" if u2 < 0 else "Refuted" if l2 > 0 else "Inconclusive"
    return p


def secondary(st, daily, rng):
    """PERSIANN (satellite-only) against PERSIANN-CDR, 2001-2020; label from the GPCC gauge count of the 2.5 deg cell
    (supported >= 1, independent 0). Same QC, timing (shift chosen against PERSIANN), inclusion and statistics."""
    f = RUN / "data" / "extract" / "persiann_daily.csv"
    if not f.exists():
        return dict(status="not done: inputs not retrieved (plan section 2 feasibility rule)")
    pd_ = pd.read_csv(f, parse_dates=["date"])
    lab = pd.read_csv(RUN / "data" / "labels_gpcc.csv")
    rows = []
    for s in st.itertuples():
        x = pd_[pd_.station == s.id].set_index("date")[["persiann", "cdr"]].asfreq("D")
        if x.empty:
            continue
        x["pentad"] = pentad_id(x.index.to_series())
        g = x.groupby("pentad").agg(persiann=("persiann", "sum"), cdr=("cdr", "sum"), np_=("persiann", "count"), nc=("cdr", "count"),
                                    days=("persiann", "size"))
        g = g[(g.np_ == g.days) & (g.nc == g.days)]
        d = daily[(daily.station == s.id) & (daily.date >= "2000-12-30") & (daily.date <= "2021-01-02")]
        if d.empty:
            continue
        best = None
        for sh in (-1, 0, 1):
            gp = gauge_pentads(d, sh)
            j = pd.concat([gp.rename("obs"), g.persiann], axis=1).dropna()
            if len(j) >= MIN_PENTADS:
                rho = spearmanr(j.obs, j.persiann).statistic
                if best is None or rho > best[1]:
                    best = (sh, rho, gp)
        if best is None:
            continue
        j = pd.concat([best[2].rename("obs"), g.persiann.rename("chirp"), g.cdr.rename("chirps")], axis=1).dropna()
        j["ym"] = j.index.str[:4] + "-" + j.index.str[5:7]
        j = j.merge(lab[lab.station == s.id][["ym", "numgauge"]], on="ym", how="left").set_index(j.index).dropna(subset=["numgauge"])
        j["stratum"] = np.where(j.numgauge >= 1, "supported", "independent")
        for sv, gg in j.groupby("stratum"):
            if len(gg) >= MIN_STRATUM:
                rows.append(dict(variant="secondary", station=s.id, cc=s.cc, stratum=sv, shift=best[0], **metrics(gg)))
    sk = pd.DataFrame(rows)
    ren = {c: c.replace("chirps", "cdr").replace("chirp", "persiann") for c in sk.columns}
    sk.rename(columns=ren).to_csv(T / "station_skill_secondary.csv", index=False)
    if sk.empty or not (sk.stratum == "supported").any() or not (sk.stratum == "independent").any():
        return dict(status="done", note="a stratum has no qualifying station", n_station_strata=int(len(sk)))
    r = verdicts(summarise(sk, rng))
    r["status"] = "done"; r["pair"] = "gain = 1 - RMSE(PERSIANN-CDR)/RMSE(PERSIANN); dKGE = KGE(CDR) - KGE(PERSIANN)"
    return r


def read_parts(prod):
    fs = [f for f in glob.glob(str(RUN / "data" / "extract" / f"{prod}*.csv")) if re.fullmatch(prod + r"(_[a-z0-9]+)?\.csv", Path(f).name)]
    e = pd.concat([pd.read_csv(f, dtype={"pentad": str, "station": str}) for f in fs])
    e = e[e.status == "ok"].drop_duplicates(["pentad", "station"]).copy()
    e["value"] = pd.to_numeric(e.value)   # error rows carry their message in this column, so it reads as text
    return e


def main():
    rng = np.random.default_rng(20261018)
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    daily = pd.read_csv(RUN / "data" / "gauge_daily.csv.gz", parse_dates=["date"])
    lab = pd.read_csv(RUN / "data" / "labels.csv")
    ex = {}
    for prod in ("chirp", "chirps"):
        e = read_parts(prod)
        ex[prod] = e.pivot_table(index="pentad", columns="station", values="value", aggfunc="first")
    out = dict(extract_pentads={p: int(len(v)) for p, v in ex.items()})
    masked = [s for s in st.id if s in ex["chirps"].columns and ex["chirps"][s].isna().all()]
    rows, shifts, per_country = [], {}, []
    for s in st.itertuples():
        d = daily[daily.station == s.id]
        if s.id not in ex["chirp"].columns or d.empty:
            continue
        # timing: the shift maximising Spearman correlation with CHIRP (the satellite-only twin), then applied to both
        best = None
        for sh in (-1, 0, 1):
            gp = gauge_pentads(d, sh)
            j = pd.concat([gp.rename("obs"), ex["chirp"][s.id].rename("chirp")], axis=1).dropna()
            if len(j) >= MIN_PENTADS:
                rho = spearmanr(j.obs, j.chirp).statistic
                if best is None or rho > best[1]:
                    best = (sh, rho, gp)
        if best is None:
            continue
        shifts[s.id] = best[0]
        j = pd.concat([best[2].rename("obs"), ex["chirp"][s.id].rename("chirp"), ex["chirps"].get(s.id, pd.Series(dtype=float)).rename("chirps")], axis=1)
        j = j.dropna(subset=["obs", "chirp"])
        j["ym"] = j.index.str[:4] + "-" + j.index.str[5:7]
        j = j.merge(lab[lab.station == s.id][["ym", "nearest_km"]], on="ym", how="left").set_index(j.index)
        per_country.append(dict(station=s.id, cc=s.cc, pentads=len(j), chirps_masked=s.id in masked,
                                independent=int((j.nearest_km > 100).sum()), supported=int((j.nearest_km <= 25).sum())))
        if s.id in masked or j.chirps.isna().all():
            continue
        jj = j.dropna(subset=["chirps", "nearest_km"])
        for name, lo, hi, tf in [("primary", 25, 100, None), ("t10_50", 10, 50, None), ("t50_150", 50, 150, None), ("log", 25, 100, np.log1p)]:
            x = jj.copy()
            if tf is not None:
                x[["obs", "chirp", "chirps"]] = tf(x[["obs", "chirp", "chirps"]])
            x["stratum"] = stratum(x.nearest_km.values, lo, hi)
            for sv, g in x.groupby("stratum"):
                if len(g) >= MIN_STRATUM:
                    rows.append(dict(variant=name, station=s.id, cc=s.cc, stratum=sv, shift=best[0], **metrics(g)))
            co = x[x.nearest_km <= 5]
            if name == "primary" and len(co) >= MIN_STRATUM:
                rows.append(dict(variant="colocated_5km", station=s.id, cc=s.cc, stratum="supported", shift=best[0], **metrics(co)))
    sk = pd.DataFrame(rows)
    sk.to_csv(T / "station_skill.csv", index=False)
    pc = pd.DataFrame(per_country)
    pc.to_csv(T / "benchmark_stations.csv", index=False)
    out["stations_with_pentads"] = int(len(pc)); out["chirps_masked_stations"] = len(masked)
    out["shift_counts"] = pd.Series(shifts).value_counts().to_dict()
    res = {v: summarise(sk[sk.variant == v], rng) for v in ("primary", "t10_50", "t50_150", "log")}
    verdicts(res["primary"])
    out["results"] = res
    out["secondary"] = secondary(st, daily, np.random.default_rng(20261018))
    out["by_country"] = pc.groupby("cc").agg(stations=("station", "size"), pentads=("pentads", "sum"), independent=("independent", "sum"),
                                             supported=("supported", "sum"), masked=("chirps_masked", "sum")).reset_index().to_dict("records")
    lab["decade"] = lab.ym.str[:3] + "0s"
    out["ingested_share_by_decade"] = lab.assign(co=lab.nearest_km <= 5).groupby("decade").co.mean().round(3).to_dict()
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("stations_with_pentads", "chirps_masked_stations", "shift_counts")}, default=float))
    print(json.dumps(res["primary"], indent=1, default=float))


if __name__ == "__main__":
    main()
