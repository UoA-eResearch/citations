"""Frozen package lists and registry metadata (plan section 1).

  fetch.py top        top 10,000 npm and PyPI packages by last-month downloads (ecosyste.ms) -> data/raw/top_{npm,pypi}.json
  fetch.py registry   per package: releases (non-pre-release) with publish times, latest version, repository URL
                      -> data/interim/releases_{npm,pypi}.parquet, data/interim/packages.parquet
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, INT = RUN / "data" / "raw", RUN / "data" / "interim"
RAW.mkdir(parents=True, exist_ok=True)
INT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "research-lab-supply-chain-study (open-data research; github.com/UoA-eResearch/citations)"}
REG = {"npm": "npmjs.org", "pypi": "pypi.org"}
N = 10000
PRE_NPM = re.compile(r"-")                                     # semver pre-release
PRE_PY = re.compile(r"(a|b|rc|dev|alpha|beta|pre|preview|c)\d*", re.I)
GH = re.compile(r"github\.com[/:]+([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)


def get(url, tries=6, accept=None):
    h = dict(UA)
    if accept:
        h["Accept"] = accept
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(min(60, 2 ** k * 3))
        except Exception:
            time.sleep(min(60, 2 ** k * 3))
    return None


def gh_repo(url):
    if not url:
        return None
    m = GH.search(str(url))
    if not m:
        return None
    owner, repo = m.group(1).lower(), m.group(2).lower()
    repo = re.sub(r"\.git$", "", repo)
    if owner in ("sponsors", "orgs") or not repo:
        return None
    return f"{owner}/{repo}"


def top():
    for eco, reg in REG.items():
        out = []
        for page in range(1, N // 100 + 1):
            d = get(f"https://packages.ecosyste.ms/api/v1/registries/{reg}/packages?sort=downloads&order=desc&per_page=100&page={page}")
            assert d is not None, (eco, page)
            out += [{"name": p["name"], "downloads": p.get("downloads"), "downloads_period": p.get("downloads_period"),
                     "repository_url": p.get("repository_url"), "latest": p.get("latest_release_number")} for p in d]
            time.sleep(0.8)
        (RAW / f"top_{eco}.json").write_text(json.dumps({"fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "packages": out}))
        print(eco, len(out), flush=True)


def npm_meta(name):
    d = get("https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@"))
    if not d:
        return name, None
    t = d.get("time", {})
    rel = [(v, t[v]) for v in d.get("versions", {}) if v in t and not PRE_NPM.search(v)]
    repo = d.get("repository")
    repo = repo.get("url") if isinstance(repo, dict) else repo
    return name, {"latest": d.get("dist-tags", {}).get("latest"), "repo_reg": repo, "releases": rel}


def pypi_meta(name):
    d = get(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    if not d:
        return name, None
    rel = []
    for v, files in d.get("releases", {}).items():
        if not files or PRE_PY.search(v.split("+")[0].split(".")[-1]) or PRE_PY.search(v):
            continue
        rel.append((v, min(f["upload_time_iso_8601"] for f in files)))
    info = d.get("info", {})
    urls = list((info.get("project_urls") or {}).values()) + [info.get("home_page"), info.get("download_url")]
    repo = next((u for u in urls if u and "github.com" in u), None)
    return name, {"latest": info.get("version"), "repo_reg": repo, "releases": rel}


def registry():
    pk, rels = [], []
    for eco, fn in (("npm", npm_meta), ("pypi", pypi_meta)):
        top_ = json.loads((RAW / f"top_{eco}.json").read_text())["packages"]
        with ThreadPoolExecutor(8) as ex:
            meta = dict(ex.map(fn, [p["name"] for p in top_]))
        for rank, p in enumerate(top_, 1):
            m = meta.get(p["name"])
            repo = gh_repo(p.get("repository_url")) or (gh_repo(m["repo_reg"]) if m else None)
            pk.append({"eco": eco, "name": p["name"], "rank": rank, "downloads": p["downloads"], "repo": repo,
                       "latest": (m or {}).get("latest") or p.get("latest"), "registry_ok": m is not None})
            for v, t in (m or {}).get("releases", []):
                rels.append({"eco": eco, "name": p["name"], "version": v, "published": t})
        print(eco, "metadata", sum(v is not None for v in meta.values()), "of", len(top_), flush=True)
    P = pd.DataFrame(pk)
    R = pd.DataFrame(rels)
    R["published"] = pd.to_datetime(R.published, utc=True, format="ISO8601")
    P.to_parquet(INT / "packages.parquet", index=False)
    R.to_parquet(INT / "releases.parquet", index=False)
    print(P.groupby("eco").agg(n=("name", "size"), repo=("repo", lambda s: s.notna().sum()),
                               unique_repos=("repo", "nunique")).to_string())


if __name__ == "__main__":
    {"top": top, "registry": registry}[sys.argv[1]]()
