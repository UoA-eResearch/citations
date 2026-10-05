"""Measure A (audit_plan.md): preregistration timing from git history. For each run: first commit adding plan.md,
first commit adding a results/ file or report.md, and every later commit touching plan.md (with diffstat).
Writes paper/audit/A_prereg_timing.csv and paper/audit/A_plan_edits.csv."""
import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "research-lab" / "runs"
OUT = REPO / "research-lab" / "paper" / "audit"


def git(*a):
    return subprocess.check_output(["git", *a], cwd=REPO, text=True)


def commits(path, extra=()):
    """(hash, unix time, subject) of commits touching path, oldest first."""
    out = git("log", "--reverse", "--format=%H%x09%ct%x09%s", *extra, "--", path).strip().splitlines()
    return [tuple(x.split("\t", 2)) for x in out if x]


def main():
    rows, edits = [], []
    for d in sorted(p for p in RUNS.iterdir() if p.is_dir()):
        rel = d.relative_to(REPO)
        plan = commits(f"{rel}/plan.md", ("--diff-filter=A",))
        res = commits(f"{rel}/results", ("--diff-filter=A",))
        rep = commits(f"{rel}/report.md", ("--diff-filter=A",))
        t_plan = int(plan[0][1]) if plan else None
        outs = [int(c[1]) for c in res[:1] + rep[:1]]
        t_out = min(outs) if outs else None
        first_out = min(res[:1] + rep[:1], key=lambda c: int(c[1])) if outs else None
        same_commit = bool(plan and first_out and plan[0][0] == first_out[0])
        rows.append(dict(run=d.name, plan_commit=plan[0][0][:7] if plan else None, t_plan=t_plan,
                         first_output_commit=first_out[0][:7] if first_out else None, t_out=t_out,
                         hours_plan_to_first_output=(t_out - t_plan) / 3600 if t_plan and t_out else None,
                         passes=bool(t_plan and (t_out is None or (t_plan < t_out and not same_commit))), same_commit=same_commit,
                         report_exists=(d / "report.md").exists()))
        allp = commits(f"{rel}/plan.md")
        for h, t, s in allp[1:]:
            stat = git("show", "--numstat", "--format=", h, "--", f"{rel}/plan.md").split()
            edits.append(dict(run=d.name, commit=h[:7], time=int(t), subject=s, lines_added=int(stat[0]) if stat else 0,
                              lines_removed=int(stat[1]) if len(stat) > 1 else 0, after_first_output=bool(t_out and int(t) > t_out)))
    a = pd.DataFrame(rows)
    a.to_csv(OUT / "A_prereg_timing.csv", index=False)
    e = pd.DataFrame(edits)
    e.to_csv(OUT / "A_plan_edits.csv", index=False)
    print(a[["run", "plan_commit", "first_output_commit", "hours_plan_to_first_output", "passes", "same_commit"]].round(1).to_string(index=False))
    print(f"\npass {int(a.passes.sum())}/{len(a)}; plan edits after first commit: {len(e)} (after first output: {int(e.after_first_output.sum()) if len(e) else 0})")
    if len(e):
        print(e[["run", "commit", "subject", "lines_added", "lines_removed", "after_first_output"]].to_string(index=False))


if __name__ == "__main__":
    main()


def rewrite_map():
    """Commits whose identity was rewritten on 2026-10-01 (filter-branch, author fix; see paper 5.2). Pairs each commit
    on the local backup ref that is not on main with the main commit having the same tree, author date and subject.
    Writes paper/audit/A_rewrite_map.csv (no author identities are written)."""
    back = "refs/heads/backup/pre-author-fix"
    old = git("rev-list", back, "--not", "main").split()
    cur = {}
    for h in git("rev-list", "main").split():
        t, ad, s = git("show", "-s", "--format=%T%x09%ad%x09%s", "--date=raw", h).strip().split("\t", 2)
        cur[(t, ad, s)] = h
    rows = []
    for h in old:
        t, ad, cd, s = git("show", "-s", "--format=%T%x09%ad%x09%cd%x09%s", "--date=raw", h).strip().split("\t", 3)
        new = cur.get((t, ad, s))
        nt, ncd = (git("show", "-s", "--format=%T%x09%cd", "--date=raw", new).strip().split("\t") if new else (None, None))
        rows.append(dict(original_sha=h, current_sha=new, tree=t, tree_identical=bool(new and nt == t), author_date=ad,
                         committer_date_identical=bool(new and ncd == cd), subject=s))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "A_rewrite_map.csv", index=False)
    print(d[["original_sha", "current_sha", "tree_identical", "committer_date_identical", "subject"]].to_string(index=False))


if __name__ == "__main__" and "--rewrite" in __import__("sys").argv:
    rewrite_map()
