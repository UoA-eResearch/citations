"""Measure E (audit_plan.md): resolve every arXiv ID and DOI cited in plans, reports and leads.json.
arXiv via the export API (batches of 50); DOIs via the doi.org handle API. Writes paper/audit/E_refs.csv."""
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
LAB = REPO / "research-lab"
OUT = LAB / "paper" / "audit"
ARX = re.compile(r"(?<![\d./])(\d{4}\.\d{4,5})(?:v\d+)?(?![\d])")
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>\]\)`,;]+)")


def sources():
    files = [LAB / "leads.json"] + sorted(LAB.glob("runs/*/plan.md")) + sorted(LAB.glob("runs/*/report.md"))
    refs = []
    for f in files:
        t = f.read_text(errors="ignore")
        for m in DOI.finditer(t):
            refs.append(("doi", m.group(1).rstrip(".:"), f.relative_to(LAB).as_posix()))
        t2 = DOI.sub(" ", t)
        for m in ARX.finditer(t2):
            i = m.group(1)
            yy, mm = int(i[:2]), int(i[2:4])
            if 7 <= yy <= 26 and 1 <= mm <= 12:
                refs.append(("arxiv", i, f.relative_to(LAB).as_posix()))
    return pd.DataFrame(refs, columns=["kind", "id", "file"])


def check_arxiv(ids):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    ok = {}
    for k in range(0, len(ids), 50):
        for attempt in range(4):
            try:
                x = urllib.request.urlopen(f"https://export.arxiv.org/api/query?id_list={','.join(ids[k:k+50])}&max_results=50", timeout=60).read()
                break
            except Exception:  # noqa: BLE001
                time.sleep(10 * (attempt + 1))
        for e in ET.fromstring(x).findall("a:entry", ns):
            t = e.find("a:title", ns)
            if t is not None and t.text and t.text.strip() != "Error":
                ok[e.find("a:id", ns).text.rsplit("/", 1)[-1].split("v")[0]] = " ".join(t.text.split())
        time.sleep(3)
    return ok


def check_doi(d):
    for attempt in range(3):
        try:
            r = json.load(urllib.request.urlopen(f"https://doi.org/api/handles/{urllib.request.quote(d)}", timeout=30))
            return r.get("responseCode") == 1
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            time.sleep(5)
        except Exception:  # noqa: BLE001
            time.sleep(5)
    return None


def main():
    r = sources()
    ua = sorted(r[r.kind == "arxiv"].id.unique())
    ok = check_arxiv(ua)
    ud = sorted(r[r.kind == "doi"].id.unique())
    dok = {d: check_doi(d) for d in ud}
    r["resolves"] = [ (i in ok) if k == "arxiv" else dok.get(i) for k, i in zip(r.kind, r.id)]
    r["arxiv_title"] = r.id.map(ok)
    r.to_csv(OUT / "E_refs.csv", index=False)
    u = r.drop_duplicates(["kind", "id"])
    print(u.groupby("kind").resolves.agg(["size", "sum"]))
    print(u[u.resolves != True][["kind", "id", "file"]].to_string(index=False))  # noqa: E712


if __name__ == "__main__":
    main()
