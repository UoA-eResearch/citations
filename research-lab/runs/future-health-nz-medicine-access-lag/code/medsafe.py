"""Query Medsafe's Product and Application searches for every cohort substance (plan section 4), in a headless browser
(the search is a Blazor server app; results arrive over its interactive circuit, so a plain HTTP client gets the form
back). The page is polled until its "N records" line appears. One query at a time, ~1.5 s apart; resumable. If a multi-word name returns nothing, the longest word is tried.
Saves data/raw/medsafe/html/<type>/<slug>.html.gz and data/raw/medsafe/log.jsonl."""
import asyncio
import gzip
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/mnt/research-lab-tools/ms-playwright")
from playwright.async_api import async_playwright  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "raw" / "medsafe" / "html"
LOG = RUN / "data" / "raw" / "medsafe" / "log.jsonl"
UA = "research-lab medicines-access study (mailto:noreply@anthropic.com)"
TERM = {"concentrate of proteolytic enzymes enriched in bromelain": "bromelain"}   # D5


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


async def search(pg, st, term):
    await pg.goto("https://www.medsafe.govt.nz/DbSearch/", wait_until="networkidle")
    await pg.check(f"#opt{st}")
    await pg.fill("#txtIngredient", term)
    await pg.press("#txtIngredient", "Enter")
    await pg.wait_for_url(re.compile(r"qry=" + st), timeout=30000)
    # results stream in over the circuit: poll until the "N records" line (or a product link) appears, up to 60 s
    for _ in range(120):
        await pg.wait_for_timeout(500)
        html = await pg.content()
        n = len(re.findall(r"ProductDetail\?Product_id=", html))
        m = re.search(r"\b(\d+)\s+records?\b", re.sub(r"<[^>]+>", " ", html))
        if n or m:
            return html, n, int(m.group(1)) if m else None
    raise TimeoutError("no result count")


async def main():
    cohort = pd.read_csv(RUN / "data" / "cohort.csv").substance.tolist()
    done = {(json.loads(l)["substance"], json.loads(l)["type"]) for l in open(LOG)} if LOG.exists() else set()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(user_agent=UA)
        with open(LOG, "a") as log:
            for k, s in enumerate(cohort):
                for st in ("Product", "Application"):
                    if (s, st) in done:
                        continue
                    terms = [TERM.get(s, s)] + ([max(s.split(), key=len)] if (" " in s and s not in TERM) else [])
                    rec = dict(substance=s, type=st)
                    for term in terms:
                        for attempt in range(3):
                            try:
                                html, n, nrec = await search(pg, st, term)
                                rec["n_records"] = nrec
                                break
                            except Exception as e:
                                html, n = None, -1; rec["error"] = str(e)[:120]
                                pg = await b.new_page(user_agent=UA)
                                await asyncio.sleep(10 * (attempt + 1))
                        if html is not None:
                            f = OUT / st / f"{slug(s)}.html.gz"
                            f.parent.mkdir(parents=True, exist_ok=True)
                            f.write_bytes(gzip.compress(html.encode()))
                        rec.update(term=term, n_links=n)
                        if n > 0:
                            break
                    log.write(json.dumps(rec) + "\n"); log.flush()
                    await asyncio.sleep(1.5)
                if k % 50 == 0:
                    print("medsafe", k, "/", len(cohort), flush=True)
        await b.close()
    print("medsafe done", flush=True)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
