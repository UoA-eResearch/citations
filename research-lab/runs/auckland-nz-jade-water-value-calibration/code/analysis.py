"""Calibration of the published JADE weekly runs against realised prices (plan sections 2 and 4).

For every weekly run: build the 91-member simulated distribution of the weekly average price at HAY, time-weighted
over demand blocks by that run's own hours_per_block; compare it with the realised time-weighted average at
HAY2201 over the same seven days; and record where in its own distribution the realised price fell.

H1 is the stage-2 exceedance rate of the simulated 90th percentile. H2 splits that rate by whether national
storage at the run start was below its historical 20th percentile for that week of the year. Intervals come from a
moving-block bootstrap over runs in calendar order.

Writes results/tables/{primary.json,runs.csv,by_stage.csv}.
"""
import bisect
import csv
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
DATA, T = RUN / "data", RUN / "results" / "tables"
BLOCKS = ("PEAK", "SHOULDER", "OFFPEAK")
STAGES = (1, 2, 3, 4)
PRIMARY_STAGE = 2
NODE_SIM, NODE_REAL = "HAY", "HAY2201"
OTHER_NODES = ("BEN2201", "OTA2201")
SEED, B, BLOCK = 20261020, 2000, 4
MIN_SIMS = 50      # the published runs carry 80-91 inflow sequences, not a fixed 91 (deviations D1)
MIN_PERIODS = 330  # a full settled week is 336 half-hours, 334 or 338 when the clocks change
LOW_STORAGE_Q = 0.20


def jade_week_start(year, week):
    """JADE week w of year Y begins on 1 January + 7(w-1) days (plan section 1)."""
    return date(year, 1, 1) + timedelta(days=7 * (week - 1))


def load_hours(tag):
    """hours_per_block.csv -> {(year, week): {block: hours}}"""
    out = {}
    path = DATA / "runs" / f"{tag}_hours.csv"
    if not path.exists():
        return out
    for r in csv.DictReader(open(path)):
        out[(int(r["YEAR"]), int(r["WEEK"]))] = {b: float(r[b]) for b in BLOCKS}
    return out


def load_run(tag):
    """Filtered tidy_results -> simulated weekly prices by stage, and the run-start reservoir sum."""
    hours = load_hours(tag)
    # price[(stage, sim)][block] = value ; and the (year, week) each stage refers to
    px, stage_week, res0 = {}, {}, {}
    with open(DATA / "runs" / f"{tag}.csv") as fh:
        for r in csv.DictReader(fh):
            stage = int(r["stage"])
            if r["type"] == "prices" and r["node"] == NODE_SIM and stage in STAGES:
                px.setdefault((stage, int(r["simulation"])), {})[r["demand"]] = float(r["value"])
                stage_week[stage] = (int(r["year"]), int(r["week"]))
            elif r["type"] == "reslevel" and stage == 0:
                res0[r["name"]] = float(r["value"])
    sims = {}
    for stage in STAGES:
        yw = stage_week.get(stage)
        h = hours.get(yw) if yw else None
        if h is None:
            continue
        tot = sum(h[b] for b in BLOCKS)
        vals = []
        for (st, sim), blocks in sorted(px.items()):
            if st != stage or set(blocks) != set(BLOCKS):
                continue
            vals.append(sum(blocks[b] * h[b] for b in BLOCKS) / tot)
        sims[stage] = (yw, np.array(vals), tot)
    return sims, sum(res0.values()), res0


def load_realised():
    """EMI final energy prices -> {node: {date: [prices by trading period]}}"""
    out = {}
    for path in sorted((DATA / "prices").glob("*.csv")):
        for r in csv.DictReader(open(path)):
            node = r.get("PointOfConnection") or r.get("PointofConnection") or r.get("Node")
            raw = r.get("TradingDate") or r.get("Trading_date") or r.get("TRADING_DATE")
            val = r.get("DollarsPerMegawattHour") or r.get("Price") or r.get("PRICE")
            if not (node and raw and val):
                continue
            try:
                d = datetime.strptime(raw.split("T")[0].strip(), "%Y-%m-%d").date()
            except ValueError:
                try:
                    d = datetime.strptime(raw.strip(), "%d/%m/%Y").date()
                except ValueError:
                    continue
            try:
                out.setdefault(node, {}).setdefault(d, []).append(float(val))
            except ValueError:
                continue
    return out


