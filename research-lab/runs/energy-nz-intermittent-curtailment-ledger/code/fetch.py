"""Fetch the inputs of plan section 2 from the EMI Azure blob store.

  offers   one daily file at a time, streamed and filtered: energy rows, latest submissions (IsLatestYesNo = Y), with
           a potential forecast. Written to data/offers/YYYYMMDD.csv.gz; the raw file is never stored.
  gen      Generation_MD monthly files (half-hourly metered output by generator, fuel and technology codes)
  prices   FinalEnergyPrices monthly files (final price by node and trading period)

Each completed file is logged in data/fetch_log.jsonl (rows read and kept, bytes). A day that fails after retries is
logged as failed and the script exits non-zero: a failed download must never pass for a day with no offers.

  python code/fetch.py [offers|gen|prices|all] [--workers N]
"""
import csv
import datetime as dt
import gzip
import io
import json
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
BLOB = "https://emidatasets.blob.core.windows.net/publicdata/Datasets/Wholesale"
UA = {"User-Agent": "Mozilla/5.0 (research; University of Auckland research lab)"}
START, END = dt.date(2019, 8, 1), dt.date(2026, 9, 30)
KEEP = ["TradingDate", "TradingPeriod", "ParticipantCode", "PointOfConnection", "Unit", "SubmissionOrder",
        "UTCSubmissionDate", "UTCSubmissionTime", "Tranche", "MaximumOutputMegawatts",
        "ForecastOfGenerationPotentialMegawatts", "Megawatts", "DollarsPerMegawattHour"]
LOG = DATA / "fetch_log.jsonl"
lock = threading.Lock()


def log(rec):
    with lock, open(LOG, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def done_set():
    if not LOG.exists():
        return set()
    return {json.loads(l)["file"] for l in open(LOG) if json.loads(l).get("status") == "ok"}


def open_url(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300)


def offers_day(d):
    name = f"{d:%Y%m%d}_Offers.csv"
    url = f"{BLOB}/BidsAndOffers/Offers/{d:%Y}/{name}"
    out = DATA / "offers" / f"{d:%Y%m%d}.csv.gz"
    for attempt in range(4):
        try:
            n_read = n_kept = 0
            tmp = out.with_suffix(".tmp")
            with open_url(url) as r, gzip.open(tmp, "wt", newline="") as fo:
                rd = csv.reader(io.TextIOWrapper(r, encoding="utf-8", newline=""))
                head = next(rd)
                ix = {c: i for i, c in enumerate(head)}
                need = ["ProductType", "IsLatestYesNo", "ForecastOfGenerationPotentialMegawatts"] + KEEP
                missing = [c for c in need if c not in ix]
                if missing:
                    raise RuntimeError(f"columns missing: {missing}")
                pt, lt, fp = ix["ProductType"], ix["IsLatestYesNo"], ix["ForecastOfGenerationPotentialMegawatts"]
                keep_ix = [ix[c] for c in KEEP]
                w = csv.writer(fo)
                w.writerow(KEEP)
                for row in rd:
                    n_read += 1
                    if row[pt] == "Energy" and row[lt] == "Y" and row[fp].strip():
                        w.writerow([row[i] for i in keep_ix])
                        n_kept += 1
            if n_read == 0:
                raise RuntimeError("no rows")
            tmp.rename(out)
            log({"file": name, "kind": "offers", "status": "ok", "rows": n_read, "kept": n_kept})
            return name, n_read, n_kept
        except Exception as e:                    # retried, then logged as failed
            err = repr(e)
            time.sleep(10 * (attempt + 1))
    log({"file": name, "kind": "offers", "status": "failed", "error": err})
    return name, -1, -1


def plain(kind, ym):
    if kind == "gen":
        name, path = f"{ym}_Generation_MD.csv", f"Generation/Generation_MD/{ym}_Generation_MD.csv"
    else:
        name, path = f"{ym}_FinalEnergyPrices.csv", f"DispatchAndPricing/FinalEnergyPrices/ByMonth/{ym}_FinalEnergyPrices.csv"
    out = DATA / kind / name
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with open_url(f"{BLOB}/{path}") as r:
                body = r.read()
            if len(body) < 1000:
                raise RuntimeError(f"{len(body)} bytes")
            out.write_bytes(body)
            log({"file": name, "kind": kind, "status": "ok", "bytes": len(body)})
            return name, len(body), 0
        except Exception as e:
            err = repr(e)
            time.sleep(10 * (attempt + 1))
    log({"file": name, "kind": kind, "status": "failed", "error": err})
    return name, -1, -1


def months():
    y, m = START.year, START.month
    while (y, m) <= (END.year, END.month):
        yield f"{y}{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 16
    (DATA / "offers").mkdir(parents=True, exist_ok=True)
    have = done_set()
    jobs = []
    if what in ("gen", "all"):
        jobs += [("plain", "gen", ym) for ym in months() if f"{ym}_Generation_MD.csv" not in have]
    if what in ("prices", "all"):
        jobs += [("plain", "prices", ym) for ym in months() if f"{ym}_FinalEnergyPrices.csv" not in have]
    if what in ("offers", "all"):
        d = END
        while d >= START:                          # newest (largest) first, so the long tail is small files
            if f"{d:%Y%m%d}_Offers.csv" not in have:
                jobs.append(("offers", d))
            d -= dt.timedelta(days=1)
    print(f"{len(jobs)} files to fetch with {workers} workers", flush=True)
    failed, t0 = 0, time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(offers_day, j[1]) if j[0] == "offers" else ex.submit(plain, j[1], j[2]) for j in jobs]
        for k, f in enumerate(as_completed(futs), 1):
            name, a, b = f.result()
            failed += a < 0
            if k % 50 == 0 or a < 0:
                print(f"{k}/{len(jobs)} {name} {'FAILED' if a < 0 else a} ({(time.time() - t0) / 60:.0f} min)",
                      flush=True)
    print(f"done: {len(jobs) - failed} ok, {failed} failed", flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
