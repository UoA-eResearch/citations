"""Progress figures for the A1 (MPO unswapping) runs, parsed from the run logs: total tensor elements of the core MPO
and unitaries consumed against wall-clock hours. Writes results/figures/a1_progress.png and
results/tables/a1_progress_series.csv. Uses no answer data."""
import re
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
LOGS = {"P9, cutoff 0.002 (validation)": "P9_A1.log", "P11, cutoff 0.002": "P11_A1_mb8192.log",
        "P11, cutoff 0.001": "P11_A1_mb8192_c0.001_s123.log", "P11, cutoff 0.0005": "P11_A1_mb8192_c0.0005_s123.log",
        "P12, cutoff 0.002": "P12_A1_mb8192_c0.002_s123.log"}
LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\S*\s+\[INFO\](.*)$")


def parse(path):
    rows, t0, tu = [], None, 0
    for line in open(path, errors="ignore"):
        m = LINE.match(line)
        if not m:
            continue
        t = datetime.fromisoformat(m.group(1))
        t0 = t0 or t
        body = m.group(2)
        u = re.search(r"t_u: (\d+)/(\d+)", body)
        if u:
            tu = int(u.group(1))
        e = re.search(r"'total_elems': (\d+)", body)
        b = re.search(r"'max_bond': (\d+)", body)
        if e and "[start compressing]" not in body:
            rows.append(dict(hours=(t - t0).total_seconds() / 3600, total_elems=int(e.group(1)), max_bond=int(b.group(1)) if b else None, unitaries=tu))
    return pd.DataFrame(rows)


def main():
    series = []
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for lab, f in LOGS.items():
        d = parse(RUN / "logs" / f)
        if d.empty:
            continue
        d["run"] = lab
        series.append(d)
        sm = d.set_index(pd.to_timedelta(d.hours, unit="h")).total_elems.rolling("10min").median()
        ax[0].plot(d.hours, sm.values, lw=1.0, label=lab)
        ax[1].plot(d.hours, d.unitaries, lw=1.2, label=lab)
    ax[0].set_yscale("log")
    ax[0].set_xlabel("wall-clock hours")
    ax[0].set_ylabel("core MPO tensor elements\n(10-minute rolling median)")
    ax[1].set_xlabel("wall-clock hours")
    ax[1].set_ylabel("two-qubit unitaries absorbed")
    ax[1].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    (RUN / "results" / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(RUN / "results" / "figures" / "a1_progress.png", dpi=150)
    allser = pd.concat(series)
    allser.to_csv(RUN / "results" / "tables" / "a1_progress_series.csv", index=False)
    # per-run summary (replaces the hand-built A1_progress.csv; review issue 8): bond and progress from the series
    summ = allser.groupby("run").agg(hours=("hours", "max"), peak_max_bond=("max_bond", "max"), unitaries_absorbed=("unitaries", "max"))
    tot = {"P9": 1885, "P11": 1984, "P12": 2433}
    summ["total_unitaries"] = [tot[r.split(",")[0]] for r in summ.index]
    summ["finished"] = summ.unitaries_absorbed >= summ.total_unitaries - 1
    summ.to_csv(RUN / "results" / "tables" / "A1_progress.csv")
    print(summ)
    # bond dimension against unitaries absorbed for the completed runs (plan section 5; review issue 6)
    fig2, ax2 = plt.subplots(figsize=(5.5, 3.4))
    for lab, f in [("P9, cutoff 0.002", "P9_A1_mb8192_c0.002_s123_stats.csv"), ("P11, cutoff 0.002", "P11_A1_mb8192_c0.002_s123_stats.csv")]:
        st = pd.read_csv(RUN / "results" / "tables" / f)
        st["u"] = st.u_consumed_total.ffill().fillna(0)
        ab = st[st.stage == "absorbing"]
        ax2.plot(ab.u / ab.u.max(), ab.max_bond, ".", ms=2, label=lab)
    ax2.set_yscale("log")
    ax2.set_xlabel("fraction of two-qubit unitaries absorbed")
    ax2.set_ylabel("core MPO max bond")
    ax2.legend(frameon=False, fontsize=8)
    fig2.tight_layout()
    fig2.savefig(RUN / "results" / "figures" / "a1_bond_vs_absorbed.png", dpi=150)
    print(pd.concat(series).groupby("run").agg(hours=("hours", "max"), peak_elems=("total_elems", "max"), peak_bond=("max_bond", "max"), unitaries=("unitaries", "max")))


if __name__ == "__main__":
    main()
