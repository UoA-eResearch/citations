"""Reviewer check 1: a fresh stratified sample (8 per jurisdiction x family x answer = 96 items; seed 20261021) of
items in NEITHER validation sample, with fuller evidence than the agent's sheets: NZ - the chemical's PDF block(s) and
the referenced SA block(s); AU - every PBS item for the drug in ANY program (form, benefit type, program) and, for (d),
all restriction texts of its GE items."""
import json, random, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rc_common as C
items = C.items()
V = C.RUN / "data/validation"
seen_q = {tuple(x) for x in json.load(open(V / "round1_questions.json"))}
seen_id = set(json.load(open(V / "sample_round2.json"))) | set(json.load(open(V / "sample.json")))
pool = [i for i in items if i["id"] not in seen_id and (i["jurisdiction"], i["family"], i["chemical"], i["text"]) not in seen_q]
print("eligible pool:", len(pool), "of", len(items))
rng = random.Random(20261021); pick = []
for j in ("NZ", "AU"):
    for f in "abd":
        for a in ("yes", "no"):
            cell = [i for i in pool if (i["jurisdiction"], i["family"], i["answer"]) == (j, f, a)]
            pick += rng.sample(cell, min(8, len(cell)))
json.dump([i["id"] for i in pick], open(C.RUN / "review/reviewer_checks/key_sample_ids.json", "w"))
out = []
for it in pick:
    c = it["chemical"]
    out.append(f"### {it['id']} | {it['jurisdiction']} family {it['family']} | KEY answer: {it['answer']}")
    out.append(f"Q: {c} | {it['text']}" + (f" | source chemical: {it['source_chemical']}" if "source_chemical" in it else ""))
    if it["jurisdiction"] == "NZ":
        blocks = C.nz_pdf_chem_blocks(c, maxlines=30 if it["family"] != "d" else 12)
        out.append(f"  PDF blocks found: {len(blocks)}")
        for b in blocks[:3]: out.append("  PDF> " + b.replace("\n", "\n  PDF> "))
        if it["family"] == "d":
            codes = set(re.findall(r"SA\d{3,4}", "\n".join(blocks)))
            for code in sorted(codes)[:3]:
                for sb in C.nz_pdf_sa_block(code)[:1]:
                    out.append(f"  SA-BLOCK {code}> " + sb.replace("\n", f"\n  SA-BLOCK {code}> "))
            if not codes: out.append("  (no SA code in heading; XML forms: %s)" % sorted(C.nz_sa_codes(c)))
    else:
        rows = C.au_items(c)
        seen = set()
        for x in sorted(rows, key=lambda r: (r["program_code"], r["li_form"])):
            k = (x["program_code"], x["li_form"], x["benefit_type_code"])
            if k not in seen:
                seen.add(k); out.append(f"  PBS> prog {x['program_code']} | {x['drug_name']} | {x['li_form']} | benefit {x['benefit_type_code']} | {x['pbs_code']}")
        if not rows: out.append("  PBS> (no item with this normalised drug name in schedule 4751)")
        if it["family"] == "d":
            rts = C.au_restriction_texts(c)
            hit = any(C.nkey(it["text"])[:120] in C.nkey(t) for t in rts.values())
            out.append(f"  verbatim criterion in GE restriction texts: {hit} ({len(rts)} texts)")
            for rc, t in rts.items(): out.append(f"  RES> {t[:1200]}")
    out.append("")
p = C.RUN / "review/reviewer_checks/sheets/key_sample.txt"; p.parent.mkdir(exist_ok=True); p.write_text("\n".join(out))
print(len(pick), "items ->", p, sum(len(l) for l in out), "chars")
import collections; print(collections.Counter((i["jurisdiction"], i["family"], i["answer"]) for i in pick))
