# Deviations and implementation details

The plan and the frozen detector were committed in 8f434e0 at 2026-10-03 22:50 NZDT, before any agreement statistic.
Entries are timestamped with `date`.

## D1. Behavioural label B was first built from 135 of 182 submissions (2026-10-03 23:59 NZDT, found in review)

- **What went wrong.** The sparse checkout of SWE-bench/experiments excluded per_instance_details.json, the file in
  which the 47 mini-SWE-agent submissions store their per-task results. labels.py now reads both formats: 40 files
  parse, and 7 are empty and are treated as missing.
- **Effect.**
  - B is now built from 175 submissions, and 8 of the mini submissions enter the top 30. B has 32 tasks, down from
    34.
  - Fisher p-values: AS vs B 0.025 -> 0.129; O vs B 0.019 -> 0.060.
  - Dawid-Skene prevalence: 2.2% -> 1.8%.
  - H1 and H2 do not use B and are unchanged.
- **Where the original outputs are.** results/tables/v1_135subs/.
- **Tie at the top-30 cut.** 30th and 31st place tie at 0.718. The cut follows sort order. Swapping the 31st
  submission in leaves B identical (32 tasks).

## D2. Post-hoc analyses requested by the review (2026-10-03 23:59 NZDT; code/review_checks.py)

**O-definition ladder** (results/tables/review_O_ladder.csv).

- **The preregistered O equals the maximum over OpenAI's three annotators.** Within Verified no annotator gave >= 2,
  so O = 1 means at least one annotator noted a minor issue.

| O definition | O prevalence | Median kappa | Ratio (95% CI) | H2 under the plan's rule |
|---|---|---|---|---|
| Any annotator (preregistered) | 39.4% | 0.150 | 19.7 (14.2-48.0) | Supported |
| Majority, >= 2 of 3 | 10.6% | 0.172 | 5.3 (3.6-12.8) | Supported |
| Unanimous | 1.6% | 0.176 | 1.5 (1.2-4.8) | Inconclusive |

- **Fleiss kappa among OpenAI's annotators.** Within Verified at fn >= 1 it is 0.115. Over all 1,699 instances it is
  0.364 at fn >= 1, 0.410 at fn >= 2 and 0.223 at fn >= 3.

**Per-pair kappa with bootstrap CIs, and an independence baseline for AC1** (results/tables/review_pairs.csv).

- The six kappas form two clusters. O against everything is 0.03-0.04; AS, AT and D among themselves are 0.26-0.35.
  The preregistered median, 0.15, falls in the gap between them.
- At about 2% prevalence, two independent raters give AC1 of about 0.95-0.97. The observed AC1 of 0.97 is therefore
  at chance level and is not evidence of agreement.
- Raw overlaps: AS and AT share 4 tasks, AS and D 3, AT and D 4. All three share 3 tasks (pylint-4551, pylint-4604,
  pytest-10356), and their union is 26 tasks.

**Detector validation as a binary flag.** On the 1,699 annotated instances, sensitivity is 0.27 and specificity 0.97,
with PPV 0.94 against a base rate of 0.61. The positive likelihood ratio is 9.8. AUROC 0.62 is (sens + spec) / 2,
because 83% of scores are 0.

**Dawid-Skene.** Prevalence by rater set ranges from 1.1% to 3.9%. The bootstrap 95% CI with all five raters is
0.7-8.1%. AT and B are not conditionally independent: ABA's trajectory mode uses agent runs, as B does. The
posterior-positive tasks are listed in review_posterior_positive.csv.

**Leaderboard null: random removal of the same number of tasks** (results/tables/review_leaderboard.csv).

- Removing O's tasks gives tau 0.67, against a random median of 0.78 and 5th percentile of 0.70 (one-sided p about
  0.02). With the original 135-submission top 30 it was 0.834 against a random median of 0.826. The result is post hoc,
  one of four comparisons, and fragile.
- AS, AT and D are indistinguishable from random removal.
- B's tau = 1 is tautological, because no top-30 submission solves a B task.

## D3. Detector spot check and normalised variant (2026-10-03 23:59 NZDT, post hoc)

The review hand-classified the detector's 12 Verified flags.

**Real spec gaps (6):**

- astropy-13033: the test pins a newly worded error message.
- django-14725: the edit_only keyword.
- pylint-4551: get_annotation and infer_node.
- pylint-4604: IS_PYPY.
- pylint-4661: appdirs.user_cache_dir.
- pytest-10356: consider_mro.

**Artefacts (6):**

- django-16145: a zero-width space in the issue text blocks the substring match.
- sympy-18763: the issue shows doubled backslashes.
- django-13195: a format template whose only novelty is a test path.
- django-13821: the message already exists in the repo; the test only substitutes a version.
- django-14580: the expected output is composed from strings that are in the issue.
- django-15103: the natural output once a field is dropped, counted twice.

**What this means for the detector.**

- The identifier rule was 5 of 5 correct; the literal rule was 1 of 7.
- A post-hoc variant D' normalises the text: it removes zero-width characters, unescapes doubled backslashes and
  collapses whitespace. It drops django-16145 and sympy-18763; its prevalence is 2.0% and its kappa with AS and AT is
  0.29 and 0.35.
- The preregistered numbers use the frozen detector.

## D4. Construct notes (2026-10-03 23:59 NZDT)

- **ABA "evaluation major" is broader than "tests too narrow".** Of AS's 10 flags, the review classed django-7530 as
  tests too broad, django-10097 and django-12209 as harness defects (malformed FAIL_TO_PASS lists), and astropy-7606
  (AT) as a PASS_TO_PASS test-id mismatch.
- **UTBoost.** It has 36 confirmed instances, of which 26 are in Verified (the plan said 36).
- **No AT values are missing.** has_trajectory_audit is true for all 500 tasks, so the AT missing rule never applied.
