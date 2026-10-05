# Self-audit protocol for the methodology paper

Written 2026-10-06 and committed before any audit measure below has been computed and before any coder has seen the
codebook.

**What the author already knows.** The author of this protocol is the AI agent that executed every study, so it
already knows a great deal about them. For that reason:

- the judgement-based measures (B, C and part of D) are coded by **two independent agents of different models**, which
  see only the files named here;
- the automated measures (A, D, E and F) are produced by code committed with this protocol.

**Known before writing:**

- the verdict tags of the 17 reported studies (3 Supported, 3 Refuted, 2 Unsupported, 8 Inconclusive, 1 Pending);
- that 13 of 19 plans contain an explicit disclosure section (from a regex in the survey, `related-efforts.md`);
- that all 161 arXiv IDs in `leads.json` resolve.

## Units

**Studies.** The 19 run directories under `research-lab/runs/`:

- 17 reported studies;
- 2 in progress (quantum peaked circuits, formal-math vacuity).

The in-progress studies enter only measure A (preregistration timing) and the protocol description.

**Deviation entries.** Every numbered entry (D1, D2, D27c, …) in each `deviations.md`.

## A. Preregistration timing (automated: `paper/code/audit_git.py`)

For each run, from git history:

- t_plan: the first commit adding `plan.md`;
- t_out: the first commit adding any file under `results/`, or `report.md`;
- every later commit that touches `plan.md`, with its diff size.

A run passes if t_plan < t_out. Later edits to the plan are listed and checked against `deviations.md` by the coders
(measure B, item 5).

## B. Deviation coding (two independent coder agents; codebook below)

Each deviation entry gets the following codes.

1. **Category** (one primary):
   - C1 bug or numerical fix;
   - C2 data problem (availability, quality, definitions);
   - C3 change to the primary analysis specification (estimator, sample, outcome, test);
   - C4 change to the decision rule or its thresholds;
   - C5 added secondary or sensitivity analysis;
   - C6 environment, compute or logistics;
   - C7 clarification, disclosure or documentation only;
   - C8 withdrawal or correction of a claim.
2. **Trigger**:
   - T1 the executor during the work;
   - T2 a validation or positive-control check;
   - T3 the independent reviewer;
   - T4 an external event or data release.
3. **Timing**:
   - before the primary outcome was seen;
   - after it;
   - unclear.
4. **Verdict relevance**: could this deviation plausibly change the preregistered verdict? Yes, no or unclear.
5. **Plan edits** (per study, not per entry): is every post-commit edit to `plan.md` from measure A disclosed in
   `deviations.md`? Yes, no, or none.

## C. Effects of independent review (same two coders, per reported study)

From the report's review section, `deviations.md` and the git log of `report.md`, the coders record:

- the review's recommendation (e.g. FIX FIRST, accept with changes, accept);
- whether a confirmation pass was run;
- the number of distinct substantive issues raised;
- the issue categories:
  - R1 computational or numerical error;
  - R2 analysis or model error, including local optima;
  - R3 leakage or blinding;
  - R4 overclaiming or wording;
  - R5 missing analysis or robustness check;
  - R6 documentation;
- whether the headline estimate changed after review;
- whether the verdict changed after review (pre-review verdict → final verdict, where it can be determined).

## D. Traceability of numbers in reports (automated: `paper/code/audit_numbers.py`, plus coder sample)

**Automated step.** Extract every numeric token from each `report.md`, excluding:

- dates and years (1900-2100 standing alone);
- section, figure, deviation and footnote labels;
- arXiv IDs, DOIs and commit hashes;
- numbers inside URLs or code spans.

A number is **traced** if the same value, at the precision it is printed, appears in any file under the run's
`results/` (csv, json, txt or md), or in `plan.md` or `deviations.md`. Matching is on the rounded string, and as a
percentage where the source holds a proportion. The script reports the traced fraction per report.

**Coder sample.** A seeded random sample of up to 10 untraced numbers per report is classified by both coders:

- U1 arithmetic derived from traced numbers;
- U2 from cited literature, data documentation or the lead;
- U3 a design parameter (sample size, threshold);
- U4 not traceable;
- U5 inconsistent with the results.

## E. References (automated: `paper/code/audit_refs.py`)

Every arXiv ID and DOI in all plans, reports and `leads.json` is resolved against the arXiv API and doi.org. The
script reports the number that resolve.

## F. Scout calibration (automated: `paper/code/audit_calibration.py`)

**Wall time.** Each lead's `est_wall_time` is compared with the actual wall time, measured as the first commit in the
run directory to the final report commit. The result is reported as a ratio.

**Verdicts by scouting.** Verdicts are tabulated against the scout value, cost and feasibility scores.

**Power.** Where a study states both an assumed effect and a minimum detectable effect, the coders extract them in
measure C.

## Agreement and adjudication

- Agreement is Cohen's κ for the categorical codes, reported per code family.
- Disagreements are adjudicated by the executing agent with a one-line logged reason (`paper/audit/adjudication.csv`).
- Both coders' raw outputs are committed unchanged.

## Analysis

This is a descriptive case series with no hypothesis tests. The paper reports:

- counts and proportions with Wilson intervals;
- measure A pass rates;
- the distributions in B and C;
- traced fractions in D, and the classification of the untraced sample;
- the resolution rate in E;
- the calibration ratios in F.

Where any measure reflects badly on the lab, it is reported in the paper's main text, not an appendix.
