"""Step 2c: Ministry of Foreign Affairs and Trade (MFAT) aid activities delivered by the University of Auckland.

MFAT publishes every New Zealand aid programme activity to the IATI Standard (reporting organisation NZ-1).
This step reads them through d-portal.org's public, read-only query service and keeps the activities where
  - a participating organisation is the University of Auckland, Auckland UniServices or Waipapa Taumata Rau
    (MFAT lists few university partners: about 46 of its ~3,000 activities name any), or
  - the title or description names the University of Auckland, UniServices or a UoA institute as the
    deliverer (for example the Public Policy Institute's short courses, or the Liggins Institute).
OpenAlex holds no usable MFAT award records (they have no titles or recipients), so this is the only route.

The amounts are the activity's total spend in NZD as MFAT reports it: for scholarships and short courses this
includes participants' costs, and for activities with several partners it is not UoA's share. MFAT replaces
every transaction receiver with "Pending Approval", so UoA's own share cannot be read from IATI.

Writes <WORK>/mfat_activities.jsonl (one activity per line).
"""

import datetime
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
DPORTAL = "https://d-portal.org/q.json"
UA = {"User-Agent": "uoa-cer-bph-landscape (+https://github.com/UoA-eResearch/citations)"}
ROLE = {"1": "funding", "2": "accountable", "3": "extending", "4": "implementing"}
STATUS = {"1": "pipeline", "2": "implementation", "3": "finalisation", "4": "closed", "5": "cancelled", "6": "suspended"}
UOA_ORG = "(xson::text ILIKE '%university of auckland%' OR xson::text ILIKE '%uniservices%' OR xson::text ILIKE '%waipapa taumata%')"
UOA_TEXT = re.compile(r"university of auckland|auckland uniservices|\buniservices\b|waipapa taumata rau|liggins institute|"
                      r"geothermal institute", re.I)


def q(sql):
    url = DPORTAL + "?" + urllib.parse.urlencode({"sql": sql})
    for i in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=240).read())["rows"]
        except Exception as e:  # d-portal is a small public service: back off and retry
            print(f"  d-portal retry {i + 1}: {e}")
            time.sleep(10 * (i + 1))
    raise SystemExit("d-portal query failed")


def narrative(x):
    return ((x.get("/narrative") or [{}])[0] or {}).get("", "")


def day(d):
    return (datetime.date(1970, 1, 1) + datetime.timedelta(days=int(d))).isoformat() if d not in (None, "", "0") else None


def main():
    listed = {}
    for r in q("SELECT aid, xson FROM xson WHERE aid LIKE 'NZ-1-%' "
               f"AND root='/iati-activities/iati-activity/participating-org' AND {UOA_ORG}"):
        listed.setdefault(r["aid"], []).append(f"{narrative(r['xson'])} ({ROLE.get(r['xson'].get('@role'), 'partner')})")
    named = {}
    for r in q("SELECT aid, title, description FROM act WHERE reporting_ref='NZ-1' AND (title ILIKE '%auckland%' OR "
               "title ILIKE '%liggins%' OR description ILIKE '%auckland%' OR description ILIKE '%uniservices%' OR "
               "description ILIKE '%liggins%' OR description ILIKE '%geothermal institute%')"):
        m = UOA_TEXT.search((r["title"] or "") + " " + (r["description"] or ""))
        if m and r["aid"] not in listed:
            named[r["aid"]] = m.group(0)
    aids = sorted(set(listed) | set(named))
    inl = ",".join("'" + a.replace("'", "''") + "'" for a in aids)
    acts = {r["aid"]: r for r in q("SELECT aid, title, description, status_code, day_start, day_end, commitment, spend "
                                   f"FROM act WHERE aid IN ({inl})")}
    cur = {r["aid"]: r["xson"].get("@default-currency") for r in
           q(f"SELECT aid, xson FROM xson WHERE aid IN ({inl}) AND root='/iati-activities/iati-activity'")}
    countries, partners = {}, {}
    for r in q(f"SELECT aid, xson FROM xson WHERE aid IN ({inl}) AND root='/iati-activities/iati-activity/recipient-country'"):
        countries.setdefault(r["aid"], []).append(r["xson"].get("@code"))
    for r in q(f"SELECT aid, xson FROM xson WHERE aid IN ({inl}) AND root='/iati-activities/iati-activity/participating-org'"):
        nm, role = narrative(r["xson"]), ROLE.get(r["xson"].get("@role"), "partner")
        if role == "implementing" and "Foreign Affairs" not in nm:
            partners.setdefault(r["aid"], []).append(nm)
    retrieved = datetime.date.today().isoformat()
    with open(WORK / "mfat_activities.jsonl", "w") as f:
        for a in aids:
            r = acts.get(a) or {}
            f.write(json.dumps(dict(
                aid=a, title=r.get("title"), description=r.get("description") or "",
                status=STATUS.get(str(r.get("status_code")), r.get("status_code")), start=day(r.get("day_start")),
                end=day(r.get("day_end")), spend=float(r.get("spend") or 0), commitment=float(r.get("commitment") or 0),
                currency=cur.get(a) or "NZD", countries=countries.get(a, []), partners=sorted(set(partners.get(a, []))),
                uoa="partner" if a in listed else "named", uoa_as=listed.get(a) or [named.get(a)],
                url=f"https://d-portal.org/ctrack.html#view=act&aid={urllib.parse.quote(a)}", retrieved=retrieved),
                ensure_ascii=False) + "\n")
    print(f"{len(aids)} MFAT activities: {len(listed)} list UoA as a partner, {len(named)} name UoA as the deliverer")


if __name__ == "__main__":
    main()
