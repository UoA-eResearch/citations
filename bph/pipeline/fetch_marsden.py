"""Step 2b: Marsden Fund awards 2018-2025 from Royal Society Te Apārangi's public round spreadsheets.

OpenAlex's Marsden records stop at the 2017 round, so each later round is read from the "announcement
supplement" workbook published on royalsociety.org.nz (project, contact investigator and institution,
panel, category, funding, abstract or summary, and the full team). Projects are kept when a University
of Auckland researcher is on the team: as lead (contact investigator's institution) or as a team member
on a project led elsewhere.

Writes <WORK>/marsden_awards.jsonl. Workbooks are cached in <WORK>/marsden/.
"""

import json
import os
import re
import time
from pathlib import Path

import openpyxl
import requests

WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))
BASE = "https://www.royalsociety.org.nz"
ROUNDS = {
    2018: "/assets/Uploads/Marsden-2018-annoucement-supplement.xlsx",
    2019: "/assets/2019-Marsden-Fund-awarded-supplement_with-websheet-v2.xlsx",
    2020: "/assets/2020-Marsden-Fund-announcement-supplement_corrected.xlsx",
    2021: "/assets/2021-Marsden-Fund-announcement-supplement-with-websheet-v3.xlsx",
    2022: "/assets/2022_Marsden_Fund_announcement_supplement-v14.xlsx",
    2023: "/assets/2023_Marsden_Announcements_New.xlsx",
    2024: "/assets/2024-Marsden-Fund-announcement-supplement_v10.xlsx",
    2025: "/assets/2025-Marsden-Fund-announcement-supplement_updated_v4.xlsx",
}
ROUND_PAGE = BASE + "/what-we-do/funds-and-opportunities/marsden/awarded-grants/marsden-fund-awards-{y}"
UOA = re.compile(r"^(?:the )?university of auckland$", re.I)


def fetch(year, path):
    f = WORK / "marsden" / path.rsplit("/", 1)[-1]
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(BASE + path, headers={"User-Agent": "bph-pacific-landscape"}, timeout=120)
        r.raise_for_status()
        f.write_bytes(r.content)
        time.sleep(1)
    return f


def header_map(row):
    h = {}
    for i, c in enumerate(row):
        k = re.sub(r"\s+", " ", str(c or "")).strip().lower()
        if k and k not in h:
            h[k] = i
    return h


def pick(h, *names):
    for n in names:
        if n in h:
            return h[n]
    return None


def is_uoa(org):
    return bool(UOA.match(re.sub(r"\s+", " ", str(org or "")).strip()))


def parse(year, f):
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    projects, teams = {}, {}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        h = header_map(rows[0])
        name = ws.title.lower()
        if "project id" not in h:
            continue
        has_abs = any(k in h for k in ("abstract", "project abstract", "summary", "media summary"))
        if has_abs and "team" not in name:
            ci = dict(id=h["project id"], title=pick(h, "project title", "title", "project"),
                      media=pick(h, "media title"), contact=pick(h, "contact investigator", "investigator"),
                      org=pick(h, "institution", "organisation"), panel=pick(h, "panel"),
                      cat=pick(h, "category", "catergory"), amt=pick(h, "funding (ex gst)", "funding (exc gst)", "funding (gst excl)"),
                      abs=pick(h, "project abstract", "abstract", "summary"), msum=pick(h, "media summary"))
            for r in rows[1:]:
                pid = str(r[ci["id"]] or "").strip()
                if not re.match(r"^\d\d-[A-Z]{3}-\d+", pid):
                    continue
                g = lambda k: (str(r[ci[k]]).strip() if ci[k] is not None and r[ci[k]] is not None else "")
                amt = g("amt").replace("$", "").replace(",", "").strip()
                projects[pid] = dict(pid=pid, year=year, title=g("title") or g("media"), media_title=g("media"),
                                     contact=g("contact"), org=g("org"), panel=g("panel"), category=g("cat"),
                                     amount=float(amt) if re.match(r"^\d+(\.\d+)?$", amt) else None,
                                     abstract=g("abs"), media_summary=g("msum"))
        elif "team" in name or ("role" in h and "investigator" in h and not has_abs):
            ii, ri, oi = h.get("investigator"), h.get("role"), pick(h, "institution", "organisation")
            if ii is None or oi is None:
                continue
            cur = None
            for r in rows[1:]:
                pid = str(r[h["project id"]] or "").strip()
                if not pid and "proposal" in h:
                    pid = str(r[h["proposal"]] or "").strip()
                if re.match(r"^\d\d-[A-Z]{3}-\d+", pid):
                    cur = pid
                if cur and r[ii]:
                    teams.setdefault(cur, []).append(dict(name=str(r[ii]).strip(), role=str(r[ri] or "").strip(),
                                                          org=str(r[oi] or "").strip()))
    out = []
    for pid, p in projects.items():
        team, seen = [], set()     # some workbooks repeat the team table on a second sheet
        for m in teams.get(pid, []):
            key = (m["name"], m["role"], m["org"])
            if key not in seen:
                seen.add(key)
                team.append(m)
        lead = is_uoa(p["org"]) or "-UOA-" in pid
        uoa_team = [m for m in team if is_uoa(m["org"])]
        if not lead and not uoa_team:
            continue
        out.append(dict(p, team=team, uoa_members=[m["name"] for m in uoa_team], role="lead" if lead else "team",
                        url=ROUND_PAGE.format(y=year)))
    return out, len(projects)


def main():
    rows = []
    for y, path in ROUNDS.items():
        got, n = parse(y, fetch(y, path))
        print(f"  {y}: {n} projects in the round, {len(got)} with UoA ({sum(r['role'] == 'lead' for r in got)} UoA-led)")
        rows += got
    with open(WORK / "marsden_awards.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} Marsden projects with UoA researchers, 2018-2025")


if __name__ == "__main__":
    main()
