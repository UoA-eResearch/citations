# Preregistration: do independent audits of SWE-bench Verified agree on which tasks are broken?

Lead: `ai-evaluation-science-swe-audit-concordance` (research-lab/leads.json). Written 2026-10-03 and committed to git
before any agreement statistic, prevalence comparison or detector output is computed.

## What has been seen before writing (disclosure)

- **File structure of every source,** and one example row of each.
- **Auto Benchmark Audit (ABA) counts.** The scout reported ABA's numbers of tasks with major findings, 21 in static
  mode and 36 in trajectory mode out of 500, for any category; they were computed from ABA's public data.
- **OpenAI's 2024 annotations.** The labels have not been tabulated within Verified.
- **Detector.** The code (`code/detector.py`) was debugged on the 22 astropy tasks in Verified:
  - It first flagged none.
  - Inspection of astropy-13033, whose test pins a new error message, showed two misses: implicit string
    concatenation across lines, and messages built with `.format()`. The literal rule was revised to join adjacent
    literals and to require only a shared 3-word run with the gold patch.
  - It then flags 1 of 22 astropy tasks.
  - No audit label was consulted while developing it.

Every later departure goes to `deviations.md` with a timestamp from `date`.

## 1. Question

Claims about how many SWE-bench Verified tasks are broken range from about 4% to 16% or more. Each audit is reported
on its own. Do the released per-task audits agree on which tasks have tests that reject valid solutions, and on how
many there are?

## 2. Label sources for the 500 Verified tasks

Flaw type A is tests too narrow, rejecting valid fixes.

| Code | Source | Flag rule |
|---|---|---|
| O | OpenAI 2024 ensembled annotations (`ensembled_annotations_public.csv`) | `false_negative` ≥ 1. Within Verified the scores were pre-filtered to 0 or 1, so 1 = "minor issue" in OpenAI's rubric. |
| AS | ABA static mode (`benchmark.json`) | evaluation-category major findings ≥ 1 |
| AT | ABA trajectory mode (same file) | evaluation-category major findings ≥ 1. Tasks without a trajectory audit are missing. |
| D | The deterministic spec-gap detector (`code/detector.py`, frozen at this commit) | score ≥ 1; problem statement only, hints not used |
| B | Behaviour: unsolved by all of the 30 submissions with the highest resolve rate on all 500 tasks (SWE-bench/experiments, `evaluation/verified/*/results/results.json`) | unsolved by all 30 |

**Flaw type U, underspecified problem statement (secondary).**

- O_U: `underspecified` ≥ 1.
- AS_U and AT_U: instruction-category major findings ≥ 1.

**Flaw type W, tests too broad (descriptive only).** UTBoost's 36 confirmed augmented-test instances that fall in
Verified.

## 3. Primary hypotheses and decision rules

**H1 (low agreement).** The median of the six pairwise Cohen's κ among O, AS, AT and D for flaw type A is below 0.20.

- **Interval.** A 95% CI for the median comes from a task bootstrap with 2,000 resamples.
- **Supported:** the median is < 0.20 and the CI's upper bound is < 0.40.
- **Contradicted:** the CI's lower bound is ≥ 0.20.
- **Inconclusive:** otherwise.

**H2 (prevalence disagreement).** The highest flagged share among O, AS, AT and D, divided by the lowest, exceeds 3.

- **Interval.** The same bootstrap gives a 95% CI for the ratio.
- **Supported:** the CI's lower bound is > 3.
- **Contradicted:** the CI's upper bound is < 3.
- **Inconclusive:** otherwise.
- **Zero prevalence.** If any source flags no task, the ratio is undefined; H2 is then reported as Supported only if
  another source flags at least 3% of tasks.

## 4. Secondary analyses (no verdicts)

- **Agreement within limits:**
  - Gwet's AC1 for all pairs;
  - κ restricted to the independent external pair types (O–AS, O–AT);
  - agreement of each source with B (behavioural), as odds ratios with Fisher exact CIs.
- **Within-audit reliability ceiling.** Fleiss' κ among OpenAI's three annotators on `false_negative` ≥ 2,
  over all 1,699 annotated instances (`samples_with_3_annotations_public.csv`).
- **Detector validation.** AUROC of the detector score against OpenAI's consensus `false_negative` (≥ 2 vs < 2) on
  the 1,699 annotated instances. Repositories are at each instance's base_commit; the issue text comes from the full
  SWE-bench test split. CIs come from a bootstrap.
- **Latent prevalence.** A Dawid-Skene latent-class model on O, AS, AT, D and B gives the estimated true prevalence
  and each source's sensitivity and specificity, with a sensitivity analysis that drops the AS–AT pair (same tool).
- **Leaderboard consequences.** Kendall's τ between the top-30 ranking on all 500 tasks and the ranking after
  removing each source's flagged tasks, plus the spread of mean scores.
- **Flaw type U.** The same pairwise κ, for underspecified statements.
- **Detector with hints.** The detector re-run with hints added to the issue text.

## 5. Threats (fixed now)

- **Different definitions.** The audits define flaws differently, so low κ can mean construct mismatch rather than
  unreliability; AC1 and the latent-class model help separate the two.
- **Restricted OpenAI labels.** OpenAI's labels within Verified are restricted to 0 or 1, which limits agreement by
  construction.
- **Not independent.** ABA's static and trajectory modes are one tool. The detector is this project's own.
- **Unsolved does not mean broken.** The behavioural flag also captures genuinely hard tasks.

## 6. Review and reporting

- An independent reviewer agent checks code and results before any verdict.
- The report opens with "In plain terms".
- The cross-audit label matrix and the detector code are released.
