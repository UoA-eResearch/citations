"""Reviewer misc checks: (A) generator determinism; (B) duplicate texts; (C) own-passage length for AU (b) misses;
(F) job index where NZ-d output starts; (G) NZ 'Tab'/'Cap' rejections; (I) generic boilerplate among TRUE criteria."""
import json, re, subprocess, sys, collections
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code")); import generate as G
items = [json.loads(l) for l in open(RUN / "data/items.jsonl")]

print("== (A) determinism: regenerate in two fresh interpreters (random hash seeds) and under PYTHONHASHSEED=0/1 ==")
code = r'''
import sys, io, json, contextlib; sys.path.insert(0, sys.argv[1]); import generate as G
written={}; orig=open
def fo(f, mode="r", *a, **k):
    f=str(f)
    if "w" in mode and (f.endswith("items.jsonl") or f.endswith("passages.jsonl") or f.endswith("generation_stats.json")):
        class W(io.StringIO):
            def close(self): pass
        w=W(); written[f.split("/")[-1]]=w; return w
    return orig(f, mode, *a, **k)
G.open=fo
with contextlib.redirect_stdout(io.StringIO()): G.main()
sys.stdout.write(written["items.jsonl"].getvalue())
'''
outs = {}
for tag, env in (("rand1", {}), ("rand2", {}), ("hs0", {"PYTHONHASHSEED": "0"}), ("hs1", {"PYTHONHASHSEED": "1"})):
    import os; e = {**os.environ, **env}
    r = subprocess.run([str(RUN / "venv/bin/python"), "-c", code, str(RUN / "code")], capture_output=True, text=True, env=e, timeout=600)
    outs[tag] = [json.loads(l) for l in r.stdout.splitlines()]
    nd = sum(a != b for a, b in zip(outs[tag], items)); fams = collections.Counter(b["family"] for a, b in zip(outs[tag], items) if a != b)
    print(f"{tag}: {len(outs[tag])} items; differ from data/items.jsonl in {nd} positions; by family {dict(fams)}")
print("rand1 vs rand2 differ in", sum(a != b for a, b in zip(outs["rand1"], outs["rand2"])), "positions")
print("families a,b identical to file in all runs:", all(all(a == b for a, b in zip(o, items) if b["family"] in "ab") for o in outs.values()))

print("\n== (B) duplicates ==")
c1 = collections.Counter((x["jurisdiction"], x["family"], x["text"]) for x in items)
c2 = collections.Counter((x["jurisdiction"], x["family"], x["chemical"], x["text"]) for x in items)
print("dup (jur,fam,text):", sum(v > 1 for v in c1.values()), " by family:", collections.Counter(k[1] for k, v in c1.items() if v > 1))
print("dup (jur,fam,chemical,text):", sum(v > 1 for v in c2.values()))
ex = [k for k, v in c1.items() if v > 1][:3]
for k in ex: print("  e.g.", k[0], k[1], k[2][:80], "-> chemicals:", [x["chemical"] for x in items if (x["jurisdiction"], x["family"], x["text"]) == k])

print("\n== (C) own-passage token length: AU (b) misses vs hits ==")
tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
pas = {(p["jurisdiction"], p["chemical"]): len(tok(p["text"])) for p in map(json.loads, open(RUN / "data/passages.jsonl"))}
rr = pd.read_csv(RUN / "review/reviewer_checks/retrieval_ranks.csv")
rr["own_len"] = [pas.get((j, c)) for j, c in zip(rr.jur, rr.chemical)]
for (j, f), x in rr[rr.fam.isin(["b", "d"])].groupby(["jur", "fam"]):
    hit = x[x.own_rank > 0].own_len; miss = x[x.own_rank == 0].own_len
    print(f"{j} ({f}): own passage retrieved: n={len(hit)} median len={hit.median():.0f}; NOT retrieved: n={len(miss)} median len={miss.median() if len(miss) else float('nan'):.0f}")
