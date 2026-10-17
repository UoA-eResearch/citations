"""Parse and QC the GHCN-Daily PRCP records (plan section 3). Values with a blank quality flag only; runs of >= 5
consecutive identical non-zero daily values removed. Writes data/gauge_daily.csv.gz (station, date, prcp_mm) and
data/gauge_qc.csv (per station: days read, flagged, run-removed, kept)."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]


def parse(f):
    rows = []
    for line in open(f):
        if line[17:21] != "PRCP":
            continue
        y, m = int(line[11:15]), int(line[15:17])
        if y < 1980:
            continue
        for d in range(31):
            v = int(line[21 + 8 * d:26 + 8 * d]); q = line[27 + 8 * d]
            if v == -9999:
                continue
            rows.append((y, m, d + 1, v / 10.0, q))
    df = pd.DataFrame(rows, columns=["y", "m", "d", "prcp", "q"])
    df["date"] = pd.to_datetime(dict(year=df.y, month=df.m, day=df.d), errors="coerce")
    return df.dropna(subset=["date"])


def main():
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    out, qc = [], []
    for sid in st.id:
        f = RUN / "data" / "raw" / "ghcn" / "dly" / f"{sid}.dly"
        if not f.exists():
            qc.append(dict(station=sid, read=0, flagged=0, run_removed=0, kept=0, note="missing file")); continue
        df = parse(f).sort_values("date")
        n0 = len(df)
        df = df[df.q == " "]
        nflag = n0 - len(df)
        # runs of >= 5 identical non-zero values on consecutive days
        s = df.set_index("date").prcp.asfreq("D")
        grp = (s != s.shift()).cumsum()
        run = s.groupby(grp).transform("size")
        bad = (run >= 5) & (s > 0)
        s = s[~bad].dropna()
        qc.append(dict(station=sid, read=n0, flagged=nflag, run_removed=int(bad.sum()), kept=len(s), note=""))
        out.append(pd.DataFrame(dict(station=sid, date=s.index, prcp_mm=s.values)))
    pd.concat(out).to_csv(RUN / "data" / "gauge_daily.csv.gz", index=False)
    pd.DataFrame(qc).to_csv(RUN / "data" / "gauge_qc.csv", index=False)
    print(len(out), "stations;", sum(q["kept"] for q in qc), "valid days")


if __name__ == "__main__":
    main()
