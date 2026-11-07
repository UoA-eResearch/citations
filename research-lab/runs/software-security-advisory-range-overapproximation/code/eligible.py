"""Eligibility and sample (plan section 1). -> data/eligible.parquet, results/tables/sample.csv, coverage stage "eligible"

Eligible: GHSA records, not withdrawn, exactly one affected package in the ecosystem, a SEMVER or ECOSYSTEM range with
an `introduced` and a `fixed` event (OSV encodes npm ranges as SEMVER and PyPI ranges as ECOSYSTEM; D1), and at least
one fix commit (a FIX reference or a github.com/{owner}/{repo}/commit/{sha} URL). The lower bound studied is the
earliest `introduced` of the package's ranges; the paired `fixed` is the first `fixed` after it.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

SEED, N_PER = 20261107, 400
COMMIT = re.compile(r"https?://github\.com/([^/\s]+)/([^/\s]+)/(?:pull/\d+/)?commits?/([0-9a-f]{7,40})", re.I)
REPO = re.compile(r"https?://github\.com/([^/\s#?]+)/([^/\s#?]+)", re.I)


def rows(eco):
    with zipfile.ZipFile(D / "raw" / f"{eco}.zip") as z:
        for name in z.namelist():
            if name.endswith(".json"):
                yield json.loads(z.read(name))


def main():
    out, drops = [], {}
    n_all = 0

    def drop(k):
        drops[k] = drops.get(k, 0) + 1
    for eco in ("npm", "PyPI"):
        for r in rows(eco):
            n_all += 1
            if not r.get("id", "").startswith("GHSA-"):
                drop(f"{eco}: not a GHSA record"); continue
            if r.get("withdrawn"):
                drop(f"{eco}: withdrawn"); continue
            aff = [a for a in r.get("affected", []) if a.get("package", {}).get("ecosystem") == eco]
            if len(aff) != 1:
                drop(f"{eco}: not exactly one affected package"); continue
            a = aff[0]
            evs = []
            for rg in a.get("ranges", []):
                if rg.get("type") in ("SEMVER", "ECOSYSTEM"):
                    evs += rg.get("events", [])
            intro = [e["introduced"] for e in evs if "introduced" in e]
            fixed = [e["fixed"] for e in evs if "fixed" in e]
            if not intro or not fixed:
                drop(f"{eco}: no introduced+fixed range"); continue
            refs = r.get("references", [])
            commits = []
            for ref in refs:
                m = COMMIT.search(ref.get("url", ""))
                if m:
                    commits.append((m.group(1).lower(), m.group(2).lower().removesuffix(".git"), m.group(3).lower()))
            if not commits:
                drop(f"{eco}: no fix commit"); continue
            pkg_repo = None
            for ref in refs:
                if ref.get("type") == "PACKAGE":
                    m = REPO.search(ref.get("url", ""))
                    if m:
                        pkg_repo = (m.group(1).lower(), m.group(2).lower().removesuffix(".git"))
            pick = next((c for c in commits if pkg_repo and (c[0], c[1]) == pkg_repo), commits[0])
            out.append({"id": r["id"], "ecosystem": eco, "package": a["package"]["name"], "introduced_events": json.dumps(intro),
                        "fixed_events": json.dumps(fixed), "n_ranges_events": len(evs), "intro_zero": "0" in intro,
                        "fix_owner": pick[0], "fix_repo": pick[1], "fix_sha": pick[2], "n_fix_commits": len(set(commits)),
                        "repo_matches_package": bool(pkg_repo and (pick[0], pick[1]) == pkg_repo),
                        "published": r.get("published"), "modified": r.get("modified"),
                        "severity": (r.get("database_specific") or {}).get("severity")})
    E = pd.DataFrame(out)
    E.to_parquet(D / "eligible.parquet", index=False)
    rng = np.random.default_rng(SEED)
    S = pd.concat([g.iloc[rng.choice(len(g), min(N_PER, len(g)), replace=False)] for _, g in E.sort_values("id").groupby("ecosystem")])
    S.to_csv(T / "sample.csv", index=False)
    c = Coverage("eligible", T / "coverage.json")
    c.add_counts(ok=int(len(E)), drops=drops)
    c.save()
    print(n_all, "records;", len(E), "eligible;", E.ecosystem.value_counts().to_dict(), "; sampled", len(S),
          "; intro_zero share in sample", round(float(S.intro_zero.mean()), 3))
    print(drops)


if __name__ == "__main__":
    main()
