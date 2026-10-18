"""Round-2 extraction check (deviation D2). `draw`: a fresh random sample of 272 papers (15%) from the papers extracted in
round 1 but not sampled there (seed 20261020), fixed before any v2 output exists; writes
data/validation/extraction_sample_round2.json. `sheet`: the focused sheet for the v2 output (papers with a candidate
signal, or a numeric ROR in the abstract); writes data/validation/extraction_focus_round2.txt."""
import json
import random
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
V = RUN / "data" / "validation"
RORNUM = re.compile(r"(ROR|reporting odds ratio)[^.;]{0,160}\d", re.I)


def draw():
    ex = {json.loads(l)["id"] for l in open(RUN / "data" / "extract" / "signals_raw.jsonl") if "out" in json.loads(l)}
    old = set(json.load(open(V / "extraction_sample.json")))
    pick = sorted(random.Random(20261020).sample(sorted(ex - old), 272))
    json.dump(pick, open(V / "extraction_sample_round2.json", "w"))
    print(len(pick), "papers")


def cand(o, s):
    return (s.get("measure") == "ROR" and s.get("estimate") is not None and s.get("ci_low") is not None and s.get("ci_high") is not None
            and s["ci_low"] > 1 and bool(o.get("window")) and s.get("database") == "FAERS" and s.get("comparison") != "interaction")


def sheet(sample="extraction_sample_round2.json", name="extraction_focus_round2.txt"):
    pick = json.load(open(V / sample))
    recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
    ex = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data" / "extract" / "signals_raw_v2.jsonl") if "out" in json.loads(l)}
    out, nf, nr, miss = [], 0, 0, []
    for pid in pick:
        if pid not in ex:
            miss.append(pid); continue
        ab = re.sub(r"<[^>]+>", " ", recs[pid].get("abstractText") or "")
        o = ex[pid]["out"]; sig = o.get("signals") or []
        if not any(cand(o, s) for s in sig) and not RORNUM.search(ab):
            nr += 1; continue
        nf += 1
        out.append(f"### {pid}\nABSTRACT: {ab}\nWINDOW: {o.get('window')}")
        for j, s in enumerate(sig):
            out.append(f"  {'CAND' if cand(o, s) else '    '} s{j}: {s.get('measure')} | {s.get('database')} | {s.get('comparison')} | "
                       f"{s.get('drug')} | {s.get('event')} [{s.get('level')}] | {s.get('estimate')} ({s.get('ci_low')}-{s.get('ci_high')})")
        out.append("")
    (V / name).write_text("\n".join(out))
    print(nf, "focus papers;", nr, "with nothing to verify;", len(miss), "not extracted:", miss)


if __name__ == "__main__":
    {"draw": draw, "sheet": sheet}[sys.argv[1]]()
