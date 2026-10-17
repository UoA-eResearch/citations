"""(a) How much table/caption text leaks into 'result'-typed sentences in the v2 strict set (glued text such as
'Table 1Dataset' or 'groups.Association' marks a flattened <sec> containing table-wrap/fig children), and how long
the 'sentences' are. (b) Does the v2 middle-dot repair break middle-dot multiplication ('2·10-5')? (c) class
changes v1 -> v2 for the same pairs."""
import gzip, json, re, sys
from collections import Counter
from pathlib import Path
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
from analysis_v2 import strict, CROSS
import pandas as pd
pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data/aligned_v2/pairs.jsonl")])
v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
GLUE = re.compile(r"[a-z\)\]]\.[A-Z]|Table\s?\d+[A-Z]|Fig\.?\s?\d+[A-Z][a-z]|\bTable\b.*\bTable\b")
rows = [json.loads(l) for l in gzip.open(RUN / "data/aligned_v2/statistics.jsonl.gz", "rt")]
al = [r for r in rows if r["status"] == "aligned"]
st_ = [r for r in al if strict(r)]
sc = [r for r in st_ if r["pair"] in v1 and r["cls"] in CROSS]
def leak(x): return bool(GLUE.search(x["sentence"]))
print("strict eligible", len(st_), "strict v1 crossings", len(sc))
print("strict-eligible pairs with glued text on either side:", sum(leak(r["pre"]) or leak(r["pub"]) for r in st_), f"({sum(leak(r['pre']) or leak(r['pub']) for r in st_)/len(st_):.1%})")
print("strict v1 crossings with glued text on either side:", sum(leak(r["pre"]) or leak(r["pub"]) for r in sc))
L = [max(len(r["pre"]["sentence"]), len(r["pub"]["sentence"])) for r in sc]
print("strict v1 crossings: sentence length >600 chars:", sum(l > 600 for l in L), "; >1500:", sum(l > 1500 for l in L))
print("strict v1 crossings n_in_sent distribution:", Counter(r["pre"]["n_in_sent"] for r in sc))
print("strict v1 crossings by section pre/pub:", Counter((r["pre"]["section"], r["pub"]["section"]) for r in sc))
print("strict v1 crossings by how:", Counter(r["how"] for r in sc), " sim quantiles:", pd.Series([r["sim"] for r in sc]).quantile([0, .25, .5, .75, 1]).round(3).tolist())
# (b) middle-dot multiplication in v1 sentences
rows1 = [json.loads(l) for l in gzip.open(RUN / "data/aligned/statistics.jsonl.gz", "rt")]
MD = re.compile(r"\d\s*[·∙•]\s*10")
hits = [(r, x) for r in rows1 for side in ("pre", "pub") if (x := r.get(side)) and MD.search(x["sentence"]) and x["kind"] == "p"]
print("\n(b) v1 statistics whose sentence has 'digit·10':", len(hits))
for r, x in hits[:8]:
    m = MD.search(x["sentence"]); print("   ", repr(x["sentence"][max(0, m.start()-60):m.end()+25]), "| v1 p =", x["p"])
# what does v2 do with such a sentence?
import extract_v2 as X2, extract as X1
for s in ["Genome-wide hit (p = 1·2·10−8).", "Strong association (P = 2·10-5).", "No difference (p=0·76).", "p = 3·4 × 10−6"]:
    print("   ", repr(s), "v1:", [x["p"] for x in X1.extract(s)], "v2:", [x["p"] for x in X2.extract(s)])
# (c) v1 -> v2 class counts for v1 population
c1 = Counter(r["cls"] for r in rows1 if r["status"] == "aligned" and r["pair"] in v1)
c2 = Counter(r["cls"] for r in rows if r["status"] == "aligned" and r["pair"] in v1)
print("\n(c) v1-population class counts, v1 extraction:", dict(c1)); print("    v2 extraction:", dict(c2))
# (d) exact tuple matches with empty df among crossings, all versions, v1 extraction
ex = [r for r in rows1 if r["status"] == "aligned" and r["how"] == "exact"]
print("\n(d) exact tuple matches:", len(ex), " with empty df:", sum(r["pre"]["df"] == "" for r in ex), " by test:", Counter(r["pre"]["test"] for r in ex))
exc = [r for r in ex if r["cls"] in CROSS]
print("    exact crossings all versions:", len(exc), " with empty df:", sum(r["pre"]["df"] == "" for r in exc), [ (r["pre"]["test"], r["pre"]["df"], r["pre"]["stat"], r["pre"]["p"], r["pub"]["p"]) for r in exc])