def weekly_realised(real, node, start):
    """Time-weighted average over the seven days from `start`: every trading period is half an hour, so the mean
    over all periods in the week is the time-weighted average. Returns (mean, n_periods, n_days)."""
    vals, days = [], 0
    for k in range(7):
        got = real.get(node, {}).get(start + timedelta(days=k))
        if got:
            vals += got; days += 1
    if not vals:
        return None, 0, 0
    return float(np.mean(vals)), len(vals), days


def pit(sim, actual):
    """Where the realised price fell in its own simulated distribution, with a mid-rank tie correction."""
    below = float(np.sum(sim < actual))
    equal = float(np.sum(sim == actual))
    return (below + 0.5 * equal) / len(sim)


def block_boot(stat, n, rng):
    """Moving-block bootstrap index draws over runs in calendar order."""
    nb = math.ceil(n / BLOCK)
    out = []
    for _ in range(B):
        starts = rng.integers(0, max(1, n - BLOCK + 1), size=nb)
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        idx = idx[idx < n]
        out.append(stat(idx))
    return np.array([v for v in out if v is not None and np.isfinite(v)])


def ci(draws, lo=2.5, hi=97.5):
    return [float(np.percentile(draws, lo)), float(np.percentile(draws, hi))] if len(draws) else [None, None]


def specific_energy():
    """GWh per million cubic metres for each lake, from the HMD's derived capacity series."""
    out = {}
    for path in sorted((DATA / "hmd").glob("*EnergyStorageCapacity*.csv")):
        for r in csv.DictReader(open(path)):
            site = r.get("SiteCode")
            mm, gwh = r.get("ActiveStorageCapacityScheme_MillionCubicMeters"), \
                r.get("ActiveStorageCapacityScheme_GigaWattHours")
            if not (site and mm and gwh):
                continue
            try:
                mm, gwh = float(mm), float(gwh)
            except ValueError:
                continue
            if mm > 0:
                out[site] = gwh / mm          # a scheme constant; the last valid row wins
    return out


def national_storage():
    """{date: national active energy storage, GWh}: the HMD lakes summed on a forward-filled daily grid.

    Volumes cannot be added across lakes, so each lake's active storage is converted to energy with its own
    GWh-per-Mm3 ratio from the derived capacity series before summing."""
    se = specific_energy()
    per, skipped = {}, []
    for path in sorted((DATA / "hmd").glob("*_Storage_*.csv")):
        site = path.name.split("_")[1]
        if site not in se:
            skipped.append(site); continue
        d = {}
        for r in csv.DictReader(open(path)):
            key = next((k for k in r if k and k.startswith("Active storage")), None)
            raw, val = r.get("Date"), (r.get(key) if key else None)
            if not (raw and val):
                continue
            try:
                d[datetime.strptime(raw.split("T")[0].strip(), "%Y-%m-%d").date()] = float(val)
            except ValueError:
                continue
        if d:
            per[site] = d
    if not per:
        return {}, {"sites": [], "skipped": skipped, "note": "no lake storage files found"}
    grids = {s: (sorted(v), [v[k] for k in sorted(v)]) for s, v in per.items()}
    lo = max(g[0][0] for g in grids.values())
    hi = min(g[0][-1] for g in grids.values())
    out, day = {}, lo
    while day <= hi:
        tot, ok = 0.0, True
        for s, (ds, vs) in grids.items():
            i = bisect.bisect_right(ds, day) - 1
            if i < 0 or (day - ds[i]).days > 31:
                ok = False; break
            tot += vs[i] * se[s]
        if ok:
            out[day] = tot
        day += timedelta(days=1)
    meta = {"sites": sorted(per), "skipped": skipped, "from": lo.isoformat(), "to": hi.isoformat(),
            "n_days": len(out)}
    return out, meta


