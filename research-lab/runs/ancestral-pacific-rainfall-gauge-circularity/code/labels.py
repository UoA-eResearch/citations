"""Independence label per station-month (plan section 1): great-circle distance from each gauge to the nearest station
in that month's CHIRPS stations-used list. Writes data/labels.csv (station, ym, nearest_km). Months whose list could
not be fetched get no row (and so no label), never a large distance."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]


def hav(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def main():
    st = pd.read_csv(RUN / "data" / "raw" / "ghcn" / "stations.csv")
    rows = []
    for y in range(1981, 2026):
        for m in range(1, 13):
            f = RUN / "data" / "raw" / "chirps_used" / f"{y}.{m:02d}.csv"
            if not f.exists() or f.stat().st_size == 0:
                continue
            u = pd.read_csv(f, usecols=[0, 1], names=["lat", "lon"], header=0)
            u = u[(u.lat.between(-40, 40)) & ((u.lon >= 100) | (u.lon <= -110))]
            for s in st.itertuples():
                d = hav(s.lat, s.lon, u.lat.values, u.lon.values) if len(u) else np.array([np.inf])
                rows.append((s.id, f"{y}-{m:02d}", float(d.min()) if len(d) else np.inf))
    pd.DataFrame(rows, columns=["station", "ym", "nearest_km"]).to_csv(RUN / "data" / "labels.csv", index=False)
    print(len(rows), "station-months")


if __name__ == "__main__":
    main()
