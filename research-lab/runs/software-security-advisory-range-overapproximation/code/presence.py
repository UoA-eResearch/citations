"""Signatures and presence (plan sections 2-3). -> data/presence/<id>.json per advisory

For each sampled advisory: parse the fix diff into per-file signatures; list the releases inside the declared range
[earliest introduced, first fixed after it) in publish order; download and normalise each release in turn and record
signature presence, stopping at the first present release (the classification needs nothing later). The first
release at or after `fixed` is also checked (secondary 3). Downloads are processed in memory and discarded.
A per-advisory cap of 400 downloads marks the rest undetermined (cap).

  presence.py test        unit checks on diff parsing and normalisation
  presence.py run [N]     all sampled advisories (8 threads)
"""
import io
import json
import re
import sys
import tarfile
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
UA = "research-lab advisory-range study (open-data research; github.com/UoA-eResearch/citations)"
EXT = {"npm": (".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx"), "PyPI": (".py",)}
EXCL = ("test", "spec", "example", "doc", "dist/", ".min.")
KEYWORD_ONLY = re.compile(r"^(?:[{}()\[\];,]|else|try|finally|except|pass|break|continue|return|end|default|do)*$")
IMPORT = re.compile(r"^(?:import\b|from\b.+\bimport\b|export\b.*\bfrom\b|(?:const|let|var)\b.*=require\(|require\()")
CAP, PRESENT, ABSENT = 400, 0.8, 0.2


def norm(line, eco):
    s = line
    if eco == "npm":
        s = re.sub(r"/\*.*?\*/", "", s)
        s = re.sub(r"(^|[^:\\])//.*$", r"\1", s)
    else:
        s = re.sub(r"(^|\s)#.*$", r"\1", s)
    s = re.sub(r"\s+", "", s).rstrip(";")
    if len(s) < 8 or KEYWORD_ONLY.match(s) or IMPORT.match(s):
        return None
    return s


def eligible_path(path, eco):
    p = path.lower()
    return p.endswith(EXT[eco]) and not any(x in p for x in EXCL) and "node_modules" not in p


def parse_diff(text, eco):
    """-> {path: {"deleted": [...], "added": [...], "context_before_added": [...]}} (normalised lines)."""
    files, cur, ctx = {}, None, []
    for line in text.splitlines():
        if line.startswith("diff --git"):
            cur, ctx = None, []
            continue
        if line.startswith("+++ "):
            p = line[4:].strip()
            p = p[2:] if p.startswith("b/") else p
            cur = p if p != "/dev/null" and eligible_path(p, eco) else None
            if cur:
                files.setdefault(cur, {"deleted": [], "added": [], "context_before_added": []})
            continue
        if cur is None or line.startswith("--- ") or line.startswith("@@"):
            if line.startswith("@@"):
                ctx = []
            continue
        if line.startswith("-"):
            n = norm(line[1:], eco)
            if n:
                files[cur]["deleted"].append(n)
        elif line.startswith("+"):
            n = norm(line[1:], eco)
            if ctx is not None and ctx:
                files[cur]["context_before_added"] += ctx[-3:]
                ctx = None                      # only the context before the first added line of a block
            if n:
                files[cur]["added"].append(n)
        else:
            n = norm(line[1:] if line.startswith(" ") else line, eco)
            if ctx is None:
                ctx = []
            if n:
                ctx.append(n)
    return {p: v for p, v in files.items() if v["deleted"] or v["added"]}


def signature(files):
    """Deleted lines if any; else context before additions, with the added lines as the patch signature."""
    deleted = {p: v["deleted"] for p, v in files.items() if v["deleted"]}
    if deleted:
        return {"kind": "deleted", "sig": deleted, "patch": {}}
    ctx = {p: list(dict.fromkeys(v["context_before_added"])) for p, v in files.items() if v["context_before_added"]}
    return {"kind": "add_only", "sig": ctx, "patch": {p: v["added"] for p, v in files.items() if v["added"]}}


