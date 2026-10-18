"""Benchmark items (plan sections 2-3; deviation D1). Reads data/raw/nz/Schedule_{2025-11,2026-10}.xml and the PBS API
pages for schedules 3834 (2025-11-01) and 4751 (2026-10-01). Writes data/items.jsonl (one yes/no item per line, with
its answer, family, jurisdiction, chemical and provenance) and data/passages.jsonl (one retrieval passage per chemical
and jurisdiction, from the 2026-10 edition)."""
import glob
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import norm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
NS = "{http://schedule.pharmac.govt.nz/2006/07/Schedule#}"
MML = "{http://www.w3.org/1998/Math/MathML}"
MR = re.compile(r"modified|controlled|sustained|extended|long[- ]acting|slow[- ]release|prolonged|\b(sr|cr|er|xr|mr|la)\b", re.I)
STR = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|µg|microgram|micrograms|g)\b", re.I)
SEED = 20261018


def ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def key_of(chem, form):
    """(chemical, strength, form class, modified-release) for a single-ingredient tablet or capsule, else None."""
    f = form.lower()
    fc = "tablet" if re.match(r"\s*(tab|tablet)", f) else "capsule" if re.match(r"\s*(cap|capsule)", f) else None
    if fc is None or re.search(r"\bwith\b|\+| and |containing", f):
        return None
    m = STR.search(form)
    if not m:
        return None
    unit = m.group(2).lower(); unit = "mcg" if unit in ("µg", "microgram", "micrograms") else unit
    val = float(m.group(1)); val = int(val) if val == int(val) else val
    return (chem, f"{val} {unit}", fc, bool(MR.search(form)))


def render(k):
    chem, strength, fc, mr = k
    return f"{chem} {strength} {fc}" + (" (modified release)" if mr else "")


def single(name):
    return not re.search(r"\+| with | and |/|,", name or "", re.I)


def nz(path):
    r = ET.parse(path).getroot()
    forms = defaultdict(list)
    for q in r.iter(NS + "Request"):
        forms[q.get("Form")] += [ws("".join(ci.itertext())) for ci in q.iter(MML + "ci") if ws("".join(ci.itertext()))]
    sec = [s for s in r.findall(NS + "Section") if s.get("ID") == "B"][0]
    items, crit, atc2 = {}, defaultdict(set), {}

    def special(rules):
        return [x for x in rules if x.get("Type") == "Special" and x.get("Attribute") == "Subsidy"]

    def walk(node, anc_rules, a2):
        for ch in node:
            tag = ch.tag.replace(NS, "")
            if tag in ("ATC1", "ATC2", "ATC3"):
                walk(ch, anc_rules + ch.findall(NS + "Rule"), ch.get("ID") if tag == "ATC2" else a2)
            elif tag == "Chemical":
                name = ch.findtext(NS + "Name") or ""
                if not single(name):
                    continue
                c = norm(name); atc2.setdefault(c, a2)
                crules = anc_rules + ch.findall(NS + "Rule")
                for f in ch.findall(NS + "Formulation"):
                    k = key_of(c, f.findtext(NS + "Name") or "")
                    frules = crules + f.findall(NS + "Rule")
                    sp = special(frules)
                    bsp = [bool(special(b.findall(NS + "Rule"))) for b in f.findall(NS + "Brand")]
                    sa = True if sp else (True if bsp and all(bsp) else ("mixed" if any(bsp) else False))
                    hrefs = {x.get("{http://www.w3.org/1999/xlink}href") for x in sp}
                    hrefs |= {x.get("{http://www.w3.org/1999/xlink}href") for b in f.findall(NS + "Brand") for x in special(b.findall(NS + "Rule"))}
                    for h in hrefs:
                        crit[c] |= set(forms.get(h, []))
                    if k:
                        prev = items.get(k)
                        items[k] = sa if prev is None or prev == sa else "mixed"
    walk(sec, sec.findall(NS + "Rule"), None)
    return items, crit, atc2


def pbs(code):
    def load(ep):
        out = []
        for f in sorted(glob.glob(str(RAW / "pbs" / f"{code}_{ep}_*.json"))):
            out += json.load(open(f))["data"]
        return out
    it = [x for x in load("items") if x.get("program_code") == "GE"]
    rel = load("item-restriction-relationships"); rpt = load("restriction-prescribing-text-relationships")
    pt = {x["prescribing_txt_id"]: x for x in load("prescribing-texts")}
    res_of = defaultdict(set)
    for x in rel:
        res_of[x["pbs_code"]].add(x["res_code"])
    pts_of = defaultdict(set)
    for x in rpt:
        pts_of[x["res_code"]].add(x["prescribing_text_id"])
    items, crit = {}, defaultdict(set)
    for x in it:
        name = x.get("drug_name") or ""
        if not single(name):
            continue
        c = norm(name)
        k = key_of(c, x.get("li_form") or "")
        auth = x.get("benefit_type_code") in ("A", "S")
        if k:
            prev = items.get(k)
            items[k] = auth if prev is None or prev == auth else "mixed"
        for rc in res_of.get(x["pbs_code"], ()):
            for pid in pts_of.get(rc, ()):
                p = pt.get(pid)
                if p and (p.get("prescribing_type") or "").upper() in ("CRITERIA", "INDICATION", "TREATMENT_CRITERIA", "CLINICAL_CRITERIA"):
                    t = re.sub(r"^[A-Za-z ]{0,40}criteria:\s*", "", ws(p.get("prescribing_txt")), flags=re.I)   # "Clinical criteria: ..."
                    if 15 <= len(t) <= 300:
                        crit[c].add(t)
    return items, crit


