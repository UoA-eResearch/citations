"""Archive Auckland Transport's GTFS-Realtime feed (lead movement-akl-crl-full-timetable-reliability).

AT publishes the realtime feed live only: there is no public archive, so the pre-period of the City Rail Link
full-timetable step-up can only be captured by recording it now. This script is run once a minute by cron and
decides for itself whether to poll.

  trip updates   every 60 s in service hours, and every 30 s in the weekday peaks (two polls per invocation),
                 because the legacy feed carries only the NEXT stop per trip, so cadence sets how many stop
                 events are seen
  service alerts every 15 minutes (cancellations and disruptions)
  feed version   once a day; the static GTFS zip is downloaded whenever feed_version changes (no key needed)

The API key is the owner's and is shared with the lab: it allows 600 calls/minute and 35,000 calls/week, and the
owner's public map breaks if the weekly cap is exhausted. WEEKLY_CAP below holds this collector to about a third
of it; the guard counts the calls already recorded this ISO week and stops when the cap is reached. The key is
read at run time from ~/.config/at/key and never written to a file, a log or the index.

Every response is stored verbatim, gzipped, with its sha256 in an index line; a failed call is recorded as an
error and never as absence.
"""
import datetime as dt
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

RUN = Path(__file__).resolve().parents[1]
DATA, LOGS = RUN / "data", RUN / "logs"
NZ = ZoneInfo("Pacific/Auckland")
API = "https://api.at.govt.nz/"
STATIC_URL = "https://gtfs.at.govt.nz/gtfs.zip"
KEY_FILE = Path(os.path.expanduser("~/.config/at/key"))
WEEKLY_CAP = 13000          # of the key's 35,000/week; the rest stays free for the owner's map
SERVICE_HOURS = set(range(5, 24)) | {0}
PEAK = [(6, 0, 9, 0), (15, 30, 18, 30)]     # weekday only, polled twice a minute


def now():
    return dt.datetime.now(tz=NZ)


def in_peak(t):
    if t.weekday() >= 5:
        return False
    m = t.hour * 60 + t.minute
    return any(h1 * 60 + m1 <= m < h2 * 60 + m2 for h1, m1, h2, m2 in PEAK)


def index_path(t):
    return DATA / "gtfsrt" / f"index_{t.strftime('%G-W%V')}.jsonl"


def calls_this_week(t):
    p = index_path(t)
    if not p.exists():
        return 0
    with open(p) as fh:
        return sum(1 for _ in fh)


def record(t, row):
    p = index_path(t)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def log(msg):
    LOGS.mkdir(exist_ok=True)
    with open(LOGS / "collect.log", "a") as fh:
        fh.write(f"{now().isoformat(timespec='seconds')} {msg}\n")


def fetch(endpoint, key):
    """One API call. Returns (status, body_bytes, seconds); status is an int or an error string."""
    req = urllib.request.Request(API + endpoint, headers={"Ocp-Apim-Subscription-Key": key,
                                                          "User-Agent": "UoA research-lab GTFS-RT archive"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=50) as r:
            return r.status, r.read(), time.time() - t0
    except urllib.error.HTTPError as e:                      # noqa: PERF203
        return e.code, b"", time.time() - t0
    except Exception as e:                                   # noqa: BLE001
        return type(e).__name__, b"", time.time() - t0


def poll(endpoint, name, key):
    t = now()
    if calls_this_week(t) >= WEEKLY_CAP:
        log(f"weekly cap {WEEKLY_CAP} reached; skipping {name}")
        return False
    status, body, secs = fetch(endpoint, key)
    row = dict(utc=dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds"),
               nz=t.isoformat(timespec="seconds"), endpoint=name, status=status, bytes=len(body),
               seconds=round(secs, 2))
    if isinstance(status, int) and status == 200 and body:
        d = DATA / "gtfsrt" / t.strftime("%Y-%m-%d")
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{name}_{t.strftime('%H%M%S')}.json.gz"
        with gzip.open(f, "wb", compresslevel=6) as fh:
            fh.write(body)
        row.update(file=str(f.relative_to(DATA)), sha256=hashlib.sha256(body).hexdigest())
    else:
        row["error"] = True
        log(f"{name} failed: {status}")
    record(t, row)
    return True


def static_check(key):
    """Once a day: the feed version, and the static GTFS whenever it changes."""
    t = now()
    seen = DATA / "static" / "versions.jsonl"
    if seen.exists() and any(json.loads(l)["nz"][:10] == t.strftime("%Y-%m-%d") for l in open(seen)):
        return
    status, body, _ = fetch("gtfs/v3/versions", key)
    record(t, dict(utc=dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec="seconds"),
                   nz=t.isoformat(timespec="seconds"), endpoint="versions", status=status, bytes=len(body)))
    if not (isinstance(status, int) and status == 200 and body):
        log(f"versions failed: {status}")
        return
    ver = json.loads(body)["data"][0]["attributes"]["feed_version"]
    seen.parent.mkdir(parents=True, exist_ok=True)
    known = {json.loads(l).get("feed_version") for l in open(seen)} if seen.exists() else set()
    with open(seen, "a") as fh:
        fh.write(json.dumps(dict(nz=t.isoformat(timespec="seconds"), feed_version=ver)) + "\n")
    if ver in known:
        return
    out = DATA / "static" / f"gtfs_{t.strftime('%Y%m%d')}.zip"
    r = subprocess.run(["curl", "-sL", "--max-time", "600", "-o", str(out), STATIC_URL], check=False)
    ok = r.returncode == 0 and out.exists() and out.stat().st_size > 1_000_000
    log(f"static GTFS {ver}: {'saved ' + str(out.stat().st_size) if ok else 'FAILED'}")
    if ok:
        with open(DATA / "static" / "SHA256SUMS", "a") as fh:
            fh.write(f"{hashlib.sha256(out.read_bytes()).hexdigest()}  {out.name}  {ver}\n")


def main():
    key = KEY_FILE.read_text().strip()
    t = now()
    if t.hour not in SERVICE_HOURS:
        return
    static_check(key)
    if t.minute % 15 == 0:
        poll("realtime/legacy/servicealerts", "servicealerts", key)
    if not poll("realtime/legacy/tripupdates", "tripupdates", key):
        return
    if in_peak(t):
        time.sleep(30)
        poll("realtime/legacy/tripupdates", "tripupdates", key)


if __name__ == "__main__":
    main()
