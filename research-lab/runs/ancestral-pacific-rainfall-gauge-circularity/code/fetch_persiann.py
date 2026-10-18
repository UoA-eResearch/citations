"""Secondary pair inputs (plan section 2): PERSIANN (UCI CHRS, daily, 0.25 deg, satellite-only) and PERSIANN-CDR (NCEI,
daily, 0.25 deg) for 2001-2020, and the GPCC Full Data Monthly v2022 2.5 deg files (gauge counts) for 2001-2020.
Four download streams per server; resumable (a file is written to .part and renamed when complete); every failure is
logged to data/raw/persiann_errors.txt. The 72-hour feasibility clock starts with this script's first run.
Writes data/raw/persiann/, data/raw/persiann_cdr/, data/raw/gpcc/."""
import datetime as dt
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = {"User-Agent": "research-lab rainfall study (mailto:noreply@anthropic.com)"}
P_URL = "https://persiann.eng.uci.edu/CHRSdata/PERSIANN/daily/ms6s4_d{yy:02d}{doy:03d}.bin.gz"
C_DIR = "https://www.ncei.noaa.gov/data/precipitation-persiann/access/{y}/"
G_URL = "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/25/full_data_monthly_v2022_{a}_{b}_25.nc.gz"
DAYS = [dt.date(2001, 1, 1) + dt.timedelta(d) for d in range((dt.date(2020, 12, 31) - dt.date(2001, 1, 1)).days + 1)]


def get(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return "have"
    tmp = dest.with_suffix(dest.suffix + ".part")
    for i in range(5):
        try:
            with requests.get(url, headers=UA, timeout=300, stream=True) as r:
                if r.status_code == 404:
                    return "404"
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 16):
                        fh.write(chunk)
            tmp.rename(dest)
            return "ok"
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]
            time.sleep(20 * (i + 1))
    with open(RAW / "persiann_errors.txt", "a") as fh:
        fh.write(f"{url}\t{err}\n")
    return "error"


def main():
    for d in ("persiann", "persiann_cdr", "gpcc"):
        (RAW / d).mkdir(parents=True, exist_ok=True)
    clock = RAW / "persiann_clock.txt"
    if not clock.exists():
        clock.write_text(dt.datetime.now(dt.timezone.utc).isoformat() + "\n")
    for a, b in ((2001, 2010), (2011, 2020)):
        print("gpcc", a, get(G_URL.format(a=a, b=b), RAW / "gpcc" / f"full_data_monthly_v2022_{a}_{b}_25.nc.gz"), flush=True)
    jobs_p = [(P_URL.format(yy=d.year % 100, doy=d.timetuple().tm_yday), RAW / "persiann" / f"ms6s4_d{d.year % 100:02d}{d.timetuple().tm_yday:03d}.bin.gz")
              for d in DAYS]
    jobs_c = []
    for y in range(2001, 2021):
        html = requests.get(C_DIR.format(y=y), headers=UA, timeout=120).text
        names = sorted(set(re.findall(r"PERSIANN-CDR_v01r01_\d{8}_c\d{8}\.nc", html)))
        jobs_c += [(C_DIR.format(y=y) + n, RAW / "persiann_cdr" / n) for n in names]
    print(len(jobs_p), "PERSIANN days;", len(jobs_c), "PERSIANN-CDR files listed", flush=True)
    with ThreadPoolExecutor(4) as ep, ThreadPoolExecutor(4) as ec:
        fp = [ep.submit(get, u, d) for u, d in jobs_p]
        fc = [ec.submit(get, u, d) for u, d in jobs_c]
        for k, f in enumerate(fp + fc):
            f.result()
            if k % 500 == 0:
                print(k, "of", len(fp) + len(fc), flush=True)
    for name, fs in (("persiann", fp), ("persiann_cdr", fc)):
        res = [f.result() for f in fs]
        print(name, {s: res.count(s) for s in set(res)}, flush=True)


if __name__ == "__main__":
    main()