b = rr[(rr.fam == "b")]
print("AU (b) yes items: own passage hit rate", (b[(b.jur=='AU')&(b.truth=='yes')].own_rank>0).mean().round(3), " no items:", (b[(b.jur=='AU')&(b.truth=='no')].own_rank>0).mean().round(3))
print("NZ (b) yes items: own passage hit rate", (b[(b.jur=='NZ')&(b.truth=='yes')].own_rank>0).mean().round(3), " no items:", (b[(b.jur=='NZ')&(b.truth=='no')].own_rank>0).mean().round(3))
print("median own-passage length NZ (b) yes:", b[(b.jur=='NZ')&(b.truth=='yes')].own_len.median(), " AU (b) yes:", b[(b.jur=='AU')&(b.truth=='yes')].own_len.median())
d = rr[rr.fam == "d"]
for j in ("NZ", "AU"):
    for t in ("yes", "no"):
        x = d[(d.jur == j) & (d.truth == t)]
        print(f"{j} (d) truth={t}: own passage in top3 {(x.own_rank>0).mean():.2f}")

print("\n== (F) job order: index at which NZ-d zero-shot calls begin ==")
import random
para = set(x["id"] for x in random.Random(20261018).sample(items, 100))
k = 0; first_nzd = None
for it in items:
    if it["family"] == "d" and it["jurisdiction"] == "NZ" and first_nzd is None: first_nzd = k
    k += 3 + (1 if it["id"] in para else 0)
print(f"NZ-d zero-shot calls start at job {first_nzd} of {k} ({first_nzd/k:.1%}); run 17:56:52-19:20:39 = 83.8 min -> uniform-rate ETA {17*60+56.9 + 83.8*first_nzd/k:.1f} min = {int((17*60+56.9 + 83.8*first_nzd/k)//60)}:{int((17*60+56.9 + 83.8*first_nzd/k)%60):02d}; screen saved 18:13:48")
# which run.log progress line would have been reached when the screen was saved? unknown (no timestamps). Count lines written before NZ-d:
print("runs.jsonl lines are written in job order (ex.map); the screen could only have been influenced by NZ-d output if >", first_nzd, "jobs had completed by 18:13:48 (17 min in).")

print("\n== (G) NZ single-ingredient 'Tab'/'Cap' formulations rejected by key_of ==")
import xml.etree.ElementTree as ET
root = ET.parse(RUN / "data/raw/nz/Schedule_2026-10.xml").getroot()
sec = [s for s in root.findall(G.NS + "Section") if s.get("ID") == "B"][0]
for ch in sec.iter(G.NS + "Chemical"):
    nm = ch.findtext(G.NS + "Name") or ""
    if not G.single(nm): continue
    for f in ch.findall(G.NS + "Formulation"):
        fn = f.findtext(G.NS + "Name") or ""
        if G.key_of("x", fn) is None and re.search(r"\b(tab|cap)", fn, re.I): print("  ", nm, "|", fn)

print("\n== (I) generic/boilerplate language among TRUE-criterion controls (the GENERIC bar is applied only to counterfactuals) ==")
for j in ("NZ", "AU"):
    tr = [x for x in items if x["family"] == "d" and x["answer"] == "yes" and x["jurisdiction"] == j]
    g = [x for x in tr if G.GENERIC.search(x["text"])]
    print(f"{j}: {len(g)}/{len(tr)} true criteria match GENERIC; e.g.:", [x["text"][:70] for x in g[:4]])
rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data/runs.jsonl")])
z = rn[rn.condition == "zero"].set_index("id").answer
for j in ("NZ", "AU"):
    tr = [x for x in items if x["family"] == "d" and x["answer"] == "yes" and x["jurisdiction"] == j]
    g = [x["id"] for x in tr if G.GENERIC.search(x["text"])]; ng = [x["id"] for x in tr if not G.GENERIC.search(x["text"])]
    print(f"{j}: zero-shot affirm rate, generic true criteria {(z[g]=='yes').mean():.2f} (n={len(g)}) vs specific true criteria {(z[ng]=='yes').mean():.2f} (n={len(ng)})")
