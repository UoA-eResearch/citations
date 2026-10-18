"""Reviewer check 3: generation. (i) items.jsonl reproduces from the committed generator (data/ is not in git);
(ii) per-chemical caps and balance; (iii) ATC2 grouping of counterfactuals; (iv) AU family-(a) negatives that are
listed in another PBS program (s100 etc.); (v) NZ / AU form vocabularies the key parser skips; (vi) question templates.
Run: venv/bin/python -I review/reviewer_checks/02_generation.py"""
import json, sys, glob, re, collections
from pathlib import Path
import xml.etree.ElementTree as ET
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import generate as G  # the code under review, used only to test that items.jsonl is its deterministic output
from names import norm

items = [json.loads(l) for l in open(RUN / "data/items.jsonl")]
by_id = {x["id"]: x for x in items}

print("== (i) does the committed generator reproduce data/items.jsonl? ==")
import io, contextlib, tempfile, shutil, os
# run G.main() with its outputs redirected to a temp copy of the run tree (RUN/data is read; writes go to tmp)
tmp = Path(tempfile.mkdtemp()); (tmp / "data").symlink_to(RUN / "data" / "raw", target_is_directory=True) if False else None
class _R:  # redirect writes by monkeypatching open targets
    pass
orig_open = open
written = {}
def fake_open(f, mode="r", *a, **k):
    f = str(f)
    if "w" in mode and (f.endswith("items.jsonl") or f.endswith("passages.jsonl") or f.endswith("generation_stats.json")):
        buf = io.StringIO(); written[Path(f).name] = buf
        class W(io.StringIO):
            def __exit__(self, *e): return False
            def close(self): pass
        w = W(); written[Path(f).name] = w; return w
    return orig_open(f, mode, *a, **k)
G.open = fake_open
with contextlib.redirect_stdout(io.StringIO()):
    G.main()
regen = [json.loads(l) for l in written["items.jsonl"].getvalue().splitlines()]
same = regen == items
print("regenerated items identical to data/items.jsonl:", same, f"({len(regen)} vs {len(items)})")
if not same:
    for a, b in zip(regen, items):
        if a != b: print("first diff:", a, b); break
pas = [json.loads(l) for l in open(RUN / "data/passages.jsonl")]
print("regenerated passages identical:", [json.loads(l) for l in written["passages.jsonl"].getvalue().splitlines()] == pas)
print("regenerated stats:", written["generation_stats.json"].getvalue().replace("\n", " ")[:300])

print("\n== (ii) caps and balance ==")
per_fam = collections.Counter((x["jurisdiction"], x["family"], x["chemical"]) for x in items)
per_fam_ans = collections.Counter((x["jurisdiction"], x["family"], x["chemical"], x["answer"]) for x in items)
print("max items per chemical per family:", max(per_fam.values()), " per family x answer:", max(per_fam_ans.values()))
print("chemicals with >3 items in a family:", sum(v > 3 for v in per_fam.values()), sorted([k for k, v in per_fam.items() if v > 3])[:12])
print("cells:", sorted(collections.Counter((x["jurisdiction"], x["family"], x["answer"]) for x in items).items()))
print("distinct chemicals per (jur, fam):", {k: len(v) for k, v in collections.defaultdict(set, {}).items()} or
      {k: len({x["chemical"] for x in items if (x["jurisdiction"], x["family"]) == k}) for k in sorted({(x["jurisdiction"], x["family"]) for x in items})})
dups = collections.Counter((x["jurisdiction"], x["family"], x["text"]) for x in items)
print("duplicate question texts within (jur, fam):", sum(v > 1 for v in dups.values()))
# chemicals present in both jurisdictions within family b (paired clusters)
for f in "abd":
    nzc = {x["chemical"] for x in items if x["family"] == f and x["jurisdiction"] == "NZ"}
    auc = {x["chemical"] for x in items if x["family"] == f and x["jurisdiction"] == "AU"}
    print(f"({f}) chemicals NZ={len(nzc)} AU={len(auc)} both={len(nzc & auc)} union={len(nzc | auc)}")

print("\n== (iii) ATC2 grouping of counterfactuals ==")
nz_new, nz_crit, atc2 = G.nz(RUN / "data/raw/nz/Schedule_2026-10.xml")
cfs = [x for x in items if x["family"] == "d" and x["answer"] == "no"]
print("CF items:", len(cfs), " with atc2 None:", sum(atc2.get(x["chemical"]) is None for x in cfs),
      " source in same ATC2:", sum(atc2.get(x["chemical"]) == atc2.get(x["source_chemical"]) for x in cfs))
