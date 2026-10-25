You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/software-security-ai-code-supply-chain-exposure/ (read-only except your
output in review/).

**The question.** How far do AI-agent-signed commits reach npm/PyPI registry releases, and through deps.dev-resolved
dependency trees, download-weighted installs? Do they reach releases faster than matched human commits?

**Reported:**
- **H1 Refuted:** npm R = P_w / p = 1.03 and P_w 22.3% (upper bound 24% < 30%); PyPI R = 1.91.
- **H2 Refuted:** latency ratio 1.01.
- **Trend:** about 11–13% of non-bot commits are agent-signed by September 2026, and 33–37% of releases are flagged.
- **Precision audit:** 100/100.

**What to read:** plan.md, deviations.md (D1 inactive repositories), report.md, code/ (attribution.py, fetch.py,
clone.sh, classify_failures.sh, extract.py, deps.py, analyse.py, figures.py) and results/tables/ (primary.json,
precision_audit.json). The data are in data/interim/*.parquet. The bare clones are in data/repos/ (13k repositories;
use `git -C` read-only; never fetch).

**Git.** Read-only git is fine. Verify that plan.md, attribution.py and the pipeline code preceded the data, and D1
preceded the flags.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep CPU moderate (≤ 4 processes), with no
network fetches beyond a handful of spot-checks. Put scripts and outputs under review/reviewer_checks/. Do not copy
commit messages or personal names into review files; package names and counts are fine.

Check at least:

1. **Attribution.**
   - False positives: re-audit a fresh sample of 100 with a different seed, and check the "copilot" trailer rule
     (Copilot Autofix and review suggestions count as AI here; is that defensible?) and the "claude" name rule.
   - False negatives that are easy to catch: agent signatures in the data that the rules miss.
2. **Release ranges.**
   - Tag matching (wrong tag for a version? Tags shared across monorepo packages?).
   - The date fallback (134,584 releases) and its effect.
   - Shallow-history effects: the first release in the window with no previous tag takes all reachable commits since
     2024-01-01. Could that over-flag?
   - Are pre-release filters right (npm "-", PyPI a/b/rc/dev)?
3. **Exposure.**
   - deps.dev name and version matching: PyPI normalisation, versions such as "1.0" vs "1.0.0".
   - Root inclusion in the tree.
   - Coverage of nodes, and download weights (ecosyste.ms last-month downloads).
   - Is the bootstrap right (p and P_w recomputed jointly)?
   - Is R a meaningful comparison when P_w includes the root itself?
4. **Monorepos.** Is npm's 22% mostly an artefact of monorepo ranges? Should the headline use the monorepo-free
   figures? Is the sensitivity's "drop" correct (siblings unflagged in trees)?
5. **Latency (H2).**
   - Matching within (repo, package) instead of the plan's "same repository".
   - Negative latencies, and the treatment of commits in several releases.
   - The 65,399 unmatched agent commits: does excluding them bias the comparison?
6. **Report.** Check every number against primary.json, and that the title, the plain-terms section ("not rushed
   out", "a third of new releases") and the trend claims are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest; check the new monorepo-free monthly shares
  (`code/monthly_nomono.py`).
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check .`; spot-check claims.
- **G4/G7:** the precision audit (100/100) has a single auditor and no second labeller. Is its sample representative
  (identity matches, bots)? Would a second blind audit change anything?
- **G1–G2:** silent fallbacks in release-range mapping (tag-less releases, failed clones counted how?).

Report any gate that is missing or hollow as a finding.
