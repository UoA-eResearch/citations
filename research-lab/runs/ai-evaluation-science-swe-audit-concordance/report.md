# How many SWE-bench Verified tasks are broken, and do the audits agree?

*A preregistered cross-audit comparison of OpenAI's 2024 annotations, Auto Benchmark Audit (static and trajectory modes), a new deterministic spec-gap detector and leaderboard behaviour on the 500 SWE-bench Verified tasks*

Run directory: `research-lab/runs/ai-evaluation-science-swe-audit-concordance` · Preregistration: [`plan.md`](plan.md) ·
Every departure from it: [`deviations.md`](deviations.md) · 3 October 2026, revised after independent review

## In plain terms

SWE-bench Verified is the best-known test of whether AI systems can fix real software bugs. Each of its 500 tasks
comes with tests that decide whether a fix is correct. If a test also rejects correct fixes, for example by demanding
a function name the bug report never mentioned, the task is "broken". Published estimates of how many are broken range
from a few percent to over 16%.

We lined up every released task-by-task audit and asked whether they agree.

**What we found.**

- **Tight checks flag about 1 in 50.** Three strict checks each flag about 2% of tasks (10–12 of 500): two modes of an
  automated audit tool, and a simple new detector we wrote. They only partly agree on which ones. All three flag the
  same 3 tasks, and any two share 3–4.
- **OpenAI's much larger figure measures something else.** OpenAI's 2024 labels mark 39% of Verified tasks. That count
  includes any task where a single one of three reviewers noted a *minor* concern, and OpenAI's own reviewers rarely
  agreed with each other about those. Requiring two of three reviewers to agree drops it to 11%; requiring all three
  drops it to 1.6%.
- **Removing flagged tasks barely changes the leaderboard** for the strict checks. Removing OpenAI's broader set
  reshuffles it somewhat more than removing random tasks would.

So the disagreement about "how many tasks are broken" is mostly a disagreement about what counts as broken, not about
the same thing measured differently.

## What was done

The plan and the detector were committed (8f434e0) before any agreement statistic was computed.

**Label sources** for "tests reject valid fixes":

| Code | Source | Flagged |
|---|---|---|
| O | OpenAI 2024 ensembled annotations: false_negative ≥ 1 within Verified, i.e. any annotator noted a minor issue | 197 (39.4%) |
| AS | Auto Benchmark Audit (ABA) static mode, at least one evaluation-category major finding | 10 (2.0%) |
| AT | ABA trajectory mode, the same rule | 12 (2.4%) |
| D | Our deterministic, execution-free spec-gap detector. It flags names or messages that the tests require, that the gold patch introduces, and that appear neither in the issue nor in the repository. | 12 (2.4%) |
| B | Behaviour: unsolved by every one of the 30 best leaderboard submissions (175 submissions; corrected in D1) | 32 (6.4%) |

**Hypotheses.**

- **H1:** the median of the six pairwise Cohen's κ among O, AS, AT and D is below 0.20.
- **H2:** the highest prevalence among those four sources is more than 3 times the lowest.

Both use 2,000-resample task bootstraps.

## Preregistered results

| | Estimate | 95% CI | Verdict |
|---|---|---|---|
| **H1: median pairwise κ (O, AS, AT, D)** | **0.15** | **0.02–0.26** | **Supported** |
| **H2: max / min prevalence** | **19.7** | **14.2–48.0** | **Supported** |

Both verdicts follow the preregistered rules. But neither number should be read on its own, for two reasons.

**The median κ is not a "typical" agreement.** The six pairs form two clusters:

| Pair | κ | 95% CI | Flagged by each | Both |
|---|---|---|---|---|
| O – AS | 0.04 | 0.01–0.08 | 197 / 10 | 8 |
| O – AT | 0.03 | 0.00–0.07 | 197 / 12 | 8 |
| O – D | 0.04 | 0.01–0.08 | 197 / 12 | 9 |
| AS – AT | 0.35 | 0.09–0.60 | 10 / 12 | 4 |
| AS – D | 0.26 | −0.02–0.49 | 10 / 12 | 3 |
| AT – D | 0.32 | 0.07–0.56 | 12 / 12 | 4 |

- The three strict sources agree only fairly with each other. O agrees with none of them beyond chance.
- The preregistered median, 0.15, falls in the gap between the two clusters.
- Gwet's AC1 (0.97 among AS, AT and D) is what two *independent* raters would also get at 2% prevalence (about
  0.95–0.97), so it carries no information here.

