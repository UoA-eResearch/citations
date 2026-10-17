"""Download every PHARMAC Schedule Update PDF listed on cpsupdates.php (data/raw/pharmac/pdf_list.txt), politely
(one at a time, 1 s apart), resumable; records sha256 in data/raw/pharmac/MANIFEST.tsv."""
import hashlib
import sys
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data" / "raw" / "pharmac"
UA = {"User-Agent": "research-lab medicines-access study (mailto:noreply@anthropic.com)"}


def main():
    paths = [l.strip() for l in open(D / "pdf_list.txt") if l.strip()]
    man = D / "MANIFEST.tsv"
    done = {l.split("\t")[0] for l in open(man)} if man.exists() else set()
    with open(man, "a") as fh:
        for p in paths:
            if p in done:
                continue
            out = D / "su" / (p.strip("/").replace("/", "-"))
            out.parent.mkdir(parents=True, exist_ok=True)
            for k in range(5):
                try:
                    r = requests.get("https://schedule.pharmac.govt.nz" + p, headers=UA, timeout=120)
                    if r.status_code == 200 and r.content[:4] == b"%PDF":
                        out.write_bytes(r.content)
                        fh.write(f"{p}\t{len(r.content)}\t{hashlib.sha256(r.content).hexdigest()}\n"); fh.flush()
                        break
                    print("status", r.status_code, p, flush=True)
                except Exception as e:
                    print("err", p, str(e)[:80], flush=True)
                time.sleep(5 * (k + 1))
            time.sleep(1)
    print("pharmac done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
