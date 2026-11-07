You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/software-security-advisory-range-overapproximation/ (read-only except your
output in review/).

**The question.** Do GHSA advisories for npm and PyPI declare affected lower bounds that start before the vulnerable
code existed (H1: >= 25%), and does correcting them shrink affected (version, advisory) pairs 1.5-fold (H2)?
Method: line-signature patch presence (the fix's deleted lines, or context before add-only fixes) in each in-range
release, walked in publish order.

**Reported:** both Inconclusive. The pipeline gives 308/411 over-approximated (75%) and H2 2.18. The preregistered
G4 audit (separate session, 60 packets) confirms only 10/30 pipeline over-approximations (8 contradicted, 12
undecidable), so H1 is reported unreliable; the audit-calibrated range is 25-55%. Post hoc strict reading (module
missing in release A): 58% (52-64%), H2 1.35.

**What to read:** plan.md, deviations.md (D1-D3), report.md, results/plausibility.md, results/attribution_ledger.csv;
results/tables/ (sample.csv, classes.csv, classes_strict.csv, primary.json, posthoc_strict.json, g4_audit.json,
handtrace.json, coverage.json); code/ (eligible.py, fetch.py, presence.py, classify.py, audit_packets.py,
posthoc_strict.py, handtrace.py, figures.py). Data: data/raw (OSV zips), data/commits (diffs), data/versions,
data/presence (per-advisory release walks), data/audit (packets and the auditor's labels.json). The audit key is not
in the run directory; the scored result is g4_audit.json.

**Git.** Read-only git is fine. Verify the plan preceded any data, and that eligible.py/sample, fetch.py,
presence.py and classify.py were committed before any presence result.

**Environment.** venv/bin/python with -I. No pip installs. At most 8 workers. Keep downloads to a handful of
releases.

Check at least:
1. Eligibility and sampling (GHSA only, withdrawn excluded, the fix-commit choice, the SEMVER/ECOSYSTEM ranges).
2. Signatures and normalisation (do they capture the vulnerable code? the add-only rule; test-file exclusion).
3. Presence and path matching (longest-suffix match; the "any file" fallback; transpiled npm packages).
4. Classification and the release walk (publish order, pre-releases, the 400 cap hit by 41 advisories).
5. The G4 audit: packet construction (could A/B position leak the label?), the scoring rule, and whether
   "Inconclusive" follows. Is the audit-calibrated range a fair use of 30 cases?
6. The strict reading and H2: is 1.35 computed correctly, and is it fairly labelled post hoc?
7. Report: every number against the tables; the title and plain terms.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence, the fix). Put supporting scripts in review/reviewer_checks/. Gate checks: G1-G7 as in
METHODS.md (G4 failed its bar and is reported; check it is honest). Report any missing or hollow gate as a finding.