**H2 depends on OpenAI's threshold.** Within Verified, OpenAI's label can only be 0 or 1, and "1" means at least one of
three annotators noted a minor issue. OpenAI's own annotators agree on that only slightly (Fleiss κ 0.12 within
Verified).

| How O is defined | O flags | Max / min ratio | H2 under the plan's rule | Median κ (H1) |
|---|---|---|---|---|
| Any annotator (preregistered) | 39.4% | 19.7 (14.2–48.0) | Supported | 0.15 |
| Two of three annotators | 10.6% | 5.3 (3.6–12.8) | Supported | 0.17 |
| All three annotators | 1.6% | 1.5 (1.2–4.8) | Inconclusive | 0.18 |

When OpenAI's reviewers all agree, the four sources flag 1.6–2.4% of tasks. H1 holds under every definition.

## The detector

**Validation.** On OpenAI's full 1,699 annotated instances, the detector flags 17% of tasks.

- 94% of the tasks it flags were judged problematic by OpenAI's annotator consensus (false_negative ≥ 2), against a
  base rate of 61%. That is a likelihood ratio of 9.8.
- It catches only 27% of the problematic tasks.
- The preregistered AUROC of 0.62 is simply (sensitivity + specificity) / 2, because 83% of scores are zero.

**A manual check of its 12 flags in Verified** (D3, by the independent reviewer):

- **6 are real spec gaps,** such as tests requiring a new `edit_only` argument or an exact new error message.
- **6 are artefacts.** For example, a zero-width space in a bug report hid an exact match, and messages that already
  existed in the repository with a different number.
- **Rule by rule:** the identifier rule was right 5 of 5 times, the message-literal rule 1 of 7.
- **A normalised variant** (zero-width characters removed, backslashes unescaped) removes 2 artefacts and leaves its
  agreement with ABA unchanged: κ 0.29 and 0.35.

## How many are really broken?

A latent-class (Dawid–Skene) model combines all five sources. It puts the share of tasks with tests that reject valid
fixes at about **2%**, with a bootstrap 95% CI of 0.7–8% and a range of 1–4% across reasonable choices of sources.

The model is weakly identified, and two of its inputs share a cause: ABA's trajectory mode and the behavioural label
both come from agent runs. So this is an order of magnitude, not a precise figure. Nine tasks are posterior-positive,
and three are flagged by every source: pylint-4551, pylint-4604 and pytest-10356.

## Does it matter for the leaderboard?

We took the top 30 submissions, removed each source's flagged tasks, and compared the new ranking with the original
using Kendall's τ. We also compared it with removing the same number of random tasks.

| Tasks removed | Count | τ | τ when as many random tasks are removed (median; 5th percentile) |
|---|---|---|---|
| OpenAI (O) | 197 | 0.67 | 0.78; 0.70 |
| ABA static | 10 | 0.95 | 0.98; 0.95 |
| ABA trajectory | 12 | 0.97 | 0.97; 0.95 |
| Detector | 12 | 0.98 | 0.97; 0.95 |

- Removing the strict audits' tasks changes the ranking no more than removing random tasks would.
- Removing OpenAI's broader set reorders it somewhat more than chance (τ 0.67 against a random 5th percentile of 0.70).
- The behavioural flag cannot change rankings by construction, because no top-30 system solves those tasks.

## Limitations

- **The audits measure different things.** ABA's "evaluation major" also includes tests that are too broad and
  harness defects (D4). OpenAI's within-Verified label is a minor-issue flag. Low agreement partly reflects these
  construct differences.
- **Rare flags make κ unstable.** With 10–12 flags per source, the pairwise CIs span roughly 0 to 0.6.
- **The detector is ours.** It is high-precision, low-recall and narrow in scope. Its message rule needs the fixes
  noted above.
- **The behavioural label was first built incorrectly,** from 135 of 182 submissions. It is corrected here (D1), and
  H1 and H2 do not depend on it.
- **OpenAI's 2026 audit,** which reports at least 59% flawed tests in a 28% subset, has no released per-task list, so
  it could not be compared task by task.

## Independent review

An independent reviewer reproduced both preregistered verdicts and judged the study "fix first". The review:

- caught the incomplete leaderboard data (D1);
- hand-checked every detector flag (D3);
- showed that H2 rests on OpenAI's any-annotator threshold, that the median κ falls between two clusters, and that
  AC1 is uninformative at this prevalence;
- required a random-removal baseline for the leaderboard analysis.

All are included above. The code is in `code/review_checks.py`.
