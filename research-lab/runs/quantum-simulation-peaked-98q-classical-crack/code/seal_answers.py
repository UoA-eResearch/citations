"""Seal the Helios-1 recovered peak bitstrings (tracker issues #246 P11, #247 P12) WITHOUT displaying them.
Writes data/sealed/answers.json ({instance: [candidate 98-bit strings found in the thread]}) and prints only counts and
SHA-256 hashes. The file is read only by the final scoring script (plan.md)."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
API = "https://api.github.com/repos/quantum-advantage-tracker/quantum-advantage-tracker.github.io/issues/"


def texts(num):
    out = []
    for url in (API + str(num), API + str(num) + "/comments?per_page=100"):
        d = json.load(urllib.request.urlopen(url, timeout=60))
        items = d if isinstance(d, list) else [d]
        out += [(it.get("body") or "") for it in items]
    return "\n".join(out)


def main():
    ans = {}
    for inst, num in [("P11", 246), ("P12", 247)]:
        t = texts(num)
        cands = sorted(set(re.findall(r"(?<![01])[01]{98}(?![01])", t)))
        ans[inst] = cands
        print(inst, "issue", num, "| 98-bit strings found:", len(cands), "| sha256:", [hashlib.sha256(c.encode()).hexdigest()[:16] for c in cands])
    p = RUN / "data" / "sealed" / "answers.json"
    p.write_text(json.dumps(ans))
    print("sealed file sha256:", hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
