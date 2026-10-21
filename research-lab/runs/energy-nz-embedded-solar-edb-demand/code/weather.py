"""Load centres for each distributor (plan section 2) and the weather controls built from Open-Meteo daily data.

Multi-region networks average several points with equal weight. Heating degree-days use base 18 C on the daily mean,
summed over the disclosure year (April-March); the summer control is the mean daily maximum, December-February.
"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
WX = RUN / "data" / "raw" / "weather"
HDD_BASE = 18.0

CENTRES = {
    "Alpine Energy": [("Timaru", -44.40, 171.25)],
    "Aurora Energy": [("Dunedin", -45.87, 170.50), ("Cromwell", -45.04, 169.20)],
    "Buller Electricity": [("Westport", -41.75, 171.60)],
    "Centralines": [("Waipukurau", -39.99, 176.56)],
    "Counties Energy": [("Pukekohe", -37.20, 174.90)],
    "EA Networks": [("Ashburton", -43.90, 171.75)],
    "Electra": [("Levin", -40.62, 175.28), ("Paraparaumu", -40.91, 175.01)],
    "Electricity Invercargill": [("Invercargill", -46.41, 168.35)],
    "Firstlight Network": [("Gisborne", -38.66, 178.02)],
    "Horizon Networks": [("Whakatane", -37.95, 176.99)],
    "MainPower NZ": [("Rangiora", -43.30, 172.60)],
    "Marlborough Lines": [("Blenheim", -41.51, 173.96)],
    "Nelson Electricity": [("Nelson", -41.27, 173.28)],
    "Network Tasman": [("Richmond", -41.34, 173.18)],
    "Network Waitaki": [("Oamaru", -45.10, 170.97)],
    "Northpower": [("Whangarei", -35.73, 174.32)],
    "Orion NZ": [("Christchurch", -43.53, 172.64)],
    "OtagoNet": [("Balclutha", -46.24, 169.74)],
    "Powerco": [("Tauranga", -37.69, 176.17), ("New Plymouth", -39.06, 174.08), ("Palmerston North", -40.35, 175.61),
                ("Whanganui", -39.93, 175.05), ("Masterton", -40.95, 175.66)],
    "Scanpower": [("Dannevirke", -40.21, 176.10)],
    "The Lines Company": [("Te Kuiti", -38.33, 175.17), ("Taumarunui", -38.88, 175.26)],
    "The Power Company": [("Gore", -46.10, 168.94)],
    "Top Energy": [("Kerikeri", -35.23, 173.95)],
    "Unison Networks": [("Hastings", -39.64, 176.84), ("Rotorua", -38.14, 176.25), ("Taupo", -38.69, 176.07)],
    "Vector Lines": [("Auckland", -36.85, 174.76)],
    "WEL Networks": [("Hamilton", -37.79, 175.28)],
    "Waipa Networks": [("Te Awamutu", -38.01, 175.32)],
    "Wellington Electricity": [("Wellington", -41.29, 174.78)],
    "Westpower": [("Greymouth", -42.45, 171.21)],
}


def key(name):
    return name.lower().replace(" ", "_")


def points():
    return {key(n): (lat, lon) for pts in CENTRES.values() for n, lat, lon in pts}


def daily(name):
    d = json.load(open(WX / f"{key(name)}.json"))["daily"]
    x = pd.DataFrame({"date": pd.to_datetime(d["time"]), "tmean": d["temperature_2m_mean"],
                      "tmax": d["temperature_2m_max"]})
    if x[["tmean", "tmax"]].isna().mean().max() > 0.01:
        raise SystemExit(f"weather for {name}: more than 1% missing days")
    return x


def controls():
    """Per distributor: HDD by disclosure year (year ending March) and mean Dec-Feb daily maximum by summer."""
    hdd, summer = [], []
    for edb, pts in CENTRES.items():
        x = pd.concat([daily(n) for n, _, _ in pts]).groupby("date")[["tmean", "tmax"]].mean().reset_index()
        x["disc_yr"] = x.date.dt.year + (x.date.dt.month >= 4)
        x["hdd"] = (HDD_BASE - x.tmean).clip(lower=0)
        h = x.groupby("disc_yr").agg(hdd=("hdd", "sum"), days=("hdd", "size")).reset_index()
        hdd.append(h[h.days >= 365].assign(edb=edb)[["edb", "disc_yr", "hdd"]])
        s = x[x.date.dt.month.isin([12, 1, 2])].copy()
        s["summer"] = s.date.dt.year - (s.date.dt.month <= 2)          # Dec 2014 - Feb 2015 -> summer 2014
        g = s.groupby("summer").agg(tmax=("tmax", "mean"), days=("tmax", "size")).reset_index()
        summer.append(g[g.days >= 89].assign(edb=edb)[["edb", "summer", "tmax"]])
    return pd.concat(hdd, ignore_index=True), pd.concat(summer, ignore_index=True)
