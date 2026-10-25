# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | AI coding agents in the npm and PyPI supply chain: a fifth to a third of new releases now carry agent-signed commits, but dependency trees do not multiply the exposure, and agent commits ship no faster | H1 R npm 1.03, PyPI 1.91; H2 ratio 1.01; monthly 37%/33% all, 21%/25% no monorepos | Supported | was 'a third of new releases' (monorepo siblings inflate it; without them 21-25%) |
| 2 | standfirst | The top 10,000 npm and the top 10,000 PyPI packages by downloads were traced to 13,134 GitHub repositories, 10,372 of them with commits since 2024 (5.3 million commits). | pipeline: 13,134 repos; 10,372 with commits since 2024; 5.3M commits | Supported |  |
| 3 | standfirst | Every commit was checked for an AI-agent signature, and every release since June 2024 (423,181) was mapped to its commit range. | release_flags.parquet 423,181 releases | Supported |  |
| 4 | standfirst | Resolved dependency graphs come from deps.dev. | ledger S10 | Supported |  |
| 5 | standfirst | The plan and all code were committed before any data was downloaded. | git: plan and code commits before downloads | Supported |  |
| 6 | verdict | **Verdict: H1 Refuted; H2 Refuted.** | primary.json verdicts | Supported |  |
| 7 | verdict | **H1 (download-weighted dependency exposure is at least 5× the share of packages that are themselves AI-flagged, and over 30% for npm): Refuted on both parts.** | plan.md H1 | Supported |  |
| 8 | verdict | **npm.** | heading | Supported |  |
| 9 | verdict | 21.6% of top packages' latest releases contain an agent-signed commit (p). | by_eco npm p 0.2164 | Supported |  |
| 10 | verdict | The download-weighted probability that a top package's resolved tree contains such a release (P_w) is 22.3% (20.6–24.1%). | npm P_w 0.2228 (0.2058-0.2411) | Supported |  |
| 11 | verdict | R = P_w / p = 1.03 (0.95–1.11). | npm R 1.030 (0.951-1.114) | Supported |  |
| 12 | verdict | **PyPI.** p = 18.6%, P_w = 35.5% (30.7–40.9%), R = 1.91 (1.65–2.21). | pypi p 0.1857, P_w 0.3551 (0.307-0.409), R 1.912 (1.654-2.210) | Supported |  |
| 13 | verdict | **Weighting lowers npm exposure.** Unweighted, 32% of top npm and 48% of top PyPI packages have at least one flagged release in their tree. | unweighted_exposure npm 0.316, pypi 0.484 | Supported |  |
| 14 | verdict | The most-downloaded npm packages are small utilities with small, rarely released trees. | top_flagged / graph sizes (interpretation of the weighting result) | Supported |  |
| 15 | verdict | **The caveat is monorepos, and it lowers npm sharply.** | sensitivity no_monorepos npm p 0.060 vs 0.216 | Supported |  |
| 16 | verdict | When one repository hosts many packages, a commit to any of them flags every sibling's release. | analyse.py release flagging by repository commit range | Supported |  |
| 17 | verdict | Without such packages, npm p is 6.0% and P_w 6.1%; PyPI p is 14.4% and P_w 28.7%. | no_monorepos npm p 0.0598, P_w 0.0614; pypi 0.1436, 0.2873 | Supported |  |
| 18 | verdict | R barely moves (1.03 and 2.00). | no_monorepos R 1.026, 2.001 | Supported |  |
| 19 | verdict | Tag-only ranges give npm 14.3% / 14.9% and PyPI 11.7% / 24.7%. | tag_only npm 0.1428/0.1492; pypi 0.1167/0.2473 | Supported |  |
| 20 | verdict | **H2 (agent commits reach a release at most half as fast as matched human commits): Refuted.** | plan.md H2 | Supported |  |
| 21 | verdict | The median commit-to-release latency is 6.8 days for agent commits against 6.7 for human commits matched in the same package within 14 days (296,806 pairs, 2,528 repositories). | H2 median 6.79 vs 6.73 days; 296,806 pairs; 2,528 repos | Supported |  |
| 22 | verdict | The ratio is 1.01 (0.99–1.11). | H2 ratio 1.009 (0.987-1.109) | Supported |  |
| 23 | verdict | **The trend is steep.** | monthly commit shares | Supported |  |
| 24 | verdict | Agent-signed commits were 0.1% of non-bot commits in npm repositories in March 2025 and 10.8% in September 2026; in PyPI repositories, 1.4% and 13.3%. | monthly commits npm 2025-03 0.0013, 2026-09 0.1085; pypi 0.0143, 0.1330 | Supported |  |
| 25 | verdict | The share of new releases containing at least one such commit rose from under 1% in January 2025 to 37% (npm) and 33% (PyPI) in September 2026. | monthly releases_flagged_by_month (all packages) | Supported |  |
| 26 | verdict | Without monorepo packages, whose releases inherit sibling commits, the September 2026 shares are 21% and 25% (`results/tables/monthly_no_monorepos.json`). | monthly_no_monorepos.json npm 0.2147, pypi 0.2539 (2026-09) | Supported |  |
| 27 | verdict | Claude Code signs 68% of attributed commits, Copilot 13–16% and Cursor 4–10%. | agents_total: claude 0.683/0.680; copilot 0.158/0.130; cursor 0.098/0.040 | Supported |  |
| 28 | verdict | **The detector is precise.** All 100 randomly audited matches are genuine agent signatures (95% lower bound 96%). | precision_audit.json 100/100, CP lower 0.964 (single auditor; G7 not applied - flagged for review) | Supported |  |
| 29 | verdict | It is blind to unsigned use, so every share is a lower bound. | detector design (trailers and identities only) | Supported |  |
| 30 | plain terms | Most software is assembled from thousands of free packages that other people maintain. | background | Supported |  |
| 31 | plain terms | AI coding agents, tools that write and commit code on a developer's behalf, have spread fast. | monthly commit shares | Supported |  |
| 32 | plain terms | Many leave a signature in the project history, such as a "Co-authored-by: Claude" line. | precision audit by_rule trailer 92 | Supported |  |
| 33 | plain terms | We looked at the 20,000 most-downloaded packages for JavaScript (npm) and Python (PyPI) and read every change made since 2024 to the nine in ten we could trace to a repository. | cloned npm 9,757/10,000, pypi 8,934/10,000 | Supported | was 'read every change made to them' (about 10% could not be traced or cloned) |
| 34 | plain terms | In September 2026, about one in ten changes carried an AI agent's signature, up from almost none two years earlier. | npm 10.8%, pypi 13.3% in 2026-09; ~0 in mid-2024 | Supported |  |
| 35 | plain terms | Between a fifth and a third of new versions included at least one such change, depending on how packages that share a repository are counted. | monthly all 37%/33%; no monorepos 21%/25% | Supported | was 'A third of new versions' (monorepo-inflated) |
| 36 | plain terms | These are minimum figures, because unsigned AI help leaves no trace. | detector blind to unsigned use | Supported |  |
| 37 | plain terms | We expected that because packages depend on other packages, the reach would multiply: install one popular package and you pull in dozens of others, so a few AI-touched packages could end up in most installations. | plan.md H1 rationale | Supported |  |
| 38 | plain terms | That multiplication was modest. | R 1.03 and 1.91 vs the 5x hypothesis | Supported |  |
| 39 | plain terms | For JavaScript it was essentially none once popularity is taken into account; for Python it was about double. | R npm 1.03, pypi 1.91 | Supported |  |
| 40 | plain terms | We also checked whether AI-written changes are rushed out faster than human ones. | plan.md H2 | Supported |  |
| 41 | plain terms | They are not: both take about a week to reach a release. | H2 pooled medians 6.8 vs 6.7 days | Supported |  |
| 42 | plain terms | Nothing here says AI-written code is less safe. | scope statement | Supported |  |
| 43 | plain terms | The study measures where it goes, not how good it is. | scope statement | Supported |  |