def fetch(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180) as r:
                return r.read()
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def release_files(blob, url, eco):
    """{relative path inside the package: set(normalised lines)} for source files."""
    out = {}
    try:
        if url.endswith((".whl", ".zip")):
            z = zipfile.ZipFile(io.BytesIO(blob))
            items = [(n, lambda n=n: z.read(n)) for n in z.namelist() if n.lower().endswith(EXT[eco]) and z.getinfo(n).file_size < 2_000_000]
        else:
            t = tarfile.open(fileobj=io.BytesIO(blob), mode="r:*")
            mem = [m for m in t.getmembers() if m.isfile() and m.name.lower().endswith(EXT[eco]) and m.size < 2_000_000]
            items = [(m.name, lambda m=m: t.extractfile(m).read()) for m in mem]
        for name, rd in items:
            if "node_modules" in name:
                continue
            rel = name.split("/", 1)[1] if "/" in name and not url.endswith(".whl") else name
            out[rel] = {x for x in (norm(l, eco) for l in rd().decode("utf-8", "ignore").splitlines()) if x}
    except Exception:
        return None
    return out


def match_file(path, rfiles):
    parts = path.split("/")
    best, score = None, 0
    for rp in rfiles:
        q = rp.split("/")
        k = 0
        while k < min(len(parts), len(q)) and parts[-1 - k] == q[-1 - k]:
            k += 1
        if k > score:
            best, score = rp, k
    return best


def presence(sig, rfiles):
    if rfiles is None:
        return {"state": "undetermined", "why": "download or parse failure"}
    allines = set().union(*rfiles.values()) if rfiles else set()
    found = total = 0
    for p, lines in sig["sig"].items():
        mf = match_file(p, rfiles)
        pool = rfiles[mf] if mf else allines
        for ln in lines:
            total += 1
            found += ln in pool
    if total == 0:
        return {"state": "undetermined", "why": "empty signature"}
    s = found / total
    patch_share = None
    if sig["kind"] == "add_only" and sig["patch"]:
        pl = [ln for v in sig["patch"].values() for ln in v]
        patch_share = sum(ln in allines for ln in pl) / len(pl) if pl else None
    if s >= PRESENT and (patch_share is None or patch_share < 0.5):
        st = "present"
    elif s <= ABSENT:
        st = "absent"
    else:
        st = "undetermined"
    return {"state": st, "s": round(s, 3), "patch_share": patch_share, "n_sig": total}


class NpmVersion:
    """node-semver ordering (pre-releases sort before their release); invalid versions raise on construction."""
    def __init__(self, v):
        import nodesemver
        self.sv = nodesemver.make_semver(v, loose=True)

    def _c(self, o):
        return self.sv.compare(o.sv)

    def __lt__(self, o): return self._c(o) < 0
    def __le__(self, o): return self._c(o) <= 0
    def __gt__(self, o): return self._c(o) > 0
    def __ge__(self, o): return self._c(o) >= 0
    def __eq__(self, o): return self._c(o) == 0


def vkey(eco):
    if eco == "npm":
        return NpmVersion
    from packaging.version import Version
    return Version


def in_range(eco, versions, intro, fixed):
    K = vkey(eco)
    out, bad = [], 0
    try:
        lo = None if intro == "0" else K(intro)
        hi = K(fixed)
    except Exception:
        return None, None
    for r in versions:
        try:
            v = K(r["version"])
        except Exception:
            bad += 1
            continue
        if (lo is None or v >= lo) and v < hi:
            out.append(r)
    return out, bad


