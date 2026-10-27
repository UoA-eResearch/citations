# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | AI coding tools in the npm and PyPI supply chain: a fifth to a third of new releases carry AI-signed commits; download-weighted, dependency trees raise exposure about 1.6-fold, far short of the fivefold hypothesised; and AI-signed commits ship no faster | primary.json monthly + monthly_no_monorepos 21-37%; posthoc decomposition multiplier 1.61/1.58; H2 ratio 1.01 | Supported | title rewritten after review finding 1 |
| 2 | standfirst | The top 10,000 npm and the top 10,000 PyPI packages by downloads were traced to 13,134 GitHub repositories, 10,372 of them with commits since 2024 (5.3 million commits). | pipeline: 13,134 repos; 10,372 with commits since 2024; 5.3M commits | Supported |  |
| 3 | standfirst | Every commit was checked for an AI signature, and every release since June 2024 (423,181) was mapped to its commit range. | primary.json release_methods sum 423,181 | Supported |  |
| 4 | standfirst | Resolved dependency graphs come from deps.dev. | ledger S10 | Supported |  |
| 5 | standfirst | The plan and the attribution rules were committed before any data was downloaded. | git log: plan + attribution.py 22:43; first data after | Supported | provenance wording fixed (review 10) |
| 6 | standfirst | Revised after an independent review (D2: one bug fix, post hoc decompositions, a stratified two-labeller audit). | deviations.md D2 | Supported |  |
| 7 | verdict | **Verdict: H1 Refuted; H2 Refuted.** | primary.json verdicts | Supported |  |
| 8 | verdict | **H1 (download-weighted dependency exposure is at least 5× the share of packages that are themselves AI-flagged, and over 30% for npm): Refuted on both parts.** | plan.md H1 | Supported |  |
| 9 | verdict | **npm.** | heading | Supported |  |
| 10 | verdict | p = 21.6% of top packages' latest releases have an AI-signed commit in their release range. | primary.json npm p 0.2164 | Supported |  |
| 11 | verdict | This is a repository-level rate: it is 6.0% for packages whose repository hosts no other top package and 38.6% for packages in multi-package repositories. | posthoc_review.json denominators npm p_single 0.0601, p_multi 0.3855 | Exploratory-labelled | added (review 2) |
| 12 | verdict | The download-weighted probability that a top package's resolved tree contains such a release (P_w) is 22.3% (20.6–24.1%). | npm P_w 0.2228 (0.2058-0.2411) | Supported |  |
| 13 | verdict | R = P_w / p = 1.03 (0.95–1.11). | npm R 1.030 (0.951-1.114) | Supported |  |
| 14 | verdict | **PyPI.** p = 18.6%, P_w = 36.1% (31.3–41.5%), R = 1.94 (1.67–2.24). | primary.json pypi p 0.1857, P_w 0.3607 [0.3129,0.4151], R 1.942 [1.672,2.237] | Supported | D2 version fix |
| 15 | verdict | **R mixes two effects (post hoc).** P_w is download-weighted and p is not. | posthoc_review.json decomposition | Exploratory-labelled | added (review 1) |
| 16 | verdict | Heavily downloaded packages are less often flagged themselves: 13.8% (npm) and 22.8% (PyPI) download-weighted. | posthoc_review.json weighted_root_rate 0.1382 / 0.2283 | Exploratory-labelled | added |
| 17 | verdict | Trees then raise those rates about 1.6-fold: 1.61 (1.51–1.73) for npm and 1.58 (1.43–1.78) for PyPI. | posthoc_review.json tree_multiplier 1.612 [1.514,1.728], 1.58 [1.433,1.783] | Exploratory-labelled | added |
| 18 | verdict | The tree effect is real but far below fivefold. | posthoc_review.json multipliers ~1.6; primary.json R_ci upper < 5 | Exploratory-labelled | replaces 'do not multiply' |
| 19 | verdict | **The caveat is monorepos, and it lowers npm sharply.** | sensitivity no_monorepos npm p 0.060 vs 0.216 | Supported |  |
| 20 | verdict | The clones carry no file paths. | plan.md clone command --filter=tree:0 | Supported |  |
| 21 | verdict | So when one repository hosts many packages, a commit to any of them flags every sibling's release. | posthoc_review.json share_of_flagged_latest_from_multi 0.8555 | Supported |  |
| 22 | verdict | Without such packages, npm p is 6.0% and P_w 6.1%; PyPI p is 14.4% and P_w 29.4%. | primary.json sensitivity no_monorepos | Supported |  |
| 23 | verdict | Tag-only ranges give npm 14.3% / 14.9% and PyPI 11.7% / 25.2%. | primary.json sensitivity tag_only | Supported |  |
| 24 | verdict | **H2 (AI-signed commits reach a release at most half as fast as matched human commits): Refuted.** | primary.json H2 ratio_ci [0.991,1.110] lower > 0.5 | Supported |  |
| 25 | verdict | The median commit-to-release latency is 6.8 days for AI-signed commits against 6.7 for human commits matched in the same package within 14 days. | primary.json H2 medians 6.79 / 6.73 | Supported |  |
| 26 | verdict | The ratio is 1.01 (0.99–1.11). | H2 ratio 1.009 (0.987-1.109) | Supported |  |
| 27 | verdict | **Matching as the plan worded it** (per repository, each commit once, post hoc) gives 1.12 (1.05–1.19). | posthoc_review.json H2_extras plan_wording ratio 1.117 [1.050,1.186] | Exploratory-labelled | added (review 4) |
| 28 | verdict | AI-signed commits wait slightly longer. | posthoc_review.json plan_wording CI lower 1.05 > 1 | Exploratory-labelled | added |
| 29 | verdict | **The trend is steep.** | monthly commit shares | Supported |  |
| 30 | verdict | AI-signed commits were 0.1% of non-bot commits in npm repositories in March 2025 and 10.8% in September 2026; in PyPI repositories, 1.4% and 13.3%. | primary.json monthly commits share | Supported |  |
| 31 | verdict | In September 2026, 28% (npm) and 33% (PyPI) of active repositories had at least one (post hoc). | posthoc_review.json trend share_of_active_repos 0.2825 / 0.3272 | Exploratory-labelled | added (review 13) |
| 32 | verdict | The share of new releases containing at least one AI-signed commit rose from under 1% in January 2025 to 37% (npm) and 33% (PyPI) in September 2026. | primary.json releases_flagged_by_month | Supported |  |
| 33 | verdict | Without monorepo packages the September 2026 shares are 21% and 25%. | monthly_no_monorepos.json 0.2147 / 0.25 | Supported |  |
| 34 | verdict | Claude-model signatures (mostly Claude Code) are 68% of attributed commits, Copilot 13–16% and Cursor 4–10%. | primary.json agents_total; review finding 9 composition | Supported | was 'Claude Code signs' |
| 35 | verdict | **The detector is precise.** | precision_audit_strata.json all strata 1.0 | Supported |  |
| 36 | verdict | A stratified audit of 120 matches, weighted towards the riskier rules, was labelled by two blind labellers. | precision_audit_strata.json items 120; agreement 100% | Supported | added (review 6, G7) |
| 37 | verdict | Every match was a genuine AI signature, with 100% agreement. | precision_audit_strata.json; labeller A/B ai share 1.0 | Supported |  |
| 38 | verdict | Per-stratum 95% lower bounds are 0.69–0.86. | precision_audit_strata.json CP lower 0.692-0.863 | Supported |  |
| 39 | verdict | The detector is blind to unsigned use and misses about 3% of signed commits, so every share is a lower bound. | review/review.md finding 8 (reviewer scan, 400 repositories) | Supported | added |
| 40 | plain terms | Most software is assembled from thousands of free packages that other people maintain. | background | Supported |  |
| 41 | plain terms | AI coding tools, which write code and sometimes commit it on a developer's behalf, have spread fast. | definition; includes committed suggestions (deviations D2) | Supported | was 'agents ... on a developer's behalf' (review 7) |
| 42 | plain terms | Many leave a signature in the project history, such as a "Co-authored-by: Claude" line. | precision audit by_rule trailer 92 | Supported |  |
| 43 | plain terms | We looked at the 20,000 most-downloaded packages for JavaScript (npm) and Python (PyPI), and read every change made since 2024 to the nine in ten we could trace to a repository. - In September 2026, about one in ten changes carried an AI signature, up from almost none two years earlier. | report How it was done: 9,810 + 9,026 packages with repositories | Supported |  |
| 44 | plain terms | About a third of active projects had at least one. - Between a fifth and a third of new versions included at least one such change, depending on how packages that share a repository are counted. - These are minimum figures, because unsigned AI help leaves no trace. | posthoc_review.json trend 0.28 / 0.33; monthly_no_monorepos 21-25% vs 33-37% | Exploratory-labelled | added; two bullets joined by the extractor |
| 45 | plain terms | We expected the reach to multiply because packages depend on other packages. | plan.md H1a rationale | Supported |  |
| 46 | plain terms | Install one popular package and you pull in dozens of others, so a few AI-touched packages could end up in most installations. | plan.md H1a rationale (the hypothesis, not a finding) | Supported |  |
| 47 | plain terms | Counted fairly, by downloads on both sides, dependencies raised the reach about one and a half times, not the fivefold we expected. | posthoc_review.json tree_multiplier 1.61 / 1.58 | Exploratory-labelled | replaces 'essentially none ... double' (review 1) |
| 48 | plain terms | We also checked whether AI-written changes are rushed out faster than human ones. | plan.md H2 | Supported |  |
| 49 | plain terms | They are not: both take about a week to reach a release. | H2 pooled medians 6.8 vs 6.7 days | Supported |  |
| 50 | plain terms | Nothing here says AI-written code is less safe. | scope statement | Supported |  |
| 51 | plain terms | The study measures where it goes, not how good it is. | scope statement | Supported |  |