def nkey(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def main():
    nz_new, nz_crit, atc2 = nz(RAW / "nz" / "Schedule_2026-10.xml")
    nz_old, nz_crit_old, _ = nz(RAW / "nz" / "Schedule_2025-11.xml")
    au_new, au_crit = pbs(4751)
    au_old, au_crit_old = pbs(3834)
    J = {"NZ": (nz_new, nz_old, nz_crit, nz_crit_old), "AU": (au_new, au_old, au_crit, au_crit_old)}
    chems = {k[0] for k in nz_new} & {k[0] for k in au_new}
    stats = dict(nz_chems=len({k[0] for k in nz_new}), au_chems=len({k[0] for k in au_new}), matched=len(chems))
    rng = random.Random(SEED)
    items = []

    def take(pool, n, fam, jur, answer):
        rng.shuffle(pool); per = defaultdict(int); got = []
        for it in pool:
            if per[it["chemical"]] >= 3:
                continue
            per[it["chemical"]] += 1; got.append(it)
            if len(got) == n:
                break
        for it in got:
            it.update(family=fam, jurisdiction=jur, answer=answer)
        items.extend(got)
        return len(got)

    avail = {}
    for jur, (new, old, cr, cr_old) in J.items():
        other = J["AU" if jur == "NZ" else "NZ"][0]
        pos = [dict(key=k, chemical=k[0], text=render(k)) for k in new if k[0] in chems and k in old]
        neg = [dict(key=k, chemical=k[0], text=render(k)) for k in other if k[0] in chems and k not in new and k not in old]
        avail[f"{jur}_a"] = (take(pos, 150, "a", jur, "yes"), take(neg, 150, "a", jur, "no"))
        yes = [dict(key=k, chemical=k[0], text=render(k)) for k, v in new.items() if k[0] in chems and v is True and old.get(k) is True]
        no = [dict(key=k, chemical=k[0], text=render(k)) for k, v in new.items() if k[0] in chems and v is False and old.get(k) is False]
        avail[f"{jur}_b"] = (take(yes, 100, "b", jur, "yes"), take(no, 100, "b", jur, "no"))
        # (d): own criteria (stable in both editions) as controls; counterfactuals from another chemical in the same ATC2 group
        stable = {c: {t for t in cr[c] if 15 <= len(t) <= 300 and nkey(t) in {nkey(x) for x in cr_old.get(c, ())}} for c in chems if cr.get(c)}
        true = [dict(chemical=c, text=t) for c, ts in stable.items() for t in ts]
        by_grp = defaultdict(list)
        for c, ts in stable.items():
            by_grp[atc2.get(c)].extend((c, t) for t in ts)
        cf = []
        for c, ts in stable.items():
            own = {nkey(t) for t in cr[c] | cr_old.get(c, set())}
            for c2, t in by_grp[atc2.get(c)]:
                if c2 != c and nkey(t) not in own and c2 not in t.lower() and c not in t.lower():
                    cf.append(dict(chemical=c, text=t, source_chemical=c2))
        avail[f"{jur}_d"] = (take(true, 100, "d", jur, "yes"), take(cf, 100, "d", jur, "no"))
    for i, it in enumerate(items):
        it["id"] = f"{it['jurisdiction']}-{it['family']}-{i:04d}"
        if "key" in it:
            it["key"] = list(it["key"])
    with open(RUN / "data" / "items.jsonl", "w") as fh:
        for it in items:
            fh.write(json.dumps(it) + "\n")
    # retrieval passages: one per chemical and jurisdiction (2026-10 edition)
    with open(RUN / "data" / "passages.jsonl", "w") as fh:
        for jur, (new, old, cr, _) in J.items():
            label = "Special Authority required" if jur == "NZ" else "Authority required (incl. Streamlined)"
            doc = "New Zealand Pharmaceutical Schedule (community)" if jur == "NZ" else "Australian PBS General Schedule"
            by = defaultdict(list)
            for k, v in new.items():
                by[k[0]].append((k, v))
            for c in sorted(set(by) | set(cr)):
                lines = [f"{doc}. Chemical: {c}."]
                for k, v in sorted(by.get(c, []), key=lambda kv: str(kv[0])):
                    lines.append(f"Listed: {render(k)}; {label}: {'yes' if v is True else 'no' if v is False else 'varies by brand or pack'}.")
                if cr.get(c):
                    lines.append("Criteria: " + " | ".join(sorted(cr[c])))
                fh.write(json.dumps(dict(jurisdiction=jur, chemical=c, text=" ".join(lines))) + "\n")
    stats["available_taken"] = avail; stats["items"] = len(items)
    json.dump(stats, open(RUN / "results" / "tables" / "generation_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
