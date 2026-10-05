"""Measure F (audit_plan.md): scout estimates vs outcomes. est_wall_time (parsed to a [lo, hi] range in days) vs actual
elapsed time from the first commit touching the run directory to the last commit touching its report.md; verdicts by
scout value/cost/feasibility. Writes paper/audit/F_calibration.csv."""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
LAB = REPO / "research-lab"
OUT = LAB / "paper" / "audit"


def parse_days(s):
    s = str(s).lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(day|week|hour)", s) or re.search(r"(\d+(?:\.\d+)?)()\s*(day|week|hour)", s)
    if not m:
        return (np.nan, np.nan)
    lo = float(m.group(1)); hi = float(m.group(2) or m.group(1))
    f = {"day": 1, "week": 7, "hour": 1 / 24}[m.group(3)]
    return lo * f, hi * f


def git_times(path):
    out = subprocess.check_output(["git", "log", "--format=%ct", "--", path], cwd=REPO, text=True).split()
    return [int(x) for x in out]


def main():
    leads = {l["id"]: l for l in json.load(open(LAB / "leads.json"))["leads"]}
    rows = []
    for run in sorted(p for p in (LAB / "runs").iterdir() if (p / "report.md").exists()):
        l = leads.get(run.name, {})
        lo, hi = parse_days(l.get("est_wall_time"))
        t_run = git_times(run.relative_to(REPO).as_posix())
        t_rep = git_times((run / "report.md").relative_to(REPO).as_posix())
        actual = (max(t_rep) - min(t_run)) / 86400 if t_run and t_rep else np.nan
        rows.append(dict(run=run.name, verdict=l.get("verdict_tag"), value=l.get("value_score"), cost=l.get("cost_score"), feasibility=l.get("feasibility"),
                         est_wall_time=l.get("est_wall_time"), est_lo_days=lo, est_hi_days=hi, actual_days=actual,
                         ratio_to_midpoint=actual / ((lo + hi) / 2) if lo == lo else np.nan))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "F_calibration.csv", index=False)
    print(d[["run", "verdict", "value", "cost", "est_wall_time", "actual_days", "ratio_to_midpoint"]].round(2).to_string(index=False))
    print(f"\nmedian ratio actual/estimated midpoint {d.ratio_to_midpoint.median():.2f}; within estimate range {((d.actual_days >= d.est_lo_days) & (d.actual_days <= d.est_hi_days)).sum()}/{len(d)}; below range {(d.actual_days < d.est_lo_days).sum()}")
    print(d.groupby("verdict")[["value", "cost"]].mean().round(2))


if __name__ == "__main__":
    main()


def intervals():
    """Second effort measure (added after the protocol): dives ran mostly one after another, so the interval between
    consecutive final-report commits approximates each dive's elapsed time (it includes concurrent scouting/other work)."""
    d = pd.read_csv(OUT / "F_calibration.csv")
    fin = {r: max(git_times(f"research-lab/runs/{r}/report.md")) for r in d.run}
    d["t_final"] = d.run.map(fin)
    d = d.sort_values("t_final")
    d["interval_days"] = d.t_final.diff() / 86400
    d["final_report"] = pd.to_datetime(d.t_final, unit="s").dt.tz_localize("UTC").dt.tz_convert("Pacific/Auckland").dt.strftime("%Y-%m-%d %H:%M")
    d["ratio_interval_to_midpoint"] = d.interval_days / ((d.est_lo_days + d.est_hi_days) / 2)
    d.to_csv(OUT / "F_calibration.csv", index=False)
    print(d[["run", "final_report", "interval_days", "est_lo_days", "est_hi_days", "ratio_interval_to_midpoint"]].round(2).to_string(index=False))
    print(f"median interval {d.interval_days.median():.2f} d; median ratio to estimate midpoint {d.ratio_interval_to_midpoint.median():.2f}; span {d.final_report.iloc[0]} -> {d.final_report.iloc[-1]}")


if __name__ == "__main__" and "--intervals" in __import__("sys").argv:
    intervals()
