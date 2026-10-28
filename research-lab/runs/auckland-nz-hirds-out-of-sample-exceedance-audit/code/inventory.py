"""Gauge inventory (plan section 1): every rainfall site on the open council Hilltop servers, with coordinates and
the span of its rainfall record. Metadata only; no rainfall values.

  inventory.py -> data/inventory.parquet (server, site, easting, northing [NZTM2000], datasource, measurement, from, to)
                  results/tables/inventory_summary.csv
"""
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SERVERS = {
    "Northland": "https://hilltop.nrc.govt.nz/Data.hts",
    "HawkesBay": "https://data.hbrc.govt.nz/Envirodata/EMAR.hts",
    "Wellington": "https://hilltop.gw.govt.nz/Data.hts",
    "Marlborough": "https://hydro.marlborough.govt.nz/data.hts",
    "Tasman": "https://envdata.tasman.govt.nz/data.hts",
    "Taranaki": "https://extranet.trc.govt.nz/getdata/merged.hts",
    "WestCoast": "https://hilltop.wcrc.govt.nz/Data.hts",
}
UA = {"User-Agent": "UoA research-lab HIRDS audit (non-commercial research)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(3 + 5 * i)
    raise RuntimeError(f"{url[:100]}: {err}")


def sites(server, base):
    x = get(base + "?Service=Hilltop&Request=SiteList&Location=Yes&Measurement=Rainfall")
    out = []
    for name, body in re.findall(r'<Site Name="([^"]+)">(.*?)</Site>', x, re.S):
        e = re.search(r"<Easting>([\d.]+)</Easting>", body)
        n = re.search(r"<Northing>([\d.]+)</Northing>", body)
        out.append({"server": server, "site": name, "easting": float(e.group(1)) if e else None,
                    "northing": float(n.group(1)) if n else None})
    return out


def measurements(args):
    server, base, site = args
    x = get(base + "?Service=Hilltop&Request=MeasurementList&Site=" + urllib.parse.quote(site))
    rows = []
    for ds, body in re.findall(r'<DataSource Name="([^"]+)"[^>]*>(.*?)</DataSource>', x, re.S):
        f = re.search(r"<From>([^<]+)</From>", body)
        t = re.search(r"<To>([^<]+)</To>", body)
        interp = re.search(r"<Interpolation>([^<]+)</Interpolation>", body)
        for m in re.findall(r'<Measurement Name="([^"]+)">', body):
            if "rain" in m.lower():
                rows.append({"server": server, "site": site, "datasource": ds, "measurement": m,
                             "from": f.group(1) if f else None, "to": t.group(1) if t else None,
                             "interpolation": interp.group(1) if interp else None,
                             "virtual": "<VM>" in body.split(f'<Measurement Name="{m}">')[1].split("</Measurement>")[0]})
    return rows


def main():
    D.mkdir(parents=True, exist_ok=True); T.mkdir(parents=True, exist_ok=True)
    S = []
    for server, base in SERVERS.items():
        s = sites(server, base)
        print(server, len(s), "sites", flush=True)
        S += s
    S = pd.DataFrame(S)
    with ThreadPoolExecutor(6) as ex:            # modest load on each council server
        M = [r for rows in ex.map(measurements, [(r.server, SERVERS[r.server], r.site) for r in S.itertuples()]) for r in rows]
    M = pd.DataFrame(M)
    inv = S.merge(M, on=["server", "site"], how="left")
    inv["from"] = pd.to_datetime(inv["from"], errors="coerce"); inv["to"] = pd.to_datetime(inv["to"], errors="coerce")
    inv.to_parquet(D / "inventory.parquet")
    raw = inv[inv.virtual.eq(False) & inv.measurement.notna()]
    summ = raw.groupby("server").agg(sites=("site", "nunique"),
                                     start_by_2007=("from", lambda s: int((s <= "2007-07-01").sum())),
                                     current_2026=("to", lambda s: int((s >= "2026-01-01").sum()))).reset_index()
    raw2 = raw.assign(ok=(raw["from"] <= "2017-07-01") & (raw["to"] >= "2026-01-01"))
    summ["span_covers_out_of_sample"] = summ.server.map(raw2.groupby("server").ok.sum())
    summ.to_csv(T / "inventory_summary.csv", index=False)
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