def one(r):
    out = D / "presence" / f"{r.id}.json"
    if out.exists():
        return
    res = {"id": r.id, "ecosystem": r.ecosystem}
    dp = D / "commits" / f"{r.id}.diff"
    vp = D / "versions" / f"{r.id}.json"
    if not dp.exists():
        res["status"] = "no fix diff"; out.write_text(json.dumps(res)); return
    files = parse_diff(dp.read_text(errors="ignore"), r.ecosystem)
    sig = signature(files)
    res["sig_kind"], res["sig_lines"] = sig["kind"], sum(len(v) for v in sig["sig"].values())
    if not res["sig_lines"]:
        res["status"] = "no usable signature"; out.write_text(json.dumps(res)); return
    vs = json.loads(vp.read_text()) if vp.exists() else {}
    if "releases" not in vs:
        res["status"] = "no release list"; out.write_text(json.dumps(res)); return
    intro = sorted(json.loads(r.introduced_events), key=lambda x: (x != "0", x))[0]
    fixed_all = json.loads(r.fixed_events)
    K = vkey(r.ecosystem)
    try:
        lo = None if intro == "0" else K(intro)
        fixed = sorted((f for f in fixed_all if lo is None or K(f) > lo), key=K)[0]
    except Exception:
        res["status"] = "unparseable range"; out.write_text(json.dumps(res)); return
    rel, bad = in_range(r.ecosystem, vs["releases"], intro, fixed)
    if rel is None:
        res["status"] = "unparseable range"; out.write_text(json.dumps(res)); return
    rel.sort(key=lambda x: (x.get("time") or "9999", x["version"]))
    res.update({"introduced": intro, "fixed": fixed, "n_in_range": len(rel), "n_unparseable_versions": bad, "releases": []})
    n = 0
    for x in rel:
        if not x.get("url"):
            res["releases"].append({"version": x["version"], "time": x.get("time"), "state": "undetermined", "why": "no artefact"})
            continue
        if n >= CAP:
            res["releases"].append({"version": x["version"], "time": x.get("time"), "state": "undetermined", "why": "cap"})
            continue
        b = fetch(x["url"]); n += 1
        p = presence(sig, release_files(b, x["url"], r.ecosystem) if b else None)
        res["releases"].append({"version": x["version"], "time": x.get("time"), **p})
        if p["state"] == "present":
            break
    after = [x for x in vs["releases"] if x.get("url")]
    try:
        after = sorted((x for x in after if K(x["version"]) >= K(fixed)), key=lambda x: K(x["version"]))
    except Exception:
        after = []
    if after:
        b = fetch(after[0]["url"])
        res["first_fixed_release"] = {"version": after[0]["version"], **presence(sig, release_files(b, after[0]["url"], r.ecosystem) if b else None)}
    res["status"], res["downloads"] = "done", n + bool(after)
    out.write_text(json.dumps(res))


def run(limit=None):
    S = pd.read_csv(T / "sample.csv")
    if limit:
        S = S.head(int(limit))
    (D / "presence").mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        for k, _ in enumerate(ex.map(one, S.itertuples(index=False)), 1):
            if k % 50 == 0:
                print(time.strftime("%H:%M:%S"), k, "of", len(S), flush=True)
    print("presence done")


def test():
    diff = """diff --git a/lib/parse.js b/lib/parse.js
--- a/lib/parse.js
+++ b/lib/parse.js
@@ -10,7 +10,8 @@ function parse(input) {
   const parts = input.split(separator);
-  return parts.map(p => evaluate(p));
+  if (!isSafe(parts)) throw new Error('unsafe');
+  return parts.map(p => evaluateSafely(p));
 }
diff --git a/test/parse.test.js b/test/parse.test.js
--- a/test/parse.test.js
+++ b/test/parse.test.js
@@ -1,1 +1,2 @@
+expect(parse('x')).toThrow();
"""
    f = parse_diff(diff, "npm")
    assert list(f) == ["lib/parse.js"], f
    s = signature(f)
    assert s["kind"] == "deleted" and s["sig"]["lib/parse.js"] == ["returnparts.map(p=>evaluate(p))"], s
    rel = {"lib/parse.js": {"returnparts.map(p=>evaluate(p))", "constparts=input.split(separator)"}}
    assert presence(s, rel)["state"] == "present"
    assert presence(s, {"lib/parse.js": {"somethingelseentirely"}})["state"] == "absent"
    add_only = """diff --git a/pkg/core.py b/pkg/core.py
--- a/pkg/core.py
+++ b/pkg/core.py
@@ -5,6 +5,8 @@
 def load(path):
     data = open(path).read()
+    if '..' in path:
+        raise ValueError('traversal')
     return deserialize(data)
"""
    s2 = signature(parse_diff(add_only, "PyPI"))
    assert s2["kind"] == "add_only" and "data=open(path).read()" in s2["sig"]["pkg/core.py"], s2
    vuln = {"pkg/core.py": {"defload(path):", "data=open(path).read()", "returndeserialize(data)"}}
    fixed = {"pkg/core.py": vuln["pkg/core.py"] | {"if'..'inpath:", "raiseValueError('traversal')"}}
    assert presence(s2, vuln)["state"] == "present" and presence(s2, fixed)["state"] != "present"
    assert match_file("src/a/b.js", {"lib/a/b.js": set(), "x/b.js": set(), "c.js": set()}) == "lib/a/b.js"
    print("presence tests pass")


if __name__ == "__main__":
    {"run": lambda: run(*sys.argv[2:3]), "test": test}[sys.argv[1]]()
