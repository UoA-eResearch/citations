"""Sampling frame and sample (plan section 3), from the archived Tranco list 64VVX.

Jurisdictions: 14 EU ccTLDs (treated), .co.uk (partly treated: UK firms selling into the EU), and .com.au, .co.nz, .ca
(placebo). Public-sector domains are excluded (the Web Accessibility Directive has covered EU public-sector sites since
2018-2020). Per jurisdiction: up to N_PER sites drawn at random (seeded) from rank <= RANK_MAX; if fewer exist, the
rank limit is widened to 400,000. Writes data/frame/sample.csv and its sha256 to data/frame/MANIFEST.txt.
"""
import csv
import hashlib
import random
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
EU = ["de", "fr", "it", "es", "nl", "pl", "se", "fi", "dk", "ie", "be", "at", "pt", "cz"]
PLACEBO = ["com.au", "co.nz", "ca"]
UK = ["co.uk"]
N_PER, RANK_MAX, RANK_WIDE, SEED = 300, 200_000, 400_000, 20261017
PUBLIC = {"gov", "gouv", "gob", "bund", "govt", "gv", "mil"}


def jurisdiction(d):
    for t in PLACEBO + UK + EU:
        if d.endswith("." + t):
            return t
    return None


def main():
    pool = {}
    for rank, dom in csv.reader(open(RUN / "data" / "raw" / "tranco" / "top-1m.csv")):
        rank, d = int(rank), dom.lower().strip()
        j = jurisdiction(d)
        if j is None or PUBLIC & set(d.split(".")) or rank > RANK_WIDE:
            continue
        pool.setdefault(j, []).append((rank, d))
    rnd = random.Random(SEED)
    rows = []
    for j in EU + UK + PLACEBO:
        cand = [x for x in pool.get(j, []) if x[0] <= RANK_MAX]
        if len(cand) < N_PER:
            cand = pool.get(j, [])
        pick = rnd.sample(cand, min(N_PER, len(cand)))
        group = "eu" if j in EU else ("uk" if j in UK else "placebo")
        rows += [dict(domain=d, rank=r, tld=j, group=group) for r, d in sorted(pick)]
    out = RUN / "data" / "frame"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "sample.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["domain", "rank", "tld", "group"]); w.writeheader(); w.writerows(rows)
    h = hashlib.sha256((out / "sample.csv").read_bytes()).hexdigest()
    (out / "MANIFEST.txt").write_text(f"tranco 64VVX\nsample.csv sha256 {h}\nrows {len(rows)}\n")
    print(len(rows), "domains;", h)


if __name__ == "__main__":
    sys.exit(main())
