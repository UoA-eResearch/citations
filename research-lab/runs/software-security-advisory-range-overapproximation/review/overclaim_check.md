# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do npm and PyPI security advisories declare affected ranges that start too early? A code-presence test says three in four do, but a blind audit shows the test over-calls it; the defensible share is a quarter to a half | g4_audit.json | Supported |  |
| 2 | standfirst | 800 GitHub-reviewed npm and PyPI advisories with a fix commit (a seeded random sample of the 6,409 eligible) were checked release by release. | classes.csv; primary.json | Supported |  |
| 3 | standfirst | The test asked whether the code the fix removes or guards existed in each release inside the declared affected range, from the earliest onward. | classes.csv; primary.json | Supported |  |
| 4 | standfirst | A separate session then re-judged 60 of them from the code alone. | classes.csv; primary.json | Supported |  |
| 5 | standfirst | The plan was committed before any advisory, commit or package file was downloaded. | plan.md / git | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive; H2 Inconclusive.** The pipeline's counts would give Supported for both. | classes.csv; primary.json | Supported |  |
| 7 | verdict | The preregistered audit found that the pipeline's "over-approximated" label is right only a third of the time, so by the plan's rule its share is reported as unreliable. | g4_audit.json | Supported |  |
| 8 | verdict | **H1 (at least 25% of advisories declare a lower bound that starts before the vulnerable code existed): Inconclusive.** | classes.csv; primary.json | Supported |  |
| 9 | verdict | **Pipeline:** 308 of the 411 classified advisories are over-approximated (75%; Wilson 70.5% to 78.9%), and 103 are tight. | classes.csv; primary.json | Supported |  |
| 10 | verdict | Even counting every undetermined advisory as not over-approximated, that is 38.5% of all 800. | classes.csv; primary.json | Supported |  |
| 11 | verdict | **The audit:** a separate session judged 30 pipeline over-approximations and 30 tight cases from the fix diff and two releases, without the labels. | g4_audit.json | Supported |  |
| 12 | verdict | Of the 30 over-approximations, it confirmed 10 (33%), contradicted 8 and could not decide 12. | g4_audit.json | Supported |  |
| 13 | verdict | The plan requires 80%. | classes.csv; primary.json | Supported |  |
| 14 | verdict | Of the 30 tight cases, it confirmed 24. | g4_audit.json | Supported |  |
| 15 | verdict | The contradicted cases are the same flaw in code written differently in the earlier release: renamed, rewritten or moved. | g4_audit.json | Supported |  |
| 16 | verdict | Exact line signatures miss it, and the pipeline calls it absent. | classes.csv; primary.json | Supported |  |
| 17 | verdict | **Audit-calibrated range:** applying the audited fractions to all 308 gives 25% to 55% of classified advisories. | g4_audit.json | Supported |  |
| 18 | verdict | The bar of 25% is the bottom of that range. | classes.csv; primary.json | Supported |  |
| 19 | verdict | **Strict reading** (post hoc): the module the fix touches is missing altogether from the earliest in-range release (no file of the same name). | posthoc_strict.json | Supported |  |
| 20 | verdict | That holds for 142 of the 308, or 58% (52% to 64%) of strict plus tight. | posthoc_strict.json | Supported |  |
| 21 | verdict | The auditor contradicted none of the 14 audited strict cases, but could decide only 4 of them. | g4_audit.json | Supported |  |
| 22 | verdict | 49% of the sample is undetermined: no usable signature (79), no diff (10), or no release in which the signature matches (300). | classes.csv; primary.json | Supported |  |
| 23 | verdict | That is above the plan's 40% warning line, so any share rests on a minority of the sample. | classes.csv; primary.json | Supported |  |
| 24 | verdict | **H2 (correcting the lower bounds removes at least a third of affected version pairs, a factor of 1.5): Inconclusive.** | classes.csv; primary.json | Supported |  |
| 25 | verdict | **Pipeline:** 35,590 declared (version, advisory) pairs fall to 16,353, a factor of **2.18** (1.93 to 2.50). | classes.csv; primary.json | Supported |  |
| 26 | verdict | **Strict reading:** the factor is **1.35** (1.27 to 1.45), below the bar. | posthoc_strict.json | Supported |  |
| 27 | verdict | The pipeline figure rests on the classification the audit found unreliable. | g4_audit.json | Supported |  |
| 28 | verdict | **npm installs** (pipeline classes): 36% of current weekly downloads of versions inside declared ranges fall outside the corrected ranges. | classes.csv; primary.json | Supported |  |
| 29 | verdict | **What holds regardless of the audit.** | g4_audit.json | Supported |  |
| 30 | verdict | **"Introduced: 0" ranges drive the pattern.** 81% of sampled advisories declare every release affected. | classes.csv; primary.json | Supported |  |
| 31 | verdict | Of those classified, the pipeline flags 83% (280 of 338), against 38% (28 of 73) of explicit lower bounds. | classes.csv; primary.json | Supported |  |
| 32 | verdict | Where a lower bound starts too early, the gap is long: a median of 42 releases, or 3.1 years (pipeline classes). | classes.csv; primary.json | Supported |  |
| 33 | verdict | **Upper bounds:** in 35 of 693 checked advisories (5%), the vulnerable code is still present in the first release at or after the declared fixed version. | classes.csv; primary.json | Supported |  |
| 34 | verdict | "Present" calls are the reliable direction in the audit. | g4_audit.json | Supported |  |
| 35 | plain terms | When a security flaw is found in an open-source package, an advisory records which versions are affected. | classes.csv; primary.json | Supported |  |
| 36 | plain terms | Tools such as Dependabot then warn everyone who uses those versions. | classes.csv; primary.json | Supported |  |
| 37 | plain terms | If the advisory says "every version before the fix" when the flaw only arrived recently, users of old, safe versions get warnings they do not need. | classes.csv; primary.json | Supported |  |
| 38 | plain terms | We took 800 advisories for JavaScript (npm) and Python (PyPI) packages and checked, release by release, whether the code that the fix changed was actually there. | classes.csv; primary.json | Supported |  |
| 39 | plain terms | A simple automatic check said three in four advisories start their range too early. | classes.csv; primary.json | Supported |  |
| 40 | plain terms | But when a separate reviewer looked at a sample by hand, the automatic check's "too early" could be confirmed only a third of the time; in a quarter of cases the flaw was already there. | g4_audit.json | Supported |  |
| 41 | plain terms | Code that existed in an older form, renamed or moved, fooled it. | g4_audit.json | Supported |  |
| 42 | plain terms | So the true share is roughly a quarter to a half of the advisories we could check. | classes.csv; primary.json | Supported |  |
| 43 | plain terms | The clearest pattern is the default: four in five advisories say every version is affected, and those are the ones most often too broad. | classes.csv; primary.json | Supported |  |
| 44 | plain terms | A better check, one that recognises older forms of the same code, is needed before the extra warnings can be counted. | classes.csv; primary.json | Supported |  |
