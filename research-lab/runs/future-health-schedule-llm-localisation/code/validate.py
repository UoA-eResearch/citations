"""Answer-key validation sheet (plan section 5; deviation D3). 100 random items per jurisdiction (seed 20261019).
Evidence is drawn from sources the generator did not parse:
  NZ: the October 2026 Schedule PDF text (pdftotext -layout): the chemical's block(s) and, for criteria items, whether
      the criterion text appears in the PDF near the chemical.
  AU: the raw PBS API JSON records for schedule 4751 read directly: every GE item whose drug name contains the chemical
      (form and benefit type), and the full restriction texts of those items (HTML stripped).
Writes data/validation/sheet.txt and data/validation/sample.json. Hand adjudication goes to
results/tables/key_validation.csv."""
import glob
import html
import json
import random
import re
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
V = RUN / "data" / "validation"


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def nkey(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def main():
    V.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(RUN / "data" / "items.jsonl")]
    rng = random.Random(20261019)
    pick = []
    for j in ("NZ", "AU"):
        pick += rng.sample([i for i in items if i["jurisdiction"] == j], 100)
    json.dump([i["id"] for i in pick], open(V / "sample.json", "w"))
    pdf = open(RUN / "data" / "raw" / "nz" / "Schedule_2026-10.txt").read().split("\n")
    pdfn = nkey(" ".join(pdf))
    load = lambda ep: [x for f in sorted(glob.glob(str(RUN / "data" / "raw" / "pbs" / f"4751_{ep}_*.json"))) for x in json.load(open(f))["data"]]
    au = [x for x in load("items") if x.get("program_code") == "GE"]
    rel = load("item-restriction-relationships"); res = {x["res_code"]: x for x in load("restrictions")}
    res_of = {}
    for x in rel:
        res_of.setdefault(x["pbs_code"], set()).add(x["res_code"])
    out = []
    for it in pick:
        c = it["chemical"]
        out.append(f"### {it['id']} | {it['jurisdiction']} family {it['family']} | answer {it['answer']}\nQ: {c} | {it['text']}")
        if it["jurisdiction"] == "NZ":
            hits = [k for k, l in enumerate(pdf) if re.match(rf"\s*{re.escape(c.upper())}\b", l)]
            for k in hits[:2]:
                out.append("  PDF> " + "\n  PDF> ".join(l.rstrip() for l in pdf[k:k + 14] if l.strip()))
            if not hits:
                out.append("  PDF> (no chemical heading found)")
            if it["family"] == "d":
                out.append(f"  criterion text in PDF anywhere: {nkey(it['text'])[:120] in pdfn}")
        else:
            rows = [x for x in au if c in (x.get("drug_name") or "").lower()]
            seen = set()
            for x in rows:
                k = (x["li_form"], x["benefit_type_code"])
                if k not in seen:
                    seen.add(k); out.append(f"  PBS> {x['drug_name']} | {x['li_form']} | benefit {x['benefit_type_code']} | {x['pbs_code']}")
            if it["family"] == "d":
                rtexts = {strip(res[r].get("li_html_text") or res[r].get("schedule_html_text")) for x in rows for r in res_of.get(x["pbs_code"], ()) if r in res}
                found = any(nkey(it["text"])[:120] in nkey(t) for t in rtexts)
                out.append(f"  criterion text in this drug's restriction texts: {found} ({len(rtexts)} restriction texts)")
        out.append("")
    (V / "sheet.txt").write_text("\n".join(out))
    print(len(pick), "items in the sheet")


if __name__ == "__main__":
    main()
