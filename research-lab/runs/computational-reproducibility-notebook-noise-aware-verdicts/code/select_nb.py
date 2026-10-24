"""Sample and repository preparation (plan section 1, D1) -> data/interim/sample_ready.csv.

Eligible: dataset executions that completed (reason IS NULL) with at least one differing cell (diff_count > 0), Python
notebooks; at most two per repository (random, seed 20261025). Each repository is cloned (blob-less) and checked out
at its last commit before the article's publication date.
"""
import ast
import json
import random
import sqlite3
import subprocess
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
DB = D / "raw" / "unz" / "computational-reproducibility-pmc" / "computational-reproducibility-pmc" / "analyses" / "db.sqlite"
IMAP = json.loads((RUN / "code" / "import_map.json").read_text())
SEED = 20261025


def git(repo, *args, timeout=900):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=timeout)


def pyver(v):
    try:
        maj, mi = [int(x) for x in str(v).split(".")[:2]]
    except Exception:
        return "3.8"
    if maj != 3:
        return "3.8"
    return f"3.{min(max(mi, 8), 12)}"


def imports_of(nb):
    mods = set()
    for c in nb.get("cells", []):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", ""))
        src = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("%", "!")))
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                mods.add(n.module.split(".")[0])
    return sorted({IMAP[m] for m in mods if IMAP.get(m)})


def env_yml_to_reqs(p):
    import re
    out = []
    try:
        import yaml
        y = yaml.safe_load(p.read_text())
        deps = y.get("dependencies", []) if isinstance(y, dict) else []
    except Exception:
        return []
    for d in deps:
        if isinstance(d, dict) and "pip" in d:
            out += [str(x) for x in d["pip"]]
        elif isinstance(d, str):
            name = re.split(r"[=<>]", d.split("::")[-1])[0].strip()
            if name and name not in ("python", "pip", "setuptools", "wheel", "r-base") and not name.startswith("r-"):
                ver = d.split("=")[1] if d.count("=") >= 1 and "==" not in d else None
                out.append(f"{name}=={ver}" if ver and ver[0].isdigit() and ver.count(".") >= 1 else name)
    return out


def main():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = """select distinct n.id nb_id, n.name nb_path, n.language_version, r.id repo_db_id, r.repository, r."commit" dcommit,
                  a.published_date, rd.size gh_kb from executions e join notebooks n on n.id = e.notebook_id
           join repositories r on r.id = n.repository_id join article a on a.id = r.article_id
           left join repository_data rd on rd.repository_id = r.id
           where e.reason is null and e.diff_count > 0 and n.language = 'python'"""
    E = pd.read_sql(q, c)
    rnd = random.Random(SEED)
    pick = []
    for repo, g in E.groupby("repository"):
        ids = sorted(g.nb_id.tolist())
        rnd.shuffle(ids)
        pick += ids[:2]
    S = E[E.nb_id.isin(pick)].copy()
    print("sampled", len(S), "notebooks from", S.repository.nunique(), "repos", flush=True)
    from concurrent.futures import ThreadPoolExecutor
    rows = []
    with ThreadPoolExecutor(6) as ex:
        for r_ in ex.map(lambda kv: prep(*kv), S.groupby("repository")):
            rows += r_
    R = pd.DataFrame(rows)
    R.to_csv(D / "interim" / "sample_all.csv", index=False)
    R[R.status == "ready"].to_csv(D / "interim" / "sample_ready.csv", index=False)
    print(R.status.value_counts().to_string())


def prep(repo, g):
    try:
        return _prep(repo, g)
    except subprocess.TimeoutExpired:
        return [{"nbid": f"nb{x.nb_id}", "status": "checkout_timeout"} for x in g.itertuples()]


def _prep(repo, g):
    rows = []
    if True:
        rid = repo.replace("/", "__")
        if float(g.gh_kb.fillna(0).iloc[0]) > 500_000:            # GitHub size (KB) before any checkout
            return [{"nbid": f"nb{x.nb_id}", "repo_id": rid, "status": "too_large"} for x in g.itertuples()]
        path = D / "repos" / rid
        if not path.exists():
            r = subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", f"https://github.com/{repo}", str(path)],
                               capture_output=True, timeout=1800, env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin"})
            if r.returncode != 0:
                return [{"nbid": f"nb{x.nb_id}", "status": "clone_failed"} for x in g.itertuples()]
        pub = str(g.published_date.iloc[0])[:10]
        sha = git(path, "rev-list", "-1", f"--before={pub} 00:00", "HEAD").stdout.decode().strip()
        flagged = False
        if not sha:
            sha, flagged = g.dcommit.iloc[0], True
        if git(path, "checkout", "-q", "--force", sha).returncode != 0:
            sha, flagged = g.dcommit.iloc[0], True
            if git(path, "checkout", "-q", "--force", sha).returncode != 0:
                return [{"nbid": f"nb{x.nb_id}", "status": "checkout_failed"} for x in g.itertuples()]
        cdate = git(path, "log", "-1", "--format=%cs", sha).stdout.decode().strip()
        size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file() and ".git" not in f.parts)
        for x in g.itertuples():
            nbp = path / x.nb_path
            rec = {"nbid": f"nb{x.nb_id}", "repo_id": rid, "nb_path": x.nb_path, "pyver": pyver(x.language_version),
                   "asof_date": cdate, "asof_commit": sha, "asof_fallback": flagged, "published": pub, "repo_mb": round(size / 1e6, 1)}
            if size > 500e6:
                rows.append({**rec, "status": "too_large"}); continue
            if not nbp.exists():
                rows.append({**rec, "status": "notebook_missing"}); continue
            req = ""
            for cand in [nbp.parent / "requirements.txt", path / "requirements.txt"] + sorted((path / "requirements").glob("*.txt")):
                if cand.exists():
                    req = str(cand.relative_to(path)); break
            if not req:
                for cand in (nbp.parent / "environment.yml", path / "environment.yml", path / "environment.yaml"):
                    if cand.exists():
                        lines = env_yml_to_reqs(cand)
                        if lines:
                            (path / ".nbrepro_requirements.txt").write_text("\n".join(lines) + "\n")
                            req = ".nbrepro_requirements.txt"
                        break
            pkgs = ""
            if not req:
                try:
                    pkgs = " ".join(imports_of(json.loads(nbp.read_text(errors="replace"))))
                except Exception:
                    pkgs = ""
            rows.append({**rec, "req_path": req, "pkgs": pkgs, "status": "ready"})
    return rows


if __name__ == "__main__":
    main()
