"""Fix-commit diffs and release lists for the sampled advisories (plan section 1).

  fetch.py commits    GitHub REST API unified diff per advisory (<= 1 request/s) -> data/commits/<id>.diff
  fetch.py versions   registry release list with publish dates -> data/versions/<id>.json

Diffs come from the public github.com/{owner}/{repo}/commit/{sha}.diff URL. The REST API is a fallback only when a token
is passed explicitly in the GITHUB_TOKEN environment variable (D4: the first version queried git's credential store
implicitly; no GitHub token was present on this host, so all 790 diffs came from the public URLs).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
UA = "research-lab advisory-range study (open-data research; github.com/UoA-eResearch/citations)"


def token():
    return os.environ.get("GITHUB_TOKEN") or None          # explicit opt-in only


def get(url, headers=None, timeout=120):
    h = {"User-Agent": UA, **(headers or {})}
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410, 422, 451):
                return None
            time.sleep(10 * (attempt + 1))
        except Exception:
            time.sleep(10 * (attempt + 1))
    return None


def commits():
    S = pd.read_csv(T / "sample.csv")
    out = D / "commits"
    out.mkdir(exist_ok=True)
    tok = token()
    hdr = {"Accept": "application/vnd.github.v3.diff"}
    if tok:
        hdr["Authorization"] = f"Bearer {tok}"
    n_ok = n_fail = 0
    for r in S.itertuples():
        f = out / f"{r.id}.diff"
        if f.exists():
            continue
        b = get(f"https://github.com/{r.fix_owner}/{r.fix_repo}/commit/{r.fix_sha}.diff")   # public diff URL (no token on this host)
        if b is None and tok:
            b = get(f"https://api.github.com/repos/{r.fix_owner}/{r.fix_repo}/commits/{r.fix_sha}", hdr)
        if b is None:
            (out / f"{r.id}.missing").write_text("not found\n"); n_fail += 1
        else:
            f.write_bytes(b); n_ok += 1
        time.sleep(1.0)
    print("commits ok", n_ok, "missing", n_fail)


def versions_one(r):
    f = D / "versions" / f"{r.id}.json"
    if f.exists():
        return
    if r.ecosystem == "npm":
        b = get("https://registry.npmjs.org/" + urllib.parse.quote(r.package, safe="@"))
        if not b:
            f.write_text(json.dumps({"error": "not found"})); return
        doc = json.loads(b)
        t = doc.get("time", {})
        rel = [{"version": v, "time": t.get(v), "url": (m.get("dist") or {}).get("tarball"),
                "downloads": None} for v, m in doc.get("versions", {}).items()]
    else:
        b = get(f"https://pypi.org/pypi/{urllib.parse.quote(r.package)}/json")
        if not b:
            f.write_text(json.dumps({"error": "not found"})); return
        doc = json.loads(b)
        rel = []
        for v, files in doc.get("releases", {}).items():
            if not files:
                continue
            sd = [x for x in files if x.get("packagetype") == "sdist"]
            wh = [x for x in files if x.get("packagetype") == "bdist_wheel" and x.get("filename", "").endswith("-none-any.whl")]
            pick = (sd or wh or [None])[0]
            rel.append({"version": v, "time": min(x.get("upload_time_iso_8601") or "" for x in files),
                        "url": pick.get("url") if pick else None, "kind": pick.get("packagetype") if pick else None})
    f.write_text(json.dumps({"releases": rel}))


def versions():
    S = pd.read_csv(T / "sample.csv")
    (D / "versions").mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(versions_one, S.itertuples(index=False)))
    print("versions done", len(list((D / "versions").glob("*.json"))))


if __name__ == "__main__":
    {"commits": commits, "versions": versions}[sys.argv[1]]()
