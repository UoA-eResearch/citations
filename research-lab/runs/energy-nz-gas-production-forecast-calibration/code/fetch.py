"""Recover every retrievable vintage of MBIE's petroleum reserves workbook, plus the realised-production tables.

MBIE's own site answers scripted requests with an Incapsula bot challenge (a 212-byte HTML page, verified
2026-10-20), so the files are taken from the Internet Archive's raw copies (the `id_` modifier returns the bytes
as captured, without the Wayback toolbar). Each capture is downloaded, hashed and deduplicated: several captures
of the same file are the same workbook.

Targets:
  reserves   every vintage: .../Energy/petroleum-reserves/petroleum-reserves-1-jan-YYYY.xlsx (2014-2026), plus the
             older names under .../nz-energy-quarterly-and-energy-in-nz/ - field-level 1P/2P/3P reserves and the
             14-year production profiles that this study calibrates
  gas        .../Gas.xlsx and the gas quarterly web tables - realised production, for the outcome series

An earlier version searched only the nz-energy-quarterly directory, never .../Energy/petroleum-reserves/, where
every vintage from 2014 to 2026 is archived; and it logged a failed archive query as "CDX gave nothing", the same
message as a genuine empty result. Together these produced a false claim that the 2025 and 2026 releases were not
archived (corrected in deviations D2). A failed query is now recorded in the manifest and makes the run exit
non-zero, so absence can never be inferred from a failure.

Writes data/raw/<group>/<timestamp>.xlsx, data/raw/MANIFEST.json (capture timestamp, URL, bytes, sha256) and
logs/fetch.log. Nothing is parsed here.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
QUARTERLY = "mbie.govt.nz/assets/Data-Files/Energy/nz-energy-quarterly-and-energy-in-nz/"
RESERVES = "mbie.govt.nz/assets/Data-Files/Energy/petroleum-reserves/"
CDX = "https://web.archive.org/cdx/search/cdx"
# group -> list of (directory, filename prefix); each prefix is queried with a trailing wildcard
GROUPS = {
    "reserves": [(RESERVES, "petroleum-reserves-1-jan-"),
                 (QUARTERLY, "petroleum-reserves.xlsx"), (QUARTERLY, "petroleum-reserves-2019.xlsx"),
                 (QUARTERLY, "reserves.xlsx")],
    "gas": [(QUARTERLY, "Gas.xlsx"), (QUARTERLY, "gas-quarterly-webtable.xlsx"),
            (QUARTERLY, "gas-quarterly-webtable-december-2025.xlsx")],
}
FAILED = []
# Inputs that are not reserves workbooks: fetched from fixed sources and recorded with their hashes (D2 -- the draft
# used these without any fetch record). The two MBIE tables are exact Internet Archive captures; the Gas Industry Co
# file is a live workbook that GIC replaces, so it is fetched once and its hash recorded rather than re-downloaded.
OTHER = [
    ("mbie_other/energy-overview_20260917134627.xlsx",
     "https://web.archive.org/web/20260917134627id_/https://www.mbie.govt.nz/assets/Data-Files/Energy/"
     "nz-energy-quarterly-and-energy-in-nz/energy-overview.xlsx", False),
    ("mbie_other/energy-balance-tables_20260927185007.xlsx",
     "https://web.archive.org/web/20260927185007id_/https://www.mbie.govt.nz/assets/Data-Files/Energy/"
     "nz-energy-quarterly-and-energy-in-nz/energy-balance-tables.xlsx", False),
    ("gic/ProductionConsumption.xlsx",
     "https://weblink.blob.core.windows.net/$web/ProductionConsumption.xlsx", True),   # linked from
    # https://www.gasindustry.co.nz/data/gas-production-and-consumption/
]


def fetch_other(man):
    rows = man.setdefault("other", {})
    for rel, url, live in OTHER:
        dest = RAW / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if live and dest.exists():
            body = dest.read_bytes()
            note = "kept the copy already on disk (live source, not re-downloaded)"
        else:
            time.sleep(2)
            body = get(url)
            if not body or body[:2] != b"PK":
                FAILED.append(url); log(f"  {rel}: download failed"); continue
            if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != hashlib.sha256(body).hexdigest():
                log(f"  {rel}: WARNING fresh download differs from the copy on disk")
            dest.write_bytes(body)
            note = "downloaded"
        rows[rel] = dict(url=url, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), live_source=live,
                         note=note)
        log(f"  {rel}: {len(body)} bytes, sha256 {rows[rel]['sha256'][:16]} ({note})")
UA = {"User-Agent": "UoA research-lab (gas production forecast calibration); contact via github.com/UoA-eResearch"}


def log(msg):
    (RUN / "logs").mkdir(exist_ok=True)
    print(msg, flush=True)
    with open(RUN / "logs" / "fetch.log", "a") as fh:
        fh.write(msg + "\n")


def get(url, tries=6, timeout=120):
    """One GET with backoff. Returns bytes, or None after `tries` failures."""
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:                       # noqa: BLE001
            log(f"  attempt {k + 1}/{tries} failed ({type(e).__name__}); backing off")
            time.sleep(5 * (k + 1))
    return None


def captures(base, name):
    """Every HTTP-200 capture under one directory and filename prefix, oldest first (one query at a time)."""
    url = f"{CDX}?url={base}{name}*&output=json&fl=timestamp,original,statuscode,length&limit=300"
    body = get(url)
    if body is None:
        log(f"{base}{name}: CDX QUERY FAILED after retries -- this is not evidence the file is absent")
        FAILED.append(f"{base}{name}")
        return []
    if not body.strip():
        log(f"{base}{name}: CDX returned an empty response (no captures)")
        return []
    try:
        rows = json.loads(body)[1:]
    except Exception:                                # noqa: BLE001
        log(f"{name}: CDX response was not JSON")
        return []
    out = [(r[0], r[1]) for r in rows if r[2] == "200"]
    log(f"{name}: {len(out)} captures with status 200")
    return sorted(set(out))


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    man_path = RAW / "MANIFEST.json"
    man = json.load(open(man_path)) if man_path.exists() else {}
    if only in (None, "other"):
        fetch_other(man)
        json.dump(man, open(man_path, "w"), indent=1)
    for group, names in GROUPS.items():
        if only == "other" or (only and group != only):
            continue
        d = RAW / group
        d.mkdir(parents=True, exist_ok=True)
        seen = {v["sha256"] for v in man.get(group, {}).values() if isinstance(v, dict)}
        rows = man.setdefault(group, {})
        for base, name in names:
            for ts, orig in captures(base, name):
                # Several vintages were archived in the same second, so a capture is identified by timestamp AND
                # URL; keying by timestamp alone kept one file per second and silently dropped the rest.
                key = f"{ts}|{orig}"
                if key in rows or (ts in rows and isinstance(rows[ts], dict) and rows[ts].get("url") == orig):
                    continue
                time.sleep(2)
                body = get(f"https://web.archive.org/web/{ts}id_/{orig}")
                if not body or len(body) < 20000 or body[:2] != b"PK":
                    log(f"  {name} {ts}: not a workbook ({len(body) if body else 0} bytes)")
                    continue
                h = hashlib.sha256(body).hexdigest()
                dup = h in seen
                fname = f"{ts}_{orig.rstrip('/').split('/')[-1]}"
                if not dup:
                    (d / fname).write_bytes(body)
                    seen.add(h)
                rows[key] = dict(url=orig, bytes=len(body), sha256=h, duplicate_of_earlier=dup,
                                 file=None if dup else f"{group}/{fname}")
                log(f"  {name} {ts}: {len(body)} bytes{' (duplicate content)' if dup else ' SAVED'}")
                json.dump(man, open(man_path, "w"), indent=1)
    man["_failed_queries"] = FAILED
    json.dump(man, open(man_path, "w"), indent=1)
    for g, rows in man.items():
        if g.startswith("_"):
            continue
        log(f"{g}: {len(rows)} captures, {sum(1 for v in rows.values() if not v.get('duplicate_of_earlier', False))} distinct files")
    if FAILED:
        log(f"FAILED QUERIES: {FAILED}")
        sys.exit(1)


if __name__ == "__main__":
    main()
