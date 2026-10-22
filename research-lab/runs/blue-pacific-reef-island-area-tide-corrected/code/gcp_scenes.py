"""Collection 1 Level-1 Landsat scenes from Google's public archive (D1), 1999-2021, per atoll.

Path/rows come from each atoll's Level-2 scene ids (data/scenes/<atoll>_ls.parquet). For every LT05, LE07 and LC08
scene of those path/rows, the MTL file gives cloud cover, acquisition time, UTM zone and the TOA reflectance
coefficients. Writes data/scenes/<atoll>_l1.parquet (MTL cloud cover <= 80) and results/tables/l1_scenes_log.json.
"""
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import ATOLLS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
GS = "https://storage.googleapis.com/gcp-public-data-landsat"
API = "https://storage.googleapis.com/storage/v1/b/gcp-public-data-landsat/o"
BANDS = {"LT05": ("B2", "B5", "B4"), "LE07": ("B2", "B5", "B4"), "LC08": ("B3", "B6", "B5")}


def get(url, as_json=True):
    for t in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-lab"}), timeout=120) as r:
                b = r.read()
            return json.loads(b) if as_json else b.decode("utf-8", "replace")
        except Exception as e:
            time.sleep(5 * (t + 1))
    return None


def list_scenes(sensor, path, row):
    out, tok = [], None
    while True:
        u = f"{API}?prefix={sensor}/01/{path}/{row}/&delimiter=/&maxResults=1000" + (f"&pageToken={tok}" if tok else "")
        d = get(u) or {}
        out += d.get("prefixes", [])
        tok = d.get("nextPageToken")
        if not tok:
            return out


def mtl(prefix):
    name = prefix.rstrip("/").split("/")[-1]
    sensor = name[:4]
    date = name.split("_")[3]
    y = int(date[:4])
    if not (1999 <= y <= 2021) or (sensor != "LC08" and y > 2015):
        return None
    txt = get(f"{GS}/{prefix}{name}_MTL.txt", as_json=False)
    if not txt:
        return None
    kv = dict(re.findall(r"^\s*(\w+)\s*=\s*\"?([^\"\n]*)\"?", txt, re.M))
    g, s, n = BANDS[sensor]
    try:
        zone = int(kv["UTM_ZONE"])
        return {"id": name, "datetime": f"{kv['DATE_ACQUIRED']}T{kv['SCENE_CENTER_TIME'][:15]}Z", "platform": sensor,
                "cloud": float(kv.get("CLOUD_COVER", 100)), "epsg": 32600 + zone,
                "green": f"{GS}/{prefix}{name}_{g}.TIF", "swir16": f"{GS}/{prefix}{name}_{s}.TIF",
                "nir": f"{GS}/{prefix}{name}_{n}.TIF", "qa": f"{GS}/{prefix}{name}_BQA.TIF",
                **{f"{b}_scale": float(kv[f"REFLECTANCE_MULT_BAND_{x[1:]}"]) for b, x in (("green", g), ("swir16", s), ("nir", n))},
                **{f"{b}_offset": float(kv[f"REFLECTANCE_ADD_BAND_{x[1:]}"]) for b, x in (("green", g), ("swir16", s), ("nir", n))}}
    except (KeyError, ValueError):
        return None


def main():
    lp = RUN / "results" / "tables" / "l1_scenes_log.json"
    log = json.load(open(lp)) if lp.exists() else {}
    for name in ATOLLS:
        src = RUN / "data" / "scenes" / f"{name}_ls.parquet"
        if not src.exists() or (RUN / "data" / "scenes" / f"{name}_l1.parquet").exists():
            continue
        ids = pd.read_parquet(src).id
        prs = sorted({re.search(r"_(\d{3})(\d{3})_", i).groups() for i in ids if re.search(r"_(\d{3})(\d{3})_", i)})
        prefixes = [p for s in BANDS for path, row in prs for p in list_scenes(s, path, row)]
        with ThreadPoolExecutor(16) as ex:
            rows = [r for r in ex.map(mtl, prefixes) if r]
        d = pd.DataFrame(rows)
        d = d[d.cloud <= 80] if len(d) else d
        d.to_parquet(RUN / "data" / "scenes" / f"{name}_l1.parquet", index=False)
        log[name] = {"path_rows": ["".join(p) for p in prs], "listed": len(prefixes), "kept": int(len(d)),
                     "by_sensor_epoch": (d.assign(e=d.datetime.str[:4].astype(int).map(lambda y: "1999-2015" if y <= 2015 else "2016-2021"))
                                         .groupby(["platform", "e"]).size().astype(int).to_dict() if len(d) else {})}
        log[name]["by_sensor_epoch"] = {f"{k[0]} {k[1]}": v for k, v in log[name]["by_sensor_epoch"].items()}
        print(name, log[name], flush=True)
        json.dump(log, open(lp, "w"), indent=1)


if __name__ == "__main__":
    main()
