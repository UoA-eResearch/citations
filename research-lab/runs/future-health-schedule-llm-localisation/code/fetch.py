"""Fetch the sources (plan section 2) into data/raw/.
NZ: Pharmac Schedule XML and PDF for 2025-11-01 (stability edition, per-month archive folder) and 2026-10 (answers).
AU: PBS API v3 for schedule 4751 (2026-10-01; items, restrictions, item-restriction relationships, prescribing texts,
restriction-prescribing-text relationships) and schedule 3834 (2025-11-01, the earliest available; items, restrictions,
item-restriction relationships). The public unregistered-user subscription key is read from the PBS_KEY environment
variable at run time and never written anywhere; the unregistered rate limit is one request per 20 s, so requests are
21 s apart. Resumable per page; SHA-256 to data/raw/SHA256SUMS."""
import hashlib
import json
import os
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = {"User-Agent": "research-lab schedule benchmark (mailto:noreply@anthropic.com)"}
PH = "https://schedule.pharmac.govt.nz"
NZ = {"Schedule_2025-11.xml": "/pub/schedule/archive/2025/2025-11-01/Schedule_2025-11-01.xml",
      "Schedule_2025-11.pdf": "/pub/schedule/archive/2025/2025-11-01/Schedule_2025-11-01.pdf",
      "Schedule_2026-10.xml": "/pub/schedule/archive/Schedule_2026-10.xml"}
API = "https://data-api.health.gov.au/pbs/api/v3/"
PBS = {4751: ["items", "restrictions", "item-restriction-relationships", "prescribing-texts", "restriction-prescribing-text-relationships"],
       3834: ["items", "restrictions", "item-restriction-relationships"]}
LIMIT = 1000


def main():
    (RAW / "nz").mkdir(parents=True, exist_ok=True); (RAW / "pbs").mkdir(parents=True, exist_ok=True)
    for name, path in NZ.items():
        f = RAW / "nz" / name
        if not f.exists():
            r = requests.get(PH + path, headers=UA, timeout=300); r.raise_for_status(); f.write_bytes(r.content); time.sleep(1)
    key = os.environ["PBS_KEY"]
    for code, eps in PBS.items():
        for ep in eps:
            page = 1
            while True:
                f = RAW / "pbs" / f"{code}_{ep}_{page:03d}.json"
                if not f.exists():
                    for i in range(5):
                        r = requests.get(API + ep, params=dict(schedule_code=code, limit=LIMIT, page=page),
                                         headers={**UA, "Subscription-Key": key}, timeout=120)
                        time.sleep(21)
                        if r.status_code == 200:
                            break
                    r.raise_for_status()
                    f.write_text(r.text)
                d = json.loads(f.read_text())
                n = d["_meta"]["total_records"]
                print(code, ep, page, len(d["data"]), "of", n, flush=True)
                if page * LIMIT >= n or not d["data"]:
                    break
                page += 1
    with open(RAW / "SHA256SUMS", "w") as fh:
        for f in sorted(RAW.rglob("*")):
            if f.is_file() and f.name != "SHA256SUMS":
                fh.write(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(RAW)}\n")


if __name__ == "__main__":
    main()
