You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/legal-digital-humanities-precedent-erosion-before-overruling/ (read-only except
your output in review/).

**The question.** Do lower-court citations to US Supreme Court precedents decline before the Court overrules them?
H1: the pre-share D(−1)/D(+5) is at least 0.33, from a stacked matched PPML event study on CourtListener citations.

**Reported:**
- **H1 not testable:** D(+5) 0.27 (−0.13 to 0.49).
- **Excluding co-citing opinions:** D(+5) 0.65, pre-share 0.31 (−1.43 to 0.81).
- **D1, post-result:** a 2019–2020 CourtListener federal coverage break (federal citations triple). A post hoc
  analysis of windows before the break shows overruled precedents cited 55% more than controls the year before
  overruling.

**What to read:** plan.md, deviations.md, report.md, code/ (idmap.py, overruled.py, counts.py, event.py,
secondary.py, figures.py), results/tables/ (overruled_pairs.csv, overruled_coverage.json, scotus_cites_by_year.csv,
primary.json, posthoc_pre2019.json, event_path.csv, secondary.json, stacks.json, matching_balance.json) and
results/figures/. The data are in data/ (interim/*.parquet, raw/, cl_raw -> the CourtListener dumps).

**Git.** Read-only git is fine. Verify that plan.md and the counting and event code preceded cites_scotus.parquet
and primary.json, and when D1 was logged.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only; use few cores. Put scripts and
outputs under review/reviewer_checks/.

Check at least:

1. **The citation mapping (idmap.py, counts.py).**
   - The CSV dialect, the opinion → cluster → docket → court chain, and citing year = citing cluster date_filed.
   - Dedup per citing–cited cluster pair.
   - "Lower-court" means citing court ≠ scotus, which includes attorney-general opinions and the like. Does it
     matter?
   - About 500,000 Supreme Court clusters: orders and duplicates. Can a precedent be split across duplicate clusters,
     and does the "most-cited cluster" rule lose citations?
2. **Treatment assignment (overruled.py).**
   - The Wikipedia parse (132 pairs), and U.S.-cite linking.
   - First overruling, the age ≥ 20 and ≥ 50-citation rules.
   - Partial overrulings. How incomplete is the list against SCDB?
3. **Matching and the model (event.py).**
   - The control pool (never listed, ±2 years, issue area, ≥ 50 citations) and the Mahalanobis matching.
   - Balance (standardised difference 0.28): is it adequate?
   - Stacked FE, the event dummies and the reference window, and dropping all-zero cases.
   - The bootstrap: spawn workers, stack resampling and relabelling.
   - Is "not testable" applied correctly? Is the pre-share robust or meaningless when D(+5) is small?
4. **The coverage break (D1).**
   - Is the 2019–2020 federal jump real, and how does it bias stacks by citer mix?
   - Is the post hoc pre-2019 restriction a fair fix? Does the "cited more before overruling" pattern survive
     reasonable alternatives: federal-only before 2019, other matching, or excluding the most-cited cases?
   - Is the Chevron interpretation right?
5. **Report.** Check every number against the tables, and that the plain-terms section and title are fair. Is "the
   evidence runs against erosion" justified for a post hoc analysis?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes (`python3 -I ../../tools/overclaim_check.py . --verify`) and is honest;
  re-label any sentence you disagree with.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check .`; spot-check claims
  against their sources, especially the corrected Feldman framing.
- **G1–G4, where they apply:** label-correlated fields (for example matching on pre-period citations), silent
  fallbacks, plausibility of the headline numbers, and the coverage of the overruling list.

Report any gate that is missing or hollow as a finding.