def deseasonalised_low(rows):
    """A storage indicator covering every run: JADE's own stage-0 reservoir sum, with two seasonal harmonics
    removed, flagged low in the bottom 20% of residuals. Used where the hydrological dataset does not reach."""
    if len(rows) < 20:
        return {}
    w = np.array([r["week"] for r in rows], float)
    y = np.array([r["res_start"] for r in rows], float)
    X = np.column_stack([np.ones_like(w)] + [f(2 * np.pi * k * w / 52.0) for k in (1, 2) for f in (np.sin, np.cos)])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    cut = np.percentile(resid, 100 * LOW_STORAGE_Q)
    return {r["tag"]: bool(resid[i] <= cut) for i, r in enumerate(rows)}


def main():
    T.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    index = sorted(csv.DictReader(open(DATA / "run_index.csv")), key=lambda r: (int(r["year"]), int(r["week"])))
    real = load_realised()
    storage, storage_meta = national_storage()

    rows, excluded = [], []
    for r in index:
        tag, year, week, stamp = r["tag"], int(r["year"]), int(r["week"]), r["input_stamp"]
        if not (DATA / "runs" / f"{tag}.csv").exists():
            excluded.append((tag, "no output file")); continue
        sims, res_sum, _ = load_run(tag)
        if PRIMARY_STAGE not in sims:
            excluded.append((tag, "no stage-2 prices")); continue
        # preregistered check: the input freeze must sit inside the stage-1 week
        s1 = jade_week_start(year, week)
        ok_stamp = None
        if len(stamp) >= 8:
            try:
                st = datetime.strptime(stamp[:8], "%Y%m%d").date()
                ok_stamp = s1 <= st < s1 + timedelta(days=7)
            except ValueError:
                ok_stamp = None
        if ok_stamp is not True:
            excluded.append((tag, f"input stamp {stamp} outside stage-1 week starting {s1}")); continue

        row = dict(tag=tag, year=year, week=week, input_stamp=stamp, res_start=res_sum)
        for stage in STAGES:
            if stage not in sims:
                continue
            (sy, sw), sim, tot_h = sims[stage]
            start = jade_week_start(sy, sw)
            actual, nper, ndays = weekly_realised(real, NODE_REAL, start)
            row[f"s{stage}_week"] = f"{sy}-{sw:02d}"
            row[f"s{stage}_start"] = start.isoformat()
            row[f"s{stage}_nsim"] = len(sim)
            row[f"s{stage}_hours"] = tot_h
            row[f"s{stage}_periods"] = nper
            row[f"s{stage}_days"] = ndays
            row[f"s{stage}_p10"] = float(np.percentile(sim, 10)) if len(sim) else None
            row[f"s{stage}_p50"] = float(np.percentile(sim, 50)) if len(sim) else None
            row[f"s{stage}_p90"] = float(np.percentile(sim, 90)) if len(sim) else None
            row[f"s{stage}_actual"] = actual
            if actual is not None and len(sim):
                row[f"s{stage}_pit"] = pit(sim, actual)
                row[f"s{stage}_exceed"] = int(actual > row[f"s{stage}_p90"])
                row[f"s{stage}_below"] = int(actual < row[f"s{stage}_p10"])
        for node in OTHER_NODES:
            (sy, sw), sim, _ = sims[PRIMARY_STAGE]
            a, _, _ = weekly_realised(real, node, jade_week_start(sy, sw))
            row[f"{node}_actual"] = a
        # storage state at the run start, as a percentile of that week-of-year's history in other years
        if storage:
            wk_start = jade_week_start(year, week)
            cur = [v for d, v in storage.items() if wk_start <= d < wk_start + timedelta(days=7)]
            woy = (wk_start - date(wk_start.year, 1, 1)).days // 7
            hist = [v for d, v in storage.items()
                    if d.year != year and abs((d - date(d.year, 1, 1)).days // 7 - woy) <= 1]
            if cur and len(hist) >= 100:
                row["storage_gwh"] = float(np.mean(cur))
                row["storage_pctile"] = float(np.mean(np.array(hist) < np.mean(cur)))
                row["storage_hist_n"] = len(hist)
        rows.append(row)

    def is_usable(r):
        return (r.get(f"s{PRIMARY_STAGE}_exceed") is not None
                and r.get(f"s{PRIMARY_STAGE}_days") == 7
                and (r.get(f"s{PRIMARY_STAGE}_periods") or 0) >= MIN_PERIODS
                and (r.get(f"s{PRIMARY_STAGE}_nsim") or 0) >= MIN_SIMS)

    for r in rows:
        if r.get(f"s{PRIMARY_STAGE}_exceed") is not None and not is_usable(r):
            excluded.append((r["tag"], f"incomplete week or too few sequences: days={r.get(f's{PRIMARY_STAGE}_days')} "
                                       f"periods={r.get(f's{PRIMARY_STAGE}_periods')} "
                                       f"nsim={r.get(f's{PRIMARY_STAGE}_nsim')}"))
    usable = [r for r in rows if is_usable(r)]
    n = len(usable)
    exc = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in usable], float)
    pits = np.array([r[f"s{PRIMARY_STAGE}_pit"] for r in usable], float)

    rate = float(exc.mean()) if n else None
    draws = block_boot(lambda idx: exc[idx].mean(), n, rng)
    out = {
        "n_runs_indexed": len(index), "n_runs_usable": n, "excluded": excluded[:40],
        "n_excluded": len(excluded), "seed": SEED, "bootstrap": B, "block": BLOCK,
        "H1": {"exceedance_rate": rate, "ci": ci(draws), "threshold": 0.20, "nominal": 0.10,
               "se": float(draws.std()) if len(draws) else None,
               "mde": float(2.8 * draws.std()) if len(draws) else None},
        "pit": {"mean": float(pits.mean()) if n else None,
                "hist": np.histogram(pits, bins=10, range=(0, 1))[0].tolist() if n else []},
        "coverage": {}, "by_stage": {}, "by_year": {}, "lower_tail": {}, "storage_meta": storage_meta,
    }
    for lvl in (0.50, 0.80, 0.90):
        lo, hi = (1 - lvl) / 2, 1 - (1 - lvl) / 2
        cov = float(np.mean((pits > lo) & (pits < hi))) if n else None
        out["coverage"][f"{int(lvl * 100)}%"] = cov
    out["lower_tail"]["rate"] = float(np.mean([r[f"s{PRIMARY_STAGE}_below"] for r in usable])) if n else None

    for stage in STAGES:
        sub = [r for r in rows if r.get(f"s{stage}_exceed") is not None
               and r.get(f"s{stage}_days") == 7 and (r.get(f"s{stage}_periods") or 0) >= MIN_PERIODS
               and (r.get(f"s{stage}_nsim") or 0) >= MIN_SIMS]
        if not sub:
            continue
        e = np.array([r[f"s{stage}_exceed"] for r in sub], float)
        p = np.array([r[f"s{stage}_pit"] for r in sub], float)
        d = block_boot(lambda idx: e[idx].mean(), len(sub), rng)
        out["by_stage"][str(stage)] = {"n": len(sub), "rate": float(e.mean()), "ci": ci(d),
                                      "pit_mean": float(p.mean())}
    for y in sorted({r["year"] for r in usable}):
        sub = [r for r in usable if r["year"] == y]
        e = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in sub], float)
        out["by_year"][str(y)] = {"n": len(sub), "rate": float(e.mean())}

    # H2: low-storage split
    have = [r for r in usable if r.get("storage_pctile") is not None]
    low = [r for r in have if r["storage_pctile"] < LOW_STORAGE_Q]
    high = [r for r in have if r["storage_pctile"] >= LOW_STORAGE_Q]
    h2 = {"n_with_storage": len(have), "n_low": len(low), "n_high": len(high), "threshold": LOW_STORAGE_Q,
          "scored": len(low) >= 10 and len(high) >= 10}
    if h2["scored"]:
        el = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in low], float)
        eh = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in high], float)
        h2["rate_low"], h2["rate_high"] = float(el.mean()), float(eh.mean())
        idx_all = np.arange(len(have))
        is_low = np.array([r["storage_pctile"] < LOW_STORAGE_Q for r in have])
        ea = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in have], float)

        def ratio(idx):
            a, b = ea[idx][is_low[idx]], ea[idx][~is_low[idx]]
            if len(a) < 3 or len(b) < 3 or b.mean() == 0:
                return None
            return a.mean() / b.mean()

        d = block_boot(ratio, len(have), rng)
        h2["ratio"] = (h2["rate_low"] / h2["rate_high"]) if h2["rate_high"] else None
        h2["ci"] = ci(d)
        h2["n_bootstrap_valid"] = int(len(d))
        _ = idx_all
    low_flag = deseasonalised_low([r for r in usable if r.get("res_start")])
    if low_flag:
        sub = [r for r in usable if r["tag"] in low_flag]
        ea = np.array([r[f"s{PRIMARY_STAGE}_exceed"] for r in sub], float)
        is_low = np.array([low_flag[r["tag"]] for r in sub])

        def ratio2(idx):
            a, b = ea[idx][is_low[idx]], ea[idx][~is_low[idx]]
            if len(a) < 3 or len(b) < 3 or b.mean() == 0:
                return None
            return a.mean() / b.mean()

        d2 = block_boot(ratio2, len(sub), rng)
        h2["sensitivity_deseasonalised"] = {
            "n": len(sub), "n_low": int(is_low.sum()),
            "rate_low": float(ea[is_low].mean()) if is_low.any() else None,
            "rate_high": float(ea[~is_low].mean()) if (~is_low).any() else None,
            "ratio": (float(ea[is_low].mean() / ea[~is_low].mean())
                      if (~is_low).any() and ea[~is_low].mean() else None),
            "ci": ci(d2)}
    out["H2"] = h2

    # validation
    nsims = [r.get(f"s{PRIMARY_STAGE}_nsim") for r in rows if r.get(f"s{PRIMARY_STAGE}_nsim")]
    out["validation"] = {
        "n_sequences": {"min": min(nsims) if nsims else None, "median": float(np.median(nsims)) if nsims else None,
                        "max": max(nsims) if nsims else None,
                        "distribution": {str(k): nsims.count(k) for k in sorted(set(nsims))}},
        "runs_with_168_hours": sum(1 for r in rows if r.get(f"s{PRIMARY_STAGE}_hours") == 168),
        "runs_with_7_price_days": sum(1 for r in usable if r.get(f"s{PRIMARY_STAGE}_days") == 7),
        "period_counts": sorted({r.get(f"s{PRIMARY_STAGE}_periods") for r in usable}),
        "median_actual": float(np.median([r[f"s{PRIMARY_STAGE}_actual"] for r in usable])) if n else None,
        "median_sim_p50": float(np.median([r[f"s{PRIMARY_STAGE}_p50"] for r in usable])) if n else None,
    }

    json.dump(out, open(T / "primary.json", "w"), indent=1)
    if rows:
        keys = sorted({k for r in rows for k in r})
        with open(T / "runs.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    with open(T / "by_stage.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["stage", "n", "rate", "lo", "hi", "pit_mean"])
        for s, v in out["by_stage"].items():
            w.writerow([s, v["n"], f"{v['rate']:.4f}", f"{v['ci'][0]:.4f}", f"{v['ci'][1]:.4f}",
                        f"{v['pit_mean']:.4f}"])
    print(json.dumps({k: out[k] for k in ("n_runs_indexed", "n_runs_usable", "n_excluded", "H1", "H2",
                                          "coverage", "validation")}, indent=1)[:2600])


if __name__ == "__main__":
    main()
