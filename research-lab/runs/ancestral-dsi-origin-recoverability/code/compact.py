"""compact.py PASS FROM TO: compact adjudication view of sheet records (reading aid; full text in the pass sheet)."""
import re, sys
sys.path.insert(0, "/mnt/citations/research-lab/runs/ancestral-dsi-origin-recoverability/code")
import countries
p, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
text = open(f"/mnt/citations/research-lab/runs/ancestral-dsi-origin-recoverability/data/gold/pass{p}.md").read()
recs = re.split(r"(?m)^## ", text)[1:]
names = sorted((re.escape(v) for v in countries.VOCAB), key=len, reverse=True)
CUE = re.compile(r"\b(collected|sampled|sampling|isolated from|obtained from|province|prefecture|region|district|"
                 r"county|state of|city|village|lake|river|sea|ocean|coast|bay|island|forest|mountain|plateau|farm|"
                 r"hospital|market|located in|latitude|longitude|national park|reserve|field site|wild|"
                 + "|".join(names) + r")\b|°", re.I)
for r in recs[a:b + 1]:
    lines = r.splitlines()
    print("## " + lines[0])
    for ln in lines[1:]:
        if not ln.strip():
            continue
        key = ln.strip().split(":", 1)[0].lstrip("- ")
        if key in ("organism", "package", "sample_title", "isolation_source", "lat_lon", "country_raw", "bioproject_title", "comment"):
            print(ln[:300])
        elif key == "attributes":
            print(ln[:500])
        elif key.startswith("publication"):
            print(ln[:220])
        else:   # bioproject_description, abstract, sampling sentences: only sentences with a location cue
            body = ln.split(":", 1)[1] if ":" in ln else ln
            sents = [s.strip() for s in re.split(r"(?<=[.;|])\s+", body) if CUE.search(s)]
            if sents:
                print(f"  [{key} cues] " + " … ".join(s[:300] for s in sents[:6]))
    print()
