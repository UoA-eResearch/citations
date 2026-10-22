"""Reviewer check (network, polite): Crossref records for (a) 15 unmarked primary-cohort documents dated only by a
Crossref self-update (D4) and (b) the 8b documents labelled 'no'/'unclear' plus five labelled 'yes' that are
Crossref-only. Prints title, issued, update-to dates, updated-by entries, deposited date.
Run: venv/bin/python -I crossref_d4.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
MAILTO = "noreply@anthropic.com"


def get(doi):
    u = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}?mailto={MAILTO}"
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": f"review (mailto:{MAILTO})"}), timeout=60) as r:
                return json.loads(r.read())["message"]
        except Exception as e:
            err = repr(e)[:80]
            time.sleep(3)
    return {"error": err}


def dp(x):
    try:
        return "-".join(f"{v:02d}" if i else str(v) for i, v in enumerate(x["date-parts"][0]))
    except Exception:
        return "?"


def show(tag, doi):
    m = get(doi)
    if "error" in m:
        print(f"{tag} {doi}: {m['error']}")
        return
    title = (m.get("title") or ["?"])[0][:90]
    ut = [(u.get("type"), u.get("DOI"), dp(u.get("updated", {}))) for u in m.get("update-to", [])]
    ub = [(u.get("type"), u.get("DOI"), dp(u.get("updated", {})), (u.get("label") or "")[:20]) for u in m.get("updated-by", [])]
    print(f"{tag} {doi}\n    title: {title}\n    type {m.get('type')}; issued {dp(m.get('issued', {}))}; deposited "
          f"{(m.get('deposited') or {}).get('date-time', '?')[:10]}; indexed {(m.get('indexed') or {}).get('date-time', '?')[:10]}")
    print(f"    update-to: {ut}\n    updated-by: {ub}")
    rel = m.get("relation") or {}
    if rel:
        print(f"    relation: {[(k, [x.get('id') for x in v][:3]) for k, v in rel.items()]}")
    time.sleep(1.0)


def main():
    ov = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz")
    O = ov[(ov.stratum == "primary") & ov.in_snapshot & ov.date_source.str.startswith("crossref-self") & ~ov.own_marker]
    print("unmarked self-update-dated primary docs:", len(O), "; of them without flag:", int((~O.sidecar_flag.fillna(False).astype(bool)).sum()))
    smp = O.sample(15, random_state=11)
    print("\n=== (a) 15 unmarked self-update-dated documents")
    for r in smp.itertuples():
        show(f"[{r.pmcid} issue-date {r.date}]", r.doi)
    print("\n=== (b) 8b 'no'/'unclear' and five Crossref-only 'yes'")
    for tag, doi in [("B-011 no", "10.1016/j.vas.2017.04.002"), ("B-014 no", "10.1186/1556-276x-9-125"),
                     ("B-015 no", "10.1016/j.jbc.2022.102346"), ("B-017 unclear", "10.1016/j.aprim.2021.102276"),
                     ("B-030 no", "10.1016/j.vas.2019.100046"), ("B-033 no", "10.1016/j.ijpx.2023.100203"),
                     ("B-039 no", "10.1016/j.bjane.2017.04.002"), ("B-000 yes", "10.4103/0019-5049.65377"),
                     ("B-006 yes", "10.1186/1742-4690-9-s2-p362"), ("B-016 yes", "10.1016/j.mcn.2011.09.002"),
                     ("B-020 yes", "10.1016/j.ygeno.2019.09.001"), ("B-023 yes", "10.1186/s13660-017-1332-0")]:
        show(tag, doi)


if __name__ == "__main__":
    main()
