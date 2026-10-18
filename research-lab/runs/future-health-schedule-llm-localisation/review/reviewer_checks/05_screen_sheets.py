"""Reviewer check 2 (and 1b): blind screening sheets for ALL 100 NZ and ALL 100 AU counterfactual items. Each entry
shows the counterfactual sentence, its source chemical, and the target chemical's OWN criteria read independently
(NZ: XML Special Authority forms for both editions, plus the PDF's SA block; AU: the full restriction texts of the
drug's GE items). The agent's labels are not loaded here."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rc_common as C
items = C.items()
out_dir = C.RUN / "review/reviewer_checks/sheets"; out_dir.mkdir(exist_ok=True)
for jur in ("NZ", "AU"):
    cfs = [x for x in items if x["family"] == "d" and x["answer"] == "no" and x["jurisdiction"] == jur]
    out = []
    for x in cfs:
        out.append(f"### {x['id']} | target: {x['chemical']} | source: {x['source_chemical']}")
        out.append(f"CF: {x['text']}")
        if jur == "NZ":
            own = sorted(C.nz_own_criteria(x["chemical"]))
            out.append(f"OWN (XML SA forms {sorted(C.nz_sa_codes(x['chemical']))}, {len(own)} criteria):")
            out += [f"  - {t}" for t in own]
        else:
            rts = C.au_restriction_texts(x["chemical"])
            out.append(f"OWN ({len(rts)} GE restriction texts):")
            for rc, t in rts.items(): out.append(f"  - {t[:1500]}")
        out.append("")
    (out_dir / f"screen_{jur}.txt").write_text("\n".join(out))
    print(jur, len(cfs), "items ->", out_dir / f"screen_{jur}.txt", sum(len(l) for l in out), "chars")
