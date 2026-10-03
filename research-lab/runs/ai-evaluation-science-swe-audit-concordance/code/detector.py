"""Deterministic, execution-free spec-gap detector (frozen in plan.md before any agreement statistic).

For a SWE-bench task, a "spec gap" is something the FAIL_TO_PASS tests require that the issue never specifies:
  (a) a novel identifier: a name used in the added test lines (attribute, imported, called or keyword-argument name)
      that (i) also appears in the gold patch's added lines, (ii) is not defined in the test patch itself, (iii) does
      not appear as a word in the problem statement, and (iv) does not occur anywhere in the repository at base_commit
      (git grep -w);
  (b) a novel message literal: a string literal in the added test code (adjacent literals joined across lines, as
      Python's implicit concatenation does) of >= 15 characters containing a space, within 200 characters after an
      assertion or match context (assert / raises / match= / warns / Regex / msg / message), that (i) shares a run of
      3 consecutive words with the gold patch's added lines (messages are often built with format/f-strings),
      (ii) is not a substring of the problem statement (case-insensitive), and (iii) does not occur in the repository
      at base_commit (git grep -F).
score = number of novel identifiers + novel literals; flag = score >= 1.
Hints (hints_text) are not used in the primary definition (agents are not shown them); a sensitivity version adds
them to the issue text.
"""
import builtins
import keyword
import re
import subprocess
from functools import lru_cache
from pathlib import Path

REPOS = Path(__file__).resolve().parents[1] / "data" / "repos"
NAME = r"[A-Za-z_][A-Za-z0-9_]*"
BUILTINS = set(dir(builtins))
SKIP = set(keyword.kwlist) | BUILTINS | {"self", "cls", "assert", "pytest", "mock", "unittest", "np", "pd", "plt"}


def added(diff, test_files=None):
    out, cur = [], None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            cur = ln[6:] if ln.startswith("+++ b/") else ln[4:]
            continue
        if ln.startswith("+") and not ln.startswith("+++"):
            out.append((cur, ln[1:]))
    return out


def names_used(lines):
    s = set()
    for ln in lines:
        code = re.sub(r"(['\"]).*?\1", " ", ln)  # drop string contents
        code = code.split("#")[0]
        s |= set(re.findall(rf"\.({NAME})", code))
        s |= set(re.findall(rf"\b({NAME})\s*\(", code))
        s |= set(re.findall(rf"[(,]\s*({NAME})\s*=(?!=)", code))
        m = re.match(rf"\s*from\s+[\w.]+\s+import\s+\(?(.+)", code)
        if m:
            s |= {p.split(" as ")[0].strip(" ()") for p in m.group(1).split(",")}
        m = re.match(rf"\s*import\s+([\w.]+)", code)
        if m:
            s |= set(m.group(1).split("."))
    return {n for n in s if n and re.fullmatch(NAME, n) and len(n) >= 3 and n not in SKIP}


def names_defined(lines):
    s = set()
    for ln in lines:
        s |= set(re.findall(rf"^\s*(?:async\s+)?def\s+({NAME})", ln))
        s |= set(re.findall(rf"^\s*class\s+({NAME})", ln))
        s |= set(re.findall(rf"^\s*({NAME})\s*(?::[^=]+)?=(?!=)", ln))
        s |= set(re.findall(rf"\bas\s+({NAME})", ln))
        s |= set(re.findall(rf"^\s*for\s+({NAME})", ln))
        m = re.match(rf"^\s*(?:async\s+)?def\s+{NAME}\s*\((.*)", ln)
        if m:
            s |= set(re.findall(rf"({NAME})\s*(?:[:=,)]|$)", m.group(1)))
    return s


MSG = re.compile(r"(assert|raises|match\s*=|warns|regex|msg\s*=|message\s*=)", re.I)
STR = re.compile(r"""(?:[rRbBuUfF]{0,2})("([^"\\\n]|\\.)*"|'([^'\\\n]|\\.)*')""")


def literals(lines):
    """Joined string literals (implicit concatenation across lines) in an assertion/match context."""
    code = "\n".join(lines)
    ms = list(STR.finditer(code))
    out, i = set(), 0
    while i < len(ms):
        j, parts = i, [ms[i].group(1)[1:-1]]
        while j + 1 < len(ms) and re.fullmatch(r"[\s()]*", code[ms[j].end():ms[j + 1].start()]):
            j += 1
            parts.append(ms[j].group(1)[1:-1])
        s_ = "".join(parts).replace("\\'", "'").replace('\\"', '"')
        ctx = code[max(0, ms[i].start() - 200):ms[i].start()]
        if len(s_) >= 15 and " " in s_ and MSG.search(ctx):
            out.add(s_)
        i = j + 1
    return out


def shares_3gram(lit, gold_words):
    w = re.findall(r"\w+", lit)
    return any(" ".join(w[k:k + 3]) in gold_words for k in range(len(w) - 2))


@lru_cache(maxsize=None)
def in_repo(repo, commit, needle, word):
    gd = REPOS / (repo.replace("/", "_") + ".git")
    cmd = ["git", "--git-dir", str(gd), "grep", "-q", "-I"] + (["-w"] if word else ["-F"]) + ["-e", needle, commit]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode not in (0, 1):
        raise RuntimeError(r.stderr.decode()[:300])
    return r.returncode == 0


def detect(task, use_hints=False):
    issue = task["problem_statement"] + ("\n" + (task.get("hints_text") or "") if use_hints else "")
    tl = [ln for f, ln in added(task["test_patch"])]
    gl = [ln for f, ln in added(task["patch"])]
    gold = "\n".join(gl)
    issue_words = set(re.findall(NAME, issue))
    cand = names_used(tl) - names_defined(tl)
    cand = {n for n in cand if re.search(rf"\b{re.escape(n)}\b", gold) and n not in issue_words}
    novel_ids = sorted(n for n in cand if not in_repo(task["repo"], task["base_commit"], n, True))
    gold_words = " ".join(re.findall(r"\w+", gold))
    lits = {s for s in literals(tl) if shares_3gram(s, gold_words) and s.lower() not in issue.lower()}
    novel_lits = sorted(s for s in lits if not in_repo(task["repo"], task["base_commit"], s, False))
    return dict(instance_id=task["instance_id"], n_ids=len(novel_ids), n_lits=len(novel_lits),
                score=len(novel_ids) + len(novel_lits), flag=int(len(novel_ids) + len(novel_lits) >= 1),
                novel_ids="|".join(novel_ids), novel_lits="|".join(novel_lits))
