"""G6 attribution ledger (see METHODS.md): every literature claim and external data fact traced to a checkable source.

Ledger: RUN_DIR/results/attribution_ledger.csv, one row per claim, columns:
  id           A1, A2, ...
  claim        the claim in our own words (never a quotation; quotes go to RUN_DIR/data/attribution_quotes/, not git)
  used_in      where we rely on it: lead.gap, lead.lit_for, plan.md §1, report.md "What was asked", ...
  source_type  paper | preprint | dataset | registry | code | documentation | web
  source_id    DOI (10.x/...), OpenAlex W-id, arXiv id, URL, GBIF datasetKey, repo@commit
  locator      section / paragraph / table / figure / field / file:line where the evidence sits
  role         for papers: main finding | background | limitation | method (what the cited text is doing there)
  support      supports | conditional | refutes | not addressed | not found
  conditions   assumptions or scope that limit the claim (population, years, model organism, version, ...)
  checked_how  how the claim was checked (read section X; API query; file listing; ...)
  checked_at   NZ date-time of the check

    python3 -I tools/attribution.py init RUN_DIR        create an empty ledger with the header
    python3 -I tools/attribution.py check RUN_DIR       validate fields; resolve every DOI (doi.org) and OpenAlex /
                                                        arXiv id (public APIs, no key); flag claims marked refutes /
                                                        not addressed / not found that are still used as support
"""
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

COLS = ["id", "claim", "used_in", "source_type", "source_id", "locator", "role", "support", "conditions", "checked_how",
        "checked_at"]
SUPPORT = {"supports", "conditional", "refutes", "not addressed", "not found"}
TYPES = {"paper", "preprint", "dataset", "registry", "code", "documentation", "web"}


def init(run):
    p = Path(run) / "results" / "attribution_ledger.csv"
    if p.exists():
        raise SystemExit(f"{p} exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="") as f:
        csv.writer(f).writerow(COLS)
    print("created", p)


def resolve(sid):
    """True / False / None (not a resolvable id type)."""
    try:
        if re.match(r"^10\.\d{4,}/", sid):
            req = urllib.request.Request("https://doi.org/" + sid, method="HEAD")
            try:
                return urllib.request.urlopen(req, timeout=30).status < 400
            except urllib.error.HTTPError as e:
                return e.code in (403, 405, 429)                # publisher blocks HEAD/robots: the DOI resolved
        if re.match(r"^W\d+$", sid):
            urllib.request.urlopen(f"https://api.openalex.org/works/{sid}?select=id", timeout=30)
            return True
        m = re.match(r"^(arXiv:)?(\d{4}\.\d{4,5})(v\d+)?$", sid)
        if m:
            s = urllib.request.urlopen(f"http://export.arxiv.org/api/query?id_list={m.group(2)}", timeout=30).read().decode()
            return "<entry>" in s and "<title>Error</title>" not in s
        if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", sid):   # GBIF datasetKey
            json.load(urllib.request.urlopen(f"https://api.gbif.org/v1/dataset/{sid}", timeout=30))
            return True
    except Exception:
        return False
    return None


def check(run):
    p = Path(run) / "results" / "attribution_ledger.csv"
    rows = list(csv.DictReader(open(p)))
    problems = []
    for r in rows:
        rid = r.get("id", "?")
        for c in ("claim", "used_in", "source_type", "source_id", "locator", "support", "checked_how", "checked_at"):
            if not (r.get(c) or "").strip():
                problems.append((rid, f"missing {c}"))
        if r.get("source_type") and r["source_type"] not in TYPES:
            problems.append((rid, f"source_type {r['source_type']!r} not in {sorted(TYPES)}"))
        if r.get("support") and r["support"] not in SUPPORT:
            problems.append((rid, f"support {r['support']!r} not in {sorted(SUPPORT)}"))
        if r.get("source_type") in ("paper", "preprint") and not (r.get("role") or "").strip():
            problems.append((rid, "paper without role (main finding / background / limitation / method)"))
        if r.get("support") in ("refutes", "not addressed", "not found") and "lit_against" not in r.get("used_in", ""):
            problems.append((rid, f"support={r['support']} but used in {r.get('used_in')!r}: fix the text or the ledger"))
        if len(r.get("claim", "")) > 400 or '"' in r.get("claim", ""):
            problems.append((rid, "claim looks like a quotation; paraphrase it (quotes go to data/attribution_quotes/)"))
        sid = (r.get("source_id") or "").strip()
        ok = resolve(sid) if sid else None
        if ok is False:
            problems.append((rid, f"source_id {sid!r} does not resolve"))
    for rid, why in problems:
        print(f"{rid}: {why}")
    print("G6", "FAILED" if problems else "passed", f"({len(rows)} claims)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    {"init": init, "check": check}[sys.argv[1]](sys.argv[2])
