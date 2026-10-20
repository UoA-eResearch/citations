"""Recover every retrievable vintage of MBIE's petroleum reserves workbook, plus the realised-production tables.

MBIE's own site answers scripted requests with an Incapsula bot challenge (a 212-byte HTML page, verified
2026-10-20), so the files are taken from the Internet Archive's raw copies (the `id_` modifier returns the bytes
as captured, without the Wayback toolbar). Each capture is downloaded, hashed and deduplicated: several captures
of the same file are the same workbook.

Targets:
  reserves   .../petroleum-reserves.xlsx and any older name (petroleum-reserves-2019.xlsx, reserves.xlsx)
             - field-level 1P/2P/3P reserves and the 14-year production profiles that this study calibrates
  gas        .../Gas.xlsx and the gas quarterly web tables - realised production, for the outcome series

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
BASE = "mbie.govt.nz/assets/Data-Files/Energy/nz-energy-quarterly-and-energy-in-nz/"
CDX = "https://web.archive.org/cdx/search/cdx"
GROUPS = {
    "reserves": ["petroleum-reserves.xlsx", "petroleum-reserves-2019.xlsx", "reserves.xlsx"],
    "gas": ["Gas.xlsx", "gas-quarterly-webtable.xlsx", "gas-quarterly-webtable-december-2025.xlsx"],
}
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


def captures(name):
    """Every HTTP-200 capture of one filename, oldest first (the Archive is polite: one query at a time)."""
    url = f"{CDX}?url={BASE}{name}*&output=json&fl=timestamp,original,statuscode,length&limit=300"
    body = get(url)
    if not body:
        log(f"{name}: CDX gave nothing")
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
    for group, names in GROUPS.items():
        if only and group != only:
            continue
        d = RAW / group
        d.mkdir(parents=True, exist_ok=True)
        seen = {v["sha256"] for v in man.get(group, {}).values()}
        rows = man.setdefault(group, {})
        for name in names:
            for ts, orig in captures(name):
                if ts in rows:
                    continue
                time.sleep(2)
                body = get(f"https://web.archive.org/web/{ts}id_/{orig}")
                if not body or len(body) < 20000 or body[:2] != b"PK":
                    log(f"  {name} {ts}: not a workbook ({len(body) if body else 0} bytes)")
                    continue
                h = hashlib.sha256(body).hexdigest()
                dup = h in seen
                if not dup:
                    (d / f"{ts}.xlsx").write_bytes(body)
                    seen.add(h)
                rows[ts] = dict(url=orig, bytes=len(body), sha256=h, duplicate_of_earlier=dup,
                                file=None if dup else f"{group}/{ts}.xlsx")
                log(f"  {name} {ts}: {len(body)} bytes{' (duplicate content)' if dup else ' SAVED'}")
                json.dump(man, open(man_path, "w"), indent=1)
    json.dump(man, open(man_path, "w"), indent=1)
    for g, rows in man.items():
        log(f"{g}: {len(rows)} captures, {sum(1 for v in rows.values() if not v['duplicate_of_earlier'])} distinct files")


if __name__ == "__main__":
    main()
