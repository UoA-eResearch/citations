"""G3 hand traces (D4, after the independent review; the first version used three chosen advisories and the pipeline's
own path matching, kept as handtrace_v1_chosen.json). One seeded-random advisory from each class (tight,
over-approximated, undetermined): re-download the earliest in-range release and, for over-approximated ones, the first
present release, with plain urllib and tarfile/zipfile; match each fix file to a release file by hand (the release file
whose path ends with the longest run of the fix path's components, written here without presence.py); and count, by
plain substring search on whitespace-stripped text, how many of the fix's deleted lines occur in the matched file, or
anywhere in the release when no file matches. -> results/tables/handtrace.json"""
import io
import json
import re
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T, D = RUN / "results" / "tables", RUN / "data"
sys.path.insert(0, str(RUN / "code"))
import classify as C  # noqa: E402  (release list order only)

EXT = {"npm": (".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx"), "PyPI": (".py",)}
UA = "research-lab advisory-range study (open-data research; github.com/UoA-eResearch/citations)"


def download(url, eco):
    b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180).read()
    files = {}
    if url.endswith((".whl", ".zip")):
        z = zipfile.ZipFile(io.BytesIO(b))
        for n in z.namelist():
            if n.lower().endswith(EXT[eco]) and "node_modules" not in n:
                files[n if url.endswith(".whl") else n.split("/", 1)[-1]] = z.read(n).decode("utf-8", "ignore")
    else:
        t = tarfile.open(fileobj=io.BytesIO(b), mode="r:*")
        for m in t.getmembers():
            if m.isfile() and m.name.lower().endswith(EXT[eco]) and "node_modules" not in m.name:
                files[m.name.split("/", 1)[-1]] = t.extractfile(m).read().decode("utf-8", "ignore")
    return files


def fix_files(diff):
    out, cur = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
            if cur:
                out.setdefault(cur, [])
        elif cur and line.startswith("-") and not line.startswith("---") and len(line.strip()) > 9:
            out[cur].append(re.sub(r"\s+", "", line[1:]))
    return {p: v for p, v in out.items() if v}


def by_hand_match(path, files):
    want = path.split("/")
    best, best_k = None, 0
    for f in files:
        have = f.split("/")
        k = 0
        while k < len(want) and k < len(have) and want[len(want) - 1 - k] == have[len(have) - 1 - k]:
            k += 1
        if k > best_k:
            best, best_k = f, k
    return best


K = pd.read_csv(T / "classes.csv")
rng = np.random.default_rng(20261110)
out = {}
for cls in ("tight", "over-approximated", "undetermined"):
    pool = K[K.cls == cls].sort_values("id")
    pool = pool[pool.id.map(lambda i: (D / "commits" / f"{i}.diff").exists())]
    r = pool.iloc[rng.integers(len(pool))].to_dict()
    eco = r["ecosystem"]
    ff = fix_files((D / "commits" / f"{r['id']}.diff").read_text(errors="ignore"))
    ff = {p: v for p, v in ff.items() if p.lower().endswith(EXT[eco])
          and not any(x in p.lower() for x in ("test", "spec", "example", "doc", "dist/", ".min."))}   # the plan's exclusions
    pres = json.loads((D / "presence" / f"{r['id']}.json").read_text())
    rel = C.in_range_sorted(r) if pres.get("status") == "done" else []
    idx = [0]
    if cls == "over-approximated":       # also the first absent release (s <= 0.2) before the first present one
        fa = next(j for j, x in enumerate(pres["releases"][: int(r["fp"])]) if x.get("s") is not None and x["s"] <= 0.2)
        idx = sorted({0, fa, int(r["fp"])})
    res = {"id": r["id"], "pipeline_class": cls, "n_in_range": len(rel), "fix_files": len(ff), "releases": []}
    for i in idx if rel else []:
        x = rel[i]
        if not x.get("url"):
            res["releases"].append({"index": i, "version": x["version"], "note": "no artefact"}); continue
        files = download(x["url"], eco)
        everything = re.sub(r"\s+", "", "\n".join(files.values()))
        found = total = 0
        matched = {}
        for p, lines in ff.items():
            mf = by_hand_match(p, files)
            matched[p] = mf
            hay = re.sub(r"\s+", "", files[mf]) if mf else everything
            total += len(lines); found += sum(ln in hay for ln in lines)
        st = pres["releases"][i] if i < len(pres["releases"]) else {}
        res["releases"].append({"index": i, "version": x["version"], "source_files": len(files), "matched": matched,
                                "deleted_lines_found": found, "deleted_lines": total,
                                "share_by_hand": round(found / total, 3) if total else None,
                                "pipeline_s": st.get("s"), "pipeline_state": st.get("state")})
    out[cls] = res
    print(json.dumps(res)[:600], flush=True)
(T / "handtrace.json").write_text(json.dumps(out, indent=1) + "\n")
