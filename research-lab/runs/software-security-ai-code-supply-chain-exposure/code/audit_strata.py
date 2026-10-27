"""POST HOC (D2, after review): stratified precision audit with two blind labellers (G4, G7).

The first audit (results/tables/precision_audit.json) sampled at random, so ~80% of it was Anthropic-address trailers
that cannot be false, and its stored line was the first co-author trailer, not the matching one. Here each sampled
commit's matching text is re-derived from the clone with the same rules, and the riskier rules are oversampled.

  audit_strata.py build    -> data/interim/audit2_key.json (item -> stratum, agent, rule; hidden from labellers)
                              data/interim/audit2_items_A.json, audit2_items_B.json (same items, two shuffled orders)
  audit_strata.py report   -> results/tables/precision_audit_strata.json (after labels A, B and adjudication)
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, REPOS, TAB = RUN / "data" / "interim", RUN / "data" / "repos", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
from attribution import COAUTHOR, GENERATED, IDENTITY, TRAILER  # noqa: E402

SEED = 20261027
STRATA = {"anthropic_address_trailer": 10, "claude_trailer_no_anthropic_address": 25, "copilot_suggestion_trailer": 10,
          "copilot_other_trailer": 15, "other_agent_trailer": 25, "generated_line": 10, "identity": 25}


def matched(repo, sha):
    """Re-run the rules on the full commit; return (rule, agent, matched text, author identity).
    Reads the local commit object only (`git cat-file commit`): `git show` on these treeless partial clones
    lazy-fetches from the remote."""
    path = REPOS / (repo.replace("/", "__") + ".git")
    r = subprocess.run(["git", "-C", str(path), "-c", "fetch.negotiationAlgorithm=noop", "cat-file", "commit", sha],
                       capture_output=True, text=True, errors="replace", env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin"})
    if r.returncode != 0 or "\n\n" not in r.stdout:
        return None
    head, msg = r.stdout.split("\n\n", 1)
    who = {}
    for line in head.splitlines():
        k, _, v = line.partition(" ")
        if k in ("author", "committer"):
            nm, _, rest = v.partition(" <")
            who[k] = (nm, rest.split(">", 1)[0])
    an, ae = who.get("author", ("", ""))
    cn, ce = who.get("committer", ("", ""))
    for who in COAUTHOR.findall(msg):
        for agent, pat in TRAILER:
            if pat.search(who):
                return "trailer", agent, "Co-authored-by: " + who, f"{an} <{ae}>"
    m = GENERATED.search(msg)
    if m:
        return "generated", None, m.group(0), f"{an} <{ae}>"
    for ident in (f"{an} <{ae}>", f"{cn} <{ce}>"):
        for agent, pat in IDENTITY:
            if pat.search(ident):
                return "identity", agent, ident, f"{an} <{ae}>"
    return None


def stratum(rule, agent, text):
    t = text.lower()
    if rule == "trailer" and agent == "claude":
        return "anthropic_address_trailer" if "noreply@anthropic.com" in t else "claude_trailer_no_anthropic_address"
    if rule == "trailer" and agent == "copilot":
        return "copilot_suggestion_trailer" if "+copilot@users.noreply.github.com" in t else "copilot_other_trailer"
    if rule == "trailer":
        return "other_agent_trailer"
    return {"generated": "generated_line", "identity": "identity"}[rule]


def build():
    A = pd.read_parquet(INT / "ai_matches.parquet")
    rng = np.random.default_rng(SEED)
    A = A.iloc[rng.permutation(len(A))].reset_index(drop=True)
    # cheap pre-strata from the stored columns, to know where to look; the final stratum uses the re-derived text
    pre = np.where(A.rule == "identity", "identity", np.where(A.rule == "generated", "generated_line",
                   np.where(A.agent == "claude", "claude", np.where(A.agent == "copilot", "copilot", "other_agent_trailer"))))
    want = dict(STRATA)
    items, key, tried = [], {}, 0
    order = {"claude": ["anthropic_address_trailer", "claude_trailer_no_anthropic_address"],
             "copilot": ["copilot_suggestion_trailer", "copilot_other_trailer"]}
    for pstr in ["identity", "generated_line", "other_agent_trailer", "copilot", "claude"]:
        targets = order.get(pstr, [pstr])
        for i in np.flatnonzero(pre == pstr):
            if all(want[t] == 0 for t in targets):
                break
            r = A.iloc[i]
            tried += 1
            m = matched(r.repo, r.sha)
            if m is None:
                continue
            rule, agent, text, author = m
            s = stratum(rule, agent or r.agent, text)
            if s not in targets or want[s] == 0:
                continue
            want[s] -= 1
            iid = f"i{len(items):03d}"
            items.append({"id": iid, "matched_text": text, "commit_author": author})
            key[iid] = {"stratum": s, "agent": r.agent, "rule": rule, "repo": r.repo, "sha": r.sha}
    for name, seed in (("A", 1), ("B", 2)):
        perm = np.random.default_rng([SEED, seed]).permutation(len(items))
        (INT / f"audit2_items_{name}.json").write_text(json.dumps([items[j] for j in perm], indent=1, ensure_ascii=False))
    (INT / "audit2_key.json").write_text(json.dumps(key, indent=1))
    print(len(items), "items;", tried, "commits re-derived; unfilled:", {k: v for k, v in want.items() if v})


def cp_lower(k, n, alpha=0.025):
    """Clopper-Pearson lower bound: the p at which P(X >= k | n, p) = alpha (exact binomial tail, bisection)."""
    from math import comb
    if k == 0:
        return 0.0
    tail = lambda p: sum(comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tail(mid) < alpha else (lo, mid)
    return lo


def report():
    key = json.loads((INT / "audit2_key.json").read_text())
    final = json.loads((INT / "audit2_labels_final.json").read_text())
    agree = json.loads((INT / "audit2_agreement.json").read_text())
    rows = [{"stratum": key[i]["stratum"], "agent": key[i]["agent"], "label": final[i]["label"]} for i in key]
    df = pd.DataFrame(rows)
    out = {"items": int(len(df)), "agreement": agree, "by_stratum": {}}
    for s, g in df.groupby("stratum"):
        k, n = int((g.label == "ai_signature").sum()), int(len(g))
        out["by_stratum"][s] = {"n": n, "ai_signature": k, "not_ai": int((g.label == "not_ai").sum()),
                                "uncertain": int((g.label == "uncertain").sum()), "precision": round(k / n, 3),
                                "ci95_lower_clopper_pearson": round(cp_lower(k, n), 3)}
    for lab in ("A", "B"):
        L = json.loads((INT / f"audit2_labels_{lab}.json").read_text())
        out[f"labeller_{lab}_ai_share"] = round(float(np.mean([L[i]["label"] == "ai_signature" for i in key])), 3)
    (TAB / "precision_audit_strata.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"build": build, "report": report}[sys.argv[1]]()
