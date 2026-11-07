# Deviations from plan.md

## D1 — 2026-11-07 19:00 NZDT — range type, before any commit or release was fetched

OSV encodes npm ranges as type SEMVER and PyPI ranges as type ECOSYSTEM. Plan section 1 says "an ECOSYSTEM range";
eligibility accepts either type. Nothing else changes. Eligibility counts: 258,101 records, 6,409 eligible (npm
3,244, PyPI 3,165); 800 sampled (seed 20261107).

## D2 — 2026-11-08 — implementation details (before any presence result, except item 3)

1. **Fix diffs** come from the public `github.com/{owner}/{repo}/commit/{sha}.diff` URL. This host has no GitHub
   token, and the REST API allows 60 unauthenticated requests per hour. 790 of 800 were fetched; 10 were not found.
2. **Release walk.** Plan section 1 says every release the declared range covers is downloaded. The classification
   (section 3) depends only on releases up to the first present one, so `presence.py` walks in publish order and
   stops at the first present release. It also checks the first release at or after `fixed` (secondary 3). A cap of
   400 downloads per advisory marks the rest undetermined. All of this was set in code committed before the run.
   H2 counts in-range releases from the registry lists, so it does not need downloads past the first present
   release.
3. **The cap was hit by 41 advisories** (found after the run). Their remaining releases count as undetermined, so
   an advisory whose first present release lies beyond 400 downloads is undetermined, not over-approximated.

## D3 — 2026-11-08 — after the G4 audit (post hoc)

The preregistered G4 audit failed its bar. A separate session judged 60 packets from the code alone, and agreed with
"over-approximated" in 10 of 30 cases (33%, against the 80% bar): 8 contradicted, 12 undecidable from the packet.
Agreement on "tight" was 24 of 30. By the plan's rule, H1 is reported as unreliable. The pipeline's verdicts
(H1 75%, H2 2.18) stay in the report beside the audit, and the headline verdicts are Inconclusive. Two post hoc
readings are added (`code/posthoc_strict.py`, `results/tables/posthoc_strict.json`):
1. **Strict over-approximation.** Release A has no file with the same name as any file the fix touches: 142 of
   308. That is 58% (52–64%) of strict plus tight. No audited strict case was contradicted, but 10 of 14 were
   undecidable. Under this reading H2's factor is 1.35 (1.27–1.45).
2. **Audit-calibrated range for H1.** The audited fractions (10 confirmed, 8 contradicted, 12 undecidable of 30)
   are applied to all 308 pipeline over-approximations: 25% to 55% of classified advisories.
