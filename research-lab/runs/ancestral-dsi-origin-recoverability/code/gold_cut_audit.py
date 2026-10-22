"""cut_audit.py: pass-2 records whose compact.py lines carried a location cue past the display cut used in that batch."""
import re, subprocess, sys, csv
from pathlib import Path
sys.path.insert(0, "code"); import countries
BATCH = [(0, 24, 420), (25, 52, 380), (53, 80, 360), (81, 108, 340), (109, 136, 320), (137, 164, 320), (165, 192, 320),
         (193, 222, 300), (223, 252, 300), (253, 284, 290), (285, 316, 290), (317, 348, 290), (349, 382, 280), (383, 416, 280)]
names = sorted((re.escape(v) for v in countries.VOCAB if v not in ("Gambia",)), key=len, reverse=True)
CUE = re.compile(r"\b(" + "|".join(names) + r")\b|\d+\.\d+\s*°?\s*[NS]\b|\b(collected (from|at|in)|sampled (from|at|in)|located in)\b")
lab = {r["sheet_id"]: r["label"] for r in csv.DictReader(open("data/gold/pass2_labels.csv"))}
key = {r["sheet_id"]: r["record"] for r in csv.DictReader(open("data/gold/pass2_key.csv"))}
dis = {r["record"] for r in csv.DictReader(open("data/gold/pass3_key.csv"))}
n = 0
for a, b, cut in BATCH:
    out = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("compact.py")), "2", str(a), str(b)],
                         capture_output=True, text=True).stdout
    for blk in re.split(r"(?m)^## ", out)[1:]:
        sid = blk.splitlines()[0].strip()
        hid = [ln[cut:] for ln in blk.splitlines()[1:] if len(ln) > cut and CUE.search(ln[cut:])]
        if hid:
            n += 1
            m = CUE.search(hid[0])
            print(sid, "| p2:", lab[sid], "| in pass 3:", key[sid] in dis, "| cue:", m.group(0))
print(n, "records with a location cue past the cut")
