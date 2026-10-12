"""show_outputs.py <model> <item> <cond> [cls]  -> unique extracted statements for that key with class and counts."""
import json, sys, re
sys.path.insert(0, "code")
import classify as CL
model, item, cond = sys.argv[1], sys.argv[2], sys.argv[3]
want = sys.argv[4] if len(sys.argv) > 4 else None
key = f"{item}|{cond}"
fz = {json.loads(l)["item"]: json.loads(l) for l in open("results/catalogue/frozen.jsonl")}
r = fz[item]
D, C = (r["D_twin"], r["C_twin"]) if cond == "T" else (r["D"], r["C"])
print(f"=== {model} {key} ===\nN: {r['N_twin'] if cond=='T' else (r['paraphrase'] if cond=='P' else r['nl'])}\nD: {re.sub(r'\s+',' ',D.strip())}\nC: {re.sub(r'\s+',' ',C.strip())}\n")
cl = {json.loads(l)["uid"]: json.loads(l) for l in open(f"data/classified/{model}.jsonl")}
from collections import Counter
cnt = Counter(); idx2uid = {}
for l in open(f"data/classified/{model}_outputs.jsonl"):
    o = json.loads(l)
    if o["key"] != key: continue
    cnt[(o.get("uid"), o["idx"] == "g")] += 1; idx2uid[o["idx"]] = o.get("uid")
codes = {}
for l in open(f"data/samples/{model}.jsonl"):
    s = json.loads(l)
    if s["key"] != key: continue
    outs = [(str(i), o) for i, o in enumerate(s.get("outputs") or [])] + [("g", o) for o in (s.get("greedy") or [])]
    for idx, o in outs:
        u = idx2uid.get(idx)
        if u and u not in codes:
            codes[u] = CL.extract(o.get("text"))
for (uid, g), n in sorted(cnt.items(), key=lambda x: -x[1]):
    c = cl.get(uid, {})
    cls = "noelab" if not c.get("elab") else "copy" if c.get("copy") and not c.get("correct") else "correct" if c.get("correct") and not c.get("copy") else ("BOTH" if c.get("copy") else "other")
    if want and cls != want: continue
    code = codes.get(uid) or "<no statement>"
    try:
        op, b, cc = CL.L.parse(code); stmt = re.sub(r"\s+", " ", f"{' '.join(op)} || {b} : {cc}")
    except Exception: stmt = re.sub(r"\s+", " ", code)[:400]
    print(f"[{cls:7s}] x{n}{' (greedy)' if g else ''} to_D={c.get('to_D')} to_C={c.get('to_C')} s={c.get('s')}\n    {stmt[:700]}")
