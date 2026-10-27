"""Commits, tags and release ranges per repository (plan section 2).

  extract.py run    -> data/interim/release_flags.parquet  (one row per analysed release)
                       data/interim/commit_releases.parquet (package, commit, release, latency; tag-based ranges only)
                       data/interim/commits.parquet         (repo, sha, time, agent, rule, bot; no text, no identities)
                       data/interim/ai_matches.parquet      (repo, sha, agent, rule, the matched line; for the precision audit)
  extract.py clone  print the clone list (repos of the study set) to data/interim/repos.txt
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from attribution import COAUTHOR, GENERATED, TRAILER, classify, is_bot  # noqa: E402

INT, REPOS = RUN / "data" / "interim", RUN / "data" / "repos"
WINDOW = pd.Timestamp("2024-06-01", tz="UTC")
SEP_F, SEP_R = "\x1f", "\x1e"


def repo_dir(repo):
    return REPOS / (repo.replace("/", "__") + ".git")


def git(path, *args):
    r = subprocess.run(["git", "-C", str(path), *args], capture_output=True, timeout=1800)
    return r.stdout.decode("utf-8", "replace")


def tag_candidates(name, v):
    short = name.split("/", 1)[1] if name.startswith("@") else name
    out = []
    for n in dict.fromkeys([name, short]):
        out += [f"{n}@{v}", f"{n}-v{v}", f"{n}-{v}", f"{n}/v{v}", f"{n}_v{v}"]
    return [f"v{v}", v, f"release-{v}", f"release/{v}", f"version-{v}"] + out


def matched_line(msg):
    # D2 (after review): return the trailer that matched a rule, not the first co-author trailer (the stored line in
    # this run's ai_matches.parquet predates the fix; the stratified audit re-derives the matching text instead)
    for who in COAUTHOR.findall(msg):
        if any(pat.search(who) for _, pat in TRAILER):
            return "Co-authored-by: " + who
    m = GENERATED.search(msg)
    return m.group(0) if m else ""


def one_repo(args):
    repo, pkgs = args
    path = repo_dir(repo)
    if not path.exists():
        return None
    raw = git(path, "log", "--all", f"--format=%H{SEP_F}%P{SEP_F}%an{SEP_F}%ae{SEP_F}%cn{SEP_F}%ce{SEP_F}%ct{SEP_F}%B{SEP_R}")
    commits, parents = {}, {}
    ai_rows = []
    for rec in raw.split(SEP_R):
        rec = rec.strip("\n")
        if not rec:
            continue
        f = rec.split(SEP_F)
        if len(f) < 8:
            continue
        sha, par, an, ae, cn, ce, ct, msg = f[0], f[1].split(), f[2], f[3], f[4], f[5], int(f[6]), f[7]
        agent, rule = classify(an, ae, cn, ce, msg)
        commits[sha] = (ct, agent, rule, is_bot(an, ae) if agent is None else False)
        parents[sha] = par
        if agent:
            ai_rows.append({"repo": repo, "sha": sha, "agent": agent, "rule": rule,
                            "line": matched_line(msg) if rule != "identity" else f"identity: {an}"})
    head = set(git(path, "rev-list", "HEAD").split())
    tags = {}
    for line in git(path, "for-each-ref", "refs/tags", f"--format=%(refname:strip=2){SEP_F}%(objectname){SEP_F}%(*objectname)").splitlines():
        t, o, deref = (line.split(SEP_F) + ["", ""])[:3]
        tags[t.lower()] = deref or o
    memo = {}

    def reach(sha):
        if sha in memo:
            return memo[sha]
        seen, stack = set(), [sha]
        while stack:
            s = stack.pop()
            if s in seen or s not in commits:
                continue
            seen.add(s)
            stack.extend(parents.get(s, []))
        memo[sha] = seen
        return seen

    rel_rows, cr_rows = [], []
    for (eco, name), rels in pkgs:
        rels = rels.sort_values("published")
        prev_tag_sha, prev_pub = None, None
        for r in rels.itertuples():
            tsha = None
            for c in tag_candidates(name, r.version):
                if c.lower() in tags:
                    tsha = tags[c.lower()]
                    break
            if r.published >= WINDOW:
                lo = prev_pub.timestamp() if prev_pub is not None else -np.inf
                hi = r.published.timestamp()
                if tsha and tsha in commits:
                    rng = reach(tsha)
                    if prev_tag_sha and prev_tag_sha in commits:
                        rng = rng - reach(prev_tag_sha)
                        method = "tag"
                    else:
                        rng = {s for s in rng if commits[s][0] > lo}
                        method = "tag_date"
                else:
                    rng = {s for s in head if lo < commits.get(s, (0,))[0] <= hi} if head else set()
                    method = "date"
                ags = sorted({commits[s][1] for s in rng if commits[s][1]})
                rel_rows.append({"eco": eco, "name": name, "version": r.version, "published": r.published, "method": method,
                                 "n_commits": len(rng), "n_ai": sum(1 for s in rng if commits[s][1]), "agents": ",".join(ags),
                                 "flagged": bool(ags)})
                if method in ("tag", "tag_date"):
                    for s in rng:
                        ct, agent, _, bot = commits[s]
                        cr_rows.append({"repo": repo, "eco": eco, "name": name, "sha": s, "version": r.version,
                                        "latency_days": (hi - ct) / 86400, "ct": ct, "agent": agent, "bot": bot})
            if tsha and tsha in commits:
                prev_tag_sha = tsha
            prev_pub = r.published
    cm = pd.DataFrame([{"repo": repo, "sha": s, "ct": v[0], "agent": v[1], "rule": v[2], "bot": v[3]} for s, v in commits.items()])
    return rel_rows, cr_rows, cm, ai_rows


def run():
    P = pd.read_parquet(INT / "packages.parquet")
    R = pd.read_parquet(INT / "releases.parquet")
    P = P[P.repo.notna()]
    R = R.merge(P[["eco", "name", "repo"]], on=["eco", "name"])
    jobs = []
    for repo, g in R.groupby("repo"):
        jobs.append((repo, [((e, n), x[["version", "published"]]) for (e, n), x in g.groupby(["eco", "name"])]))
    rel, cr, cms, ais = [], [], [], []
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "8"))) as ex:
        for k, out in enumerate(ex.map(one_repo, jobs, chunksize=4), 1):
            if out:
                rel += out[0]; cr += out[1]; cms.append(out[2]); ais += out[3]
            if k % 500 == 0:
                print(k, "repos", flush=True)
    # D1: repositories with no commits since 2024-01-01 cannot be shallow-cloned; their releases have no AI commits
    inactive = inactive_repos()
    for repo, pk in jobs:
        if repo in inactive and not repo_dir(repo).exists():
            for (e, n), x in pk:
                for r in x[x.published >= WINDOW].itertuples():
                    rel.append({"eco": e, "name": n, "version": r.version, "published": r.published, "method": "inactive",
                                "n_commits": 0, "n_ai": 0, "agents": "", "flagged": False})
    pd.DataFrame(rel).to_parquet(INT / "release_flags.parquet", index=False)
    pd.DataFrame(cr).to_parquet(INT / "commit_releases.parquet", index=False)
    pd.concat(cms).drop_duplicates(["repo", "sha"]).to_parquet(INT / "commits.parquet", index=False)
    pd.DataFrame(ais).drop_duplicates(["repo", "sha"]).to_parquet(INT / "ai_matches.parquet", index=False)
    print("releases", len(rel), "commit-release rows", len(cr))


def inactive_repos():
    f = INT / "clone_failures.tsv"
    if not f.exists():
        return set()
    t = pd.read_csv(f, sep="\t", names=["repo", "status"])
    return set(t[t.status == "inactive"].repo)


def clone_list():
    P = pd.read_parquet(INT / "packages.parquet")
    repos = sorted(P.repo.dropna().unique())
    (INT / "repos.txt").write_text("\n".join(repos) + "\n")
    print(len(repos), "repos")


if __name__ == "__main__":
    {"run": run, "clone": clone_list}[sys.argv[1]]()
