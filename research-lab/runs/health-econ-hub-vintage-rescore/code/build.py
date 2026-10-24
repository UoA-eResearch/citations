"""Truth vintages and quantile forecasts (plan section 1).

  build.py vintages   git history of each hub's truth file -> data/interim/truth.parquet
                      (location, target_end_date, first_value, first_commit, final_value, n_versions)
  build.py forecasts  quantile forecasts -> data/interim/forecasts.parquet
                      (season, model, ref_date, location, horizon, target_end_date, q, value)
"""
import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, INT = RUN / "data" / "raw", RUN / "data" / "interim"
INT.mkdir(parents=True, exist_ok=True)
HUBS = {"old": (RAW / "flusight-old", "data-truth/truth-Incident Hospitalizations.csv"),
        "new": (RAW / "flusight", "target-data/target-hospital-admissions.csv")}
QS = [0.01, 0.025] + [round(0.05 * k, 3) for k in range(1, 20)] + [0.975, 0.99]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def season_of(d):
    d = pd.Timestamp(d)
    y = d.year if d.month >= 8 else d.year - 1
    return f"{y}-{str(y + 1)[2:]}"


def vintages():
    rows = []
    for hub, (repo, path) in HUBS.items():
        log = git(repo, "log", "--format=%H %cI", "--", path).decode().split("\n")
        commits = [l.split() for l in log if l.strip()][::-1]          # oldest first
        for k, (sha, when) in enumerate(commits):
            try:
                raw = git(repo, "show", f"{sha}:{path}")
            except subprocess.CalledProcessError:
                continue
            d = pd.read_csv(io.BytesIO(raw), dtype={"location": str})
            d = d.rename(columns={"date": "target_end_date"})
            if "value" not in d or "target_end_date" not in d:
                continue
            d = d[["location", "target_end_date", "value"]].dropna()
            d["commit_time"] = pd.Timestamp(when)
            d["hub"] = hub
            d["k"] = k
            rows.append(d)
        print(hub, len(commits), "commits", flush=True)
    V = pd.concat(rows, ignore_index=True)
    V["target_end_date"] = pd.to_datetime(V.target_end_date)
    V["location"] = V.location.str.zfill(2).replace({"0S": "US"}).where(V.location != "US", "US")
    out = []
    for hub, g in V.groupby("hub"):
        g = g.sort_values(["commit_time", "k"])
        first = g.groupby(["location", "target_end_date"]).first()
        last_k = g.k.max()
        final = g[g.k == last_k].set_index(["location", "target_end_date"]).value
        nv = g.groupby(["location", "target_end_date"]).value.nunique()
        t = pd.DataFrame({"first_value": first.value, "first_commit": first.commit_time, "final_value": final, "n_distinct": nv})
        t["hub"] = hub
        out.append(t.reset_index())
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(INT / "truth.parquet", index=False)
    print(T.groupby("hub").agg(rows=("location", "size"), revised=("n_distinct", lambda s: (s > 1).mean())).to_string())


def _read(path):
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, dtype={"location": str, "output_type_id": str})


def forecasts():
    rows = []
    # 2022-23: old repo, data-forecasts/<model>/<date>-<model>.csv
    for f in sorted((RAW / "flusight-old" / "data-forecasts").glob("*/*.csv")):
        model = f.parent.name
        try:
            d = pd.read_csv(f, dtype={"location": str})
        except Exception:
            continue
        if "type" not in d or "quantile" not in d:
            continue
        d = d[(d.type == "quantile") & d.target.astype(str).str.contains("inc flu hosp")]
        if d.empty:
            continue
        d["horizon"] = d.target.str.extract(r"(\d+) wk ahead").astype(float)
        rows.append(pd.DataFrame({"model": model, "ref_date": pd.to_datetime(d.forecast_date), "location": d.location,
                                  "horizon": d.horizon, "target_end_date": pd.to_datetime(d.target_end_date),
                                  "q": d["quantile"].astype(float).round(3), "value": d.value.astype(float), "hub": "old"}))
    # 2023-24 onward: hubverse model-output/<model>/<date>-<model>.(csv|parquet)
    for f in sorted((RAW / "flusight" / "model-output").glob("*/*")):
        if f.suffix not in (".csv", ".parquet"):
            continue
        model = f.parent.name
        try:
            d = _read(f)
        except Exception:
            continue
        if "output_type" not in d:
            continue
        d = d[(d.output_type == "quantile") & (d.target.astype(str) == "wk inc flu hosp")]
        if d.empty:
            continue
        rows.append(pd.DataFrame({"model": model, "ref_date": pd.to_datetime(d.reference_date), "location": d.location.astype(str),
                                  "horizon": d.horizon.astype(float), "target_end_date": pd.to_datetime(d.target_end_date),
                                  "q": d.output_type_id.astype(float).round(3), "value": d.value.astype(float), "hub": "new"}))
    F = pd.concat(rows, ignore_index=True)
    F["location"] = F.location.str.zfill(2).where(F.location != "US", "US")
    F["season"] = F.ref_date.map(season_of)
    F = F[F.q.isin(QS)]
    F = F[F.season.isin(["2022-23", "2023-24", "2024-25"])]
    F = F[((F.hub == "old") & F.horizon.between(1, 4)) | ((F.hub == "new") & F.horizon.between(0, 3))]
    F.to_parquet(INT / "forecasts.parquet", index=False)
    print(F.groupby("season").agg(models=("model", "nunique"), refs=("ref_date", "nunique"), rows=("q", "size")).to_string())


if __name__ == "__main__":
    {"vintages": vintages, "forecasts": forecasts}[sys.argv[1]]()
