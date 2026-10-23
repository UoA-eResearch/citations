"""print_evidence.py MODE [ids...]: print gold-record evidence WITHOUT labels (reviewer re-labelling aid).
MODE = blind40  -> 40 random scored records, seed 20261023 (labels not loaded)
MODE = ids      -> the records named on the command line
Evidence shown in full for the sample's own fields; descriptions/abstracts/sampling sentences are shown as the first
600 chars plus every sentence containing an INSDC country name, a coordinate or a sampling cue."""
import json, random, re, sys
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code")); import countries  # noqa
R = {x["record"]: x for x in (json.loads(l) for l in open(RUN / "data" / "gold" / "records.jsonl"))}
names = sorted((re.escape(v) for v in countries.VOCAB), key=len, reverse=True)
CUE = re.compile(r"\b(" + "|".join(names) + r")\b|\d+(\.\d+)?\s*°|\b(collected|sampled|sampling|isolated from|obtained|"
                 r"purchased|province|prefecture|county|district|village|farm|lake|river|forest|coast|island|field|site|"
                 r"located|region|hospital|market|wild|captured|caught|genebank|accession|strain|stock|laboratory|lab\b|"
                 r"cell line|cultivar|breed|herd|flock|aquaculture|hatchery)\b", re.I)
def cues(txt, head=600, maxs=10):
    txt = txt or ""
    sents = [s.strip() for s in re.split(r"(?<=[.;|])\s+", txt) if CUE.search(s)]
    out = txt[:head]
    extra = [s[:350] for s in sents if s not in out][:maxs]
    return out + (" ... CUES: " + " || ".join(extra) if extra else "")
def show(i):
    x = R[i]
    print(f"\n######## {i}  acc={x['accession']} split={x['split']} has_pub={x['has_pub']} class={x['country_class']} raw={x['country_raw']!r}")
    for f in ("organism", "package", "sample_title", "isolation_source", "lat_lon", "attributes", "comment"):
        if x.get(f): print(f"  {f}: {x[f]}")
    print(f"  bioproject {x['bioproject']}: {x['bioproject_title']}")
    if x.get("bioproject_description"): print(f"  description: {cues(x['bioproject_description'])}")
    for p in x["publications"]:
        print(f"  publication {p['pmid']}: {p['title']}")
        if p.get("abstract"): print(f"    abstract: {cues(p['abstract'], 400)}")
        if p.get("methods_sentences"): print(f"    sampling sentences: {cues(p['methods_sentences'], 300, 12)}")
mode = sys.argv[1]
if mode == "blind40":
    excluded = {"R400", "R426", "R497"}
    ids = sorted(set(R) - excluded)
    random.Random(20261023).shuffle(ids)
    ids = sorted(ids[:40])
    print("BLIND SAMPLE:", " ".join(ids))
else:
    ids = sys.argv[2:]
for i in ids: show(i)