print("ATC2 groups used (NZ CFs):", collections.Counter(atc2.get(x["chemical"]) for x in cfs if x["jurisdiction"] == "NZ").most_common())
print("ATC2 groups used (AU CFs):", collections.Counter(atc2.get(x["chemical"]) for x in cfs if x["jurisdiction"] == "AU").most_common())
print("distinct source chemicals NZ:", len({x['source_chemical'] for x in cfs if x['jurisdiction']=='NZ'}), " AU:", len({x['source_chemical'] for x in cfs if x['jurisdiction']=='AU'}))
# true criteria: how many distinct chemicals; share of NZ true criteria that are long/complex
trues = [x for x in items if x["family"] == "d" and x["answer"] == "yes"]
print("true-criterion chemicals NZ:", len({x['chemical'] for x in trues if x['jurisdiction']=='NZ'}), " AU:", len({x['chemical'] for x in trues if x['jurisdiction']=='AU'}))
print("median criterion length (chars) NZ true/cf:", sorted(len(x['text']) for x in trues if x['jurisdiction']=='NZ')[50], sorted(len(x['text']) for x in cfs if x['jurisdiction']=='NZ')[50],
      " AU true/cf:", sorted(len(x['text']) for x in trues if x['jurisdiction']=='AU')[50], sorted(len(x['text']) for x in cfs if x['jurisdiction']=='AU')[50])

print("\n== (iv) AU family-(a) negatives listed in another PBS program; NZ negatives in other NZ sections ==")
def load(code, ep):
    return [x for f in sorted(glob.glob(str(RUN / "data/raw/pbs" / f"{code}_{ep}_*.json"))) for x in json.load(open(f))["data"]]
au_all = load(4751, "items")
STRn = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|µg|microgram|micrograms|g)\b", re.I)
def mg_of(s):
    m = STRn.search(re.sub(r"(\d),(\d{3})\b", r"\1\2", s or ""))
    if not m: return None
    u = m.group(2).lower(); return round(float(m.group(1)) * (1000 if u == "g" else 0.001 if u.startswith("m") and u != "mg" or u == "µg" else 1), 6)
rows = []
for x in items:
    if x["jurisdiction"] == "AU" and x["family"] == "a" and x["answer"] == "no":
        chem, mg, fc = x["key"]
        hits = [r for r in au_all if norm(r.get("drug_name") or "") == chem and mg_of(r.get("li_form")) == mg and re.match(r"\s*(tab|cap|wafer)", (r.get("li_form") or "").lower())]
        progs = sorted({(r["program_code"], r["li_form"]) for r in hits})
        if progs: rows.append((x["id"], x["text"], progs))
print(f"AU (a) negatives with a same-strength tablet/capsule in ANY PBS program (incl. GE = key error): {len(rows)} of {sum(1 for x in items if x['jurisdiction']=='AU' and x['family']=='a' and x['answer']=='no')}")
for r in rows: print("  ", r)
# NZ: sections other than B in the XML
root = ET.parse(RUN / "data/raw/nz/Schedule_2026-10.xml").getroot()
print("NZ XML sections:", [s.get("ID") for s in root.findall(G.NS + "Section")])

print("\n== (v) form vocabularies the key parser skips ==")
sec = [s for s in root.findall(G.NS + "Section") if s.get("ID") == "B"][0]
first = collections.Counter()
for ch in sec.iter(G.NS + "Chemical"):
    if not G.single(ch.findtext(G.NS + "Name") or ""): continue
    for f in ch.findall(G.NS + "Formulation"):
        nm = f.findtext(G.NS + "Name") or ""
        if G.key_of("x", nm) is None and re.search(r"\b(tab|cap)", nm, re.I):
            first[re.sub(r"\d.*", "", nm).strip()] += 1
print("NZ single-ingredient formulations mentioning tab/cap that key_of() rejects, by prefix:", first.most_common(25))
au_first = collections.Counter()
for r in au_all:
    if r.get("program_code") != "GE" or not G.single(r.get("drug_name") or ""): continue
    lf = r.get("li_form") or ""
    if G.key_of("x", lf) is None and re.search(r"\b(tablet|capsule)", lf, re.I):
        au_first[(r["drug_name"], lf)] += 1
print("AU GE single-ingredient li_forms mentioning tablet/capsule that key_of() rejects:", len(au_first))
for k, v in sorted(au_first.items())[:40]: print("  ", k)

print("\n== (vi) question templates (from run.py) ==")
import run as R
for k in R.Q: print(k, "|", R.Q[k]); print("   para:", R.P[k])
# how many CF items' text mention another drug name present in the item universe (not the source or own chemical)?
allchem = {x["chemical"] for x in items}
leak = [(x["id"], x["text"][:90]) for x in cfs if any(c in x["text"].lower() for c in allchem if c not in (x["chemical"], x["source_chemical"]) and len(c) > 5)]
print("\nCF texts mentioning some other benchmark chemical by name:", len(leak)); [print("  ", l) for l in leak[:10]]
