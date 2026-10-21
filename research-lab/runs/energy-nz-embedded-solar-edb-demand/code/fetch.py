"""Fetch every input (plan section 2) into data/raw/, recording sizes and sha256 in data/raw/manifest.json.

  comcom/  Commerce Commission information-disclosure Parquet and data dictionary
  ea/      Electricity Authority installed-DG trends (EMI report GUEHMT), CSV by network participant
  emi/     Network Supply Points table; half-hourly Grid_import and Grid_export for December-February
  weather/ Open-Meteo historical daily temperature at each load centre (weather.py lists them)

Files already present with a recorded hash are not fetched again. A failed request is fatal: an empty or missing
input must never pass for an absent one.
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weather  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (research; University of Auckland research lab)"}
COMCOM = "https://www.comcom.govt.nz"
EMI = "https://www.emi.ea.govt.nz"
COMCOM_FILES = ["/assets/file/0035/366299/EDB_ID_Full_2026-06-01.parquet",
                "/assets/file/0032/366296/EDB_ID_Data_Dictionary.json",
                "/assets/excel_doc/0019/366301/EDB_ID_Version_History.xlsx"]
SEGMENTS = ["All", "Res", "SME", "Com", "Ind"]
SIZES = ["All_Total", "Small", "Large"]
SUMMERS = range(2014, 2026)                       # summer 2014/15 = Dec 2014 - Feb 2015, ... 2025/26
NSP_TABLE = "20261020_NetworkSupplyPointsTable.csv"


def get(url, dest, min_bytes=100):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        return
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                body = r.read()
            if len(body) < min_bytes:
                raise RuntimeError(f"{len(body)} bytes")
            dest.write_bytes(body)
            time.sleep(1.5)
            return
        except Exception as e:                    # retried, then fatal
            err = e
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"FETCH FAILED {url}: {err}")


def ea_url(segment, size, fuel):
    q = dict(DateFrom="20130901", DateTo="20261031", RegionType="NWKP", MarketSegment=segment, Capacity=size,
             FuelType=fuel, Show="Capacity", seriesFilter="ALL", _rsdr="ALL", _si="v|4")
    return f"{EMI}/Retail/Download/DataReport/CSV/GUEHMT?" + urllib.parse.urlencode(q)


def main():
    for f in COMCOM_FILES:
        get(COMCOM + f, RAW / "comcom" / Path(f).name)
    for seg in SEGMENTS:
        for size in SIZES:
            get(ea_url(seg, size, "solar_all"), RAW / "ea" / f"solar_{seg}_{size}.csv")
    get(ea_url("All", "All_Total", "All_Total"), RAW / "ea" / "dg_All_All_All_Total.csv")
    get(ea_url("All", "All_Total", "standalone batt"), RAW / "ea" / "dg_All_All_standalonebatt.csv", min_bytes=50)
    get(f"{EMI}/Wholesale/Datasets/MappingsAndGeospatial/NetworkSupplyPointsTable/{NSP_TABLE}",
        RAW / "emi" / NSP_TABLE)
    for y in SUMMERS:
        for ym in (f"{y}12", f"{y + 1}01", f"{y + 1}02"):
            for kind in ("Grid_import", "Grid_export"):
                get(f"{EMI}/Wholesale/Datasets/Metered_data/{kind}/{ym}_{kind}.csv",
                    RAW / "emi" / kind / f"{ym}_{kind}.csv", min_bytes=10_000)
    for key, (lat, lon) in weather.points().items():
        q = dict(latitude=lat, longitude=lon, start_date="2013-04-01", end_date="2026-03-31",
                 daily="temperature_2m_mean,temperature_2m_max", timezone="Pacific/Auckland")
        get("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q),
            RAW / "weather" / f"{key}.json", min_bytes=10_000)
    manifest = {str(p.relative_to(RAW)): dict(bytes=p.stat().st_size,
                                              sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(RAW.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    json.dump(manifest, open(RAW / "manifest.json", "w"), indent=1)
    print(f"{len(manifest)} files in the manifest")


if __name__ == "__main__":
    main()
