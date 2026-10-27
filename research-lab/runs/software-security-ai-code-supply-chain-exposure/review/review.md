# Independent review: software-security-ai-code-supply-chain-exposure

Reviewer: Claude (Fable 5.1), 2026-10-27. Read-only on the study; scripts and outputs in `review/reviewer_checks/`
(`check_attribution.py`, `scan_false_negatives.py`, `check_ranges_exposure.py`, `check_latency.py`, `check_tags.py`,
with their `.json`/`.out` results). No commit text or personal names are stored there.

## Verdict: fix first (no preregistered verdict changes)

Both preregistered verdicts survive every check I ran: H1 is Refuted whichever way exposure is decomposed, and H2 is
Refuted under the study's matching and under the plan's own wording. The provenance chain is clean (plan and
attribution rules committed 22:43, pipeline code 22:47, D1 23:13, first flags 00:47 the next day; six randomly chosen
"inactive" repositories confirmed on GitHub as having no commits since 2024). What must be fixed before publication is
the interpretation and several reported numbers:

- the title and plain-terms claim that dependency trees "do not multiply the exposure" rests on R = P_w / p, which
  divides a download-weighted quantity by an unweighted one; like for like, trees multiply the weighted root rate by
  about 1.6 in both ecosystems (finding 1);
- npm's p = 21.6% is 86% monorepo-derived and is presented as a package-level rate (finding 2);
- H2's "296,806 pairs" are 89,774 distinct agent commits counted 3.3 times across sibling packages, 80% of pairs are
  in the same release as their partner, and the plan's own matching gives a ratio of 1.12, not 1.01 (finding 4);
- the "few hubs" explanation of PyPI exposure is contradicted by the data (finding 5);
- the precision audit artefact cannot support its 100/100 (finding 6);
- two silent coverage losses are unreported: 5.4% of releases have an empty range, and 10% of in-set PyPI tree nodes
  carry a deps.dev-padded version that can never match a release (findings 3 and 11; immaterial to the verdicts,
  but G2 asks for them to be counted);
- the trend sentences describe a pooled commit stream in which 69% of active repositories had no agent commit in
  September 2026 and agents' own repositories dominate several per-agent series (finding 13).

None of these needs new data; all need new numbers in `results/` and rewritten text.

## Findings

### 1. R conflates download weighting with tree amplification; the title's central claim is not what the data show (major)

`analyse.py:66-70` computes p over cloned packages (unweighted) and P_w over roots with a graph (download-weighted),
then R = P_w / p. The two differ in weighting as well as in tree inclusion, so R ≈ 1 for npm does not mean trees add
nothing. Decomposing P_w (`ranges_exposure.json`, `npm`/`pypi` blocks):

| | npm | PyPI |
|---|---|---|
| download-weighted share of roots whose own latest release is flagged | 13.8% | 22.8% |
| P_w (root or any node flagged) | 22.3% | 35.5% |
| of which root unflagged, tree flagged | 8.5 pts | 13.1 pts |
| like-for-like tree multiplier (P_w / weighted root rate) | 1.61 | 1.56 |
| unweighted: root flagged → any node flagged | 20.4% → 31.6% (1.55×) | 16.0% → 48.4% (3.0×) |

So in npm, weighting lowers the root rate (21.6% → 13.8%, because heavily downloaded packages are less often
flagged) and trees raise it back (13.8% → 22.3%); R ≈ 1 is the product of these two opposite effects, not an
absence of amplification. The preregistered H1a (R ≥ 5) is still Refuted (1.6 ≪ 5), but:

- title: "dependency trees do not multiply the exposure" → "dependency trees multiply the exposure by about 1.6,
  far below the fivefold hypothesised";
- plain terms line 52-53: "For JavaScript it was essentially none once popularity is taken into account; for Python
  it was about double" is wrong; both are about 1.6× on a like-for-like weighted basis (PyPI 3× unweighted);
- "What this does and does not show" lines 139-142 likewise;
- add the decomposition table to Results, and say in Methods that R mixes weighting with tree inclusion (it is the
  preregistered statistic, so keep it, but do not interpret it as the tree effect).

### 2. npm's 21.6% is a repository-level rate: 86% of flagged latest releases are in multi-package repositories (major)

`ranges_exposure.json` → `npm.share_of_flagged_latest_from_mono` = 0.856; p is 38.5% for the 4,688 npm packages
whose repository hosts another top package and 6.0% for the rest. The twelve repositories contributing most flagged
latest releases are DefinitelyTyped (120, all `@types/*`, no tags, date fallback), react-spectrum (107), expo (84),
opentelemetry-js-contrib and zag (44 each). Excluding the top five repositories alone lowers p to 18.8% (PyPI 16.0%).
Because the clones are `--filter=tree:0`, no file path is available, so whether a monorepo commit touched the
released package is unknowable here; the flag means "the repository had an agent-signed commit between this
package's releases". The report says this in the caveat bullet, but the verdict bullets and the standfirst present
21.6% as "top packages' latest releases contain an agent-signed commit".

Related denominators that should be stated (same file):
- 2,864 npm and 1,884 PyPI cloned packages have no release since 2024-06-01 and sit in p's denominator as unflagged
  by construction (`cloned_latest_not_in_F_reasons`); among packages that did release in the window, p is 30.9%
  (npm) and 24.0% (PyPI) (`p_among_cloned_with_latest_in_window`);
- flag probability rises with range size: 5.8% for ranges of 1-5 commits, 27% for 20-100, 42% for 100-500, 76% for
  the 1,207 releases whose range exceeds 2,000 commits (`flag_rate_by_n_commits_bucket`). Big ranges are monorepo
  ranges and date-fallback ranges, which is where the 22% comes from.

Fix: lead with the pair "6% of single-package npm packages, 39% of packages in multi-package repositories (repository
level)", or present p as a 6-22% range with the mechanism; report p among packages that released in the window; make
the no-monorepo figure the headline for npm (the plan's secondary 3 exists for exactly this). The sensitivity's
"drop" (siblings unflagged in trees, `analyse.py:53-54`) is a lower bound on exposure, not a corrected estimate, and
should be labelled so.

### 3. The date fallback and empty ranges are unreported silent fallbacks (moderate; G2)

- 134,584 releases (32%) use the HEAD date window. Their flag rate is higher than tag ranges in both ecosystems (npm
  22.6% vs 15.0%; PyPI 16.7% vs 13.3%), and for latest releases p is 39.7% (date) vs 29.5% (tag) in npm and 31.2% vs
  22.7% in PyPI (`flag_rate_by_method_eco`, `p_by_latest_method`). In multi-package repositories without tags
  (DefinitelyTyped, mypy_boto3_builder with 406 packages, azure-sdk-for-python with 164) every package's date window
  covers every sibling's commits, so the fallback is the worst case of finding 2.
- 22,747 releases (5.4%) have an empty range (21,745 date, 771 tag, 231 inactive; `date_method_zero_commits`,
  `tag_method_zero_commits`) and are unflagged without being counted anywhere. Causes include releases cut from
  branches not on HEAD, rapid successive publishes, and a `git log` that returned nothing.
- `primary.json` key `latest_release_in_window` (`analyse.py:171`) is the total number of analysed releases per
  ecosystem, not what its name says.

Fix: a coverage table (G2) giving, per ecosystem, releases by method, empty ranges, packages with no release in the
window, and the tag-only p alongside the headline; rename or drop the mislabelled key.

### 4. H2: pair count inflated 3.3×, 80% of pairs share a release, and the plan's matching gives 1.12 (moderate)

`check_latency.py` reproduces the study exactly (296,806 pairs, 2,528 repositories, ratio 1.009, CI 0.987-1.109),
then shows (`latency_check.json`):

- the 296,806 pairs contain 89,774 distinct agent commits: `extract.py:122-126` emits one row per (package, commit),
  so a commit in a monorepo appears once per sibling package, and `analyse.py:103` matches per (repo, eco, name).
  Ten repositories supply 44% of pairs (remotion 27,312; storybook 24,279; google-cloud-python 20,560;
  sentry-javascript 20,209);
- 80.2% of pairs are in the same release as their matched human commit (npm 82.5%, PyPI 75.4%). For those pairs the
  two latencies differ only by the committer-time gap, whose median is 0.07 days, so a ratio near 1 is largely
  built in. The median paired difference is 0.008 days; among the 58,866 different-release pairs the ratio is 0.90;
- the 65,399 unmatched agent commits (18% of agent rows) have shorter latencies than matched ones (median 4.8 vs 6.8
  days; npm 2.9 vs 5.4), so their exclusion pushes the ratio up a little; they come from packages with no human
  commit within 14 days, i.e. agent-dominated repositories, which the comparison therefore cannot speak to;
- matching as the plan says (same repository, one row per commit, first release containing it) gives 89,700 pairs
  and a ratio of 1.117 (95% CI 1.048-1.19): agent commits wait slightly *longer*. H2 is Refuted either way;
- negative latencies are 1.2% of rows and 1.1% of pairs, immaterial; 7.6% of rows exceed 365 days (commits reachable
  from a tag but not the previous one, through long-lived branches), harmless to medians.

Fix: report distinct commits, the same-release share, the plan-wording ratio, and the unmatched commits' latency;
change "ship no faster" to "ship no faster, and under the plan's matching slightly slower"; note the deviation
(matching within package rather than repository) in `deviations.md`, where it is absent.

### 5. "Largely through a few hubs (cryptography, cffi)" is contradicted by the data (moderate)

Un-flagging a single hub barely moves PyPI P_w (`ranges_exposure.json`): without numpy (in 1,175 trees) 35.5% →
34.2%; without cffi 34.5%; without annotated-types 33.8%; without cryptography 35.5% (no change, because every root
that includes cryptography also includes cffi or another flagged node). Exposure is diffuse across numpy, cffi,
annotated-types, cryptography, opentelemetry-api, tqdm, setuptools, aiohappyeyeballs, pillow and sqlparse. The report
(lines 119-123, 142) names only cryptography and cffi and omits numpy, the most-included flagged node. For npm the
most-included flagged nodes are Babel helpers (monorepo range, finding 2) and `use-sync-external-store` (161 trees).

Fix: replace the hub sentence with the leave-one-out numbers and the top-10 node list.

### 6. The precision audit cannot be verified from its artefact, and its sample has no power on the risky rules (moderate; G4, G7)

- `data/interim/precision_sample.csv` has columns repo, sha, agent, rule, line and no label column; the 100/100 exists
  only as a total in `precision_audit.json`. No second labeller (G7 not applied, stated in deviations.md).
- `extract.py:45-49` (`matched_line`) stores the *first* `Co-authored-by` trailer of the message, not the one that
  matched: 12,353 of 141,975 "claude" trailer rows show a line without an Anthropic address, and almost all of those
  are a human co-author listed before the Claude trailer (`attribution_strata.json`). The stored line is therefore not
  evidence for the label; the audit notes say labels were re-derived from the full commits, which is the right
  procedure but leaves nothing checkable.
- A random sample is ~80% Anthropic-address trailers, which cannot be false. My fresh 100 (seed 7, labels in
  `fresh_sample_seed7.csv`, matched text re-derived from the clones): 99 unambiguous agent signatures, 1 uncertain
  (a GitHub-app identity named "Copilot App" matched by `^copilot\b`). Stratified, the risky rules look fine: in a
  400-repository scan (`fn_scan_summary.json`) 71 commits matched the bare word "claude" without an Anthropic
  address and all but one were AI identities (claude[bot], "Claude Code", "Claude"); codex, junie, amp and jules
  trailer matches are Codex/OpenAI, JetBrains Junie, Amp and Jules identities respectively.

Fix: store per-row labels and the *matching* trailer (change `matched_line` to return the trailer that matched);
report precision by rule and stratum, with the Clopper-Pearson bound per stratum, not pooled; a second blind
labeller on the risky strata (bare-name claude, codex, copilot `^copilot\b`, identity rules) would take an hour.

### 7. "Agent" includes review-suggestion bots, inconsistently (minor-moderate)

64% of Copilot matches (19,681 of 30,564) are `Co-authored-by: Copilot <…+Copilot@users.noreply.github.com>`, the
trailer GitHub adds when a reviewer's Copilot suggestion or Copilot Autofix is committed, and 88% of Gemini matches
(1,970 of 2,233) are gemini-code-assist review suggestions (`attribution_strata.json`). These are AI-written diffs,
so counting them is defensible for an "AI-signed code" measure, but the plain-terms definition ("tools that write and
commit code on a developer's behalf") and the "agent" wording overstate them, and the scan found comparable review
bots excluded (greptile-apps[bot] 465 co-author trailers, coderabbitai[bot] 22 in 400 repositories). Fix: say
"AI-signed" where the number includes suggestions, split Copilot into coding agent (4,011 identity + swe-agent
trailers) and suggestions, and list the review bots not counted.

### 8. Easy false negatives, about 3% (minor)

The 400-repository scan found signed AI commits the rules miss: `Assisted-by:` trailers naming Claude Code or Kimi
Code (~280), "written by an agent (Claude Code, …)" lines (~96), "made with Cursor" (~31), "generated with help from
Claude" and "written with Claude Code" (~21), "AI-assisted with Codex" (10); about 440 against 14,665 matched, so
the signed population is undercounted by roughly 3% and the shares are, as stated, lower bounds. Worth a sentence;
no recomputation needed. (The matched `Cursor AI <…>` text seen in 215 first-trailer lines is not a miss: those
commits also carry a Claude trailer.)

### 9. "Claude Code signs 68%" is "Claude-model signatures" (minor)

The claude bucket is any trailer naming Claude or an Anthropic address: Claude Code's trailer, but also the
`claude[bot]` GitHub Action (1,208 identity + ~750 trailer rows), "Claude Bot" (498), Mastra Code with Claude
models (~1,000), aider with Claude models (66). Say "Claude-model signatures, mostly Claude Code".

### 10. Report text not matching the tables, and provenance wording (minor)

- Line 137 ("About a third of new releases in late 2026") was not updated by the G5 fix applied to the title and
  plain terms; make it "a fifth to a third".
- Standfirst line 5-6 and overclaim row 5: `top_npm.json` finished downloading at 22:47:19 NZDT, one second after
  the pipeline-code commit (22:47:18), so that download began before the code was committed. The plan and the
  attribution rules (22:43) did precede all data; say that.
- The agent-mix sentence relies on `agents_total`, which counts commits since 2024-06 in repositories per ecosystem
  with double counting of repositories hosting both ecosystems (immaterial).
- `analyse.py:173-175`: "monorepo" is a repository hosting more than one top package across both ecosystems, and
  `drop` removes nodes by name regardless of ecosystem; 25 npm and 27 PyPI packages are affected, immaterial but
  worth a word.
- `latency_check.json`: 0.54% of (package, commit) pairs appear in several releases of the same package before
  dedupe; the dedupe to the smallest latency is as planned.
- Every number I checked in report.md agrees with `primary.json` (p, P_w, R, CIs, sensitivity, H2 medians and pairs,
  monthly shares, agent mix, release methods, graph counts, coverage, hub counts). The 68%/13-16%/4-10% agent mix
  and the six- to eightfold rise are arithmetically right.

### 11. deps.dev pads PyPI versions, so 10% of in-set PyPI nodes can never match a release (moderate; G2)

`analyse.py:20-21` normalises PyPI names (PEP 503) but compares version strings exactly. deps.dev reports PyPI
versions with three components ("3.20.0", "26.3.0", "2026.5.0") where the registry has "3.20", "26.3", "2026.5".
`ranges_exposure.json` → `node_version_match`: 10.0% of in-set PyPI nodes (10,480 of 104,827) have a version that
exists in no registry release of that package (npm: 0.3%, all pre-releases); the biggest are idna (2,540 node
rows), packaging (1,747), pycparser (1,054), tzdata (984), networkx, pytz, websockets, jsonpointer, jsonpatch,
tornado. These nodes are silently unflagged, and the reported "coverage" (97.7% / 99.4%) counts names, not
versions. A further 1,303 in-set PyPI nodes are pre-releases that deps.dev resolved to (opentelemetry 0.66.0b1 and
the like) and that the study excluded by design; and for 2.8% of roots the deps.dev root version differs from the
registry's latest, so the root's own flag can be lost in its tree (`root_node_version_equals_latest`).

Recomputing with trailing ".0" components dropped on both sides (`version_norm.json`): PyPI node match to a
window release 78.1% → 85.9%; P_w 35.5% → 36.1%; R 1.91 → 1.94 (CI 1.67-2.21); unweighted exposure 48.4% → 48.8%.
Immaterial to the verdict, because idna, pycparser and tzdata have unflagged latest releases and packaging's roots
were already exposed, but it is an unreported silent fallback and the correct numbers should replace the current
ones. Fix: canonicalise PEP 440 versions before matching (or compare `packaging.version.Version` objects), and report
node coverage by (name, version), split into pre-window, pre-release and unmatched.

### 12. Tag matching in multi-package repositories: candidate order is wrong, effect small (minor)

`extract.py:37-42` tries the name-free candidates (`v1.2.3`, `1.2.3`, `release-1.2.3`, …) before the name-specific
ones (`name@1.2.3`, `name-v1.2.3`, …). In the 818 repositories hosting more than one top package
(`tag_check.json`): 172,358 in-window releases were tag-matched, 116,534 (68%) to a generic tag; 2,207 matched a
generic tag although a name-specific tag for the same package and version exists (the generic one won on order);
17,466 (10%; npm 11.4%, PyPI 1.2%) matched a generic tag while the package has name-specific tags for other
versions, concentrated in tiptap (6,321), tanstack/router (6,153), tanstack/query (1,006), better-auth (727) and
orpc (680). In fixed-version monorepos such as these the generic and the name tag usually point at the same commit,
and the flag rate of the suspicious matches (17.8%) is no higher than that of name-tag matches (21.3%), so there is
no sign of systematic over-flagging from wrong tags. Fix for the record: try name-specific candidates first; note
the 2,207 ambiguous matches in the coverage table. Pre-release filters are right for npm (any `-`; `+` build
metadata not handled, rare) and over-broad for PyPI (`fetch.py:26,90`: any version containing a, b, c, rc, dev,
alpha, beta, pre or preview anywhere, so "1.0.final" or "1.2c" would be dropped; negligible in practice).

### 13. The trend is a pooled share dominated by a minority of repositories and by agents' own repositories (minor-moderate)

`ranges_exposure.json` (trend block): of 216,948 agent-signed non-bot commits since 2024-06, the top 10 repositories
hold 17.8% and the top 50 hold 43.9%. Per agent, one repository dominates several series: aider's own repository is
91% of aider commits (the PyPI spike of 1,099 aider commits in 2024-08 is that repository), OpenHands' own repository
56% of openhands, intellij-community 89% of junie, litellm 41% of devin, openclaw 44% of amp. In September 2026,
1,356 of 4,396 active repositories (31%) had at least one agent-signed commit; the pooled share was 12.3%, 10.1%
without the top 10 repositories, and the median repository had none. In the same month 9,832 of the 11,667 npm
releases (84%) came from multi-package repositories (flag share 39.9% vs 21.5% for the rest).

So "about one in ten changes carried an AI agent's signature" (plain terms) and "routine in the most-downloaded
packages" (line 137) are true of the pooled commit stream, not of the typical package. Fix: add the share of
repositories with any agent commit per month (F1 would carry it well) and note the self-hosting agents in the agent
mix.

## Gate checks

- **G1** (leakage audit in plan.md): not present; the study predates the gates. Not critical for this design, which
  has no fitted model; the equivalent risk here is the range-attribution leak of finding 2, which the plan did
  anticipate in §7.
- **G2** (coverage, no silent fallbacks): no `results/tables/coverage.json`. The empty ranges (5.4% of releases),
  the no-release-in-window packages in p's denominator (29% npm, 23% PyPI), and the date fallback's higher flag rate
  are unplanned-in-effect fallbacks that entered the headline statistic without being counted (finding 3), as is the
  deps.dev version padding that unflags 10% of in-set PyPI nodes (finding 11). Clone failures are counted correctly
  (2,626 inactive, 135 missing, 1 other; D1 verified by spot check); 21 cloned repositories yielded no commit rows,
  affecting 29 packages and no in-window release.
- **G3** (plausibility): no `results/plausibility.md`.
- **G4** (error audit): the precision audit is the only validation; it has no per-row labels and a stored line that
  is not the matched text (finding 6).
- **G5**: `overclaim_check.md` passes `--verify` (43 rows). It is not honest on rows 1, 38 and 39 ("do not
  multiply", "multiplication was modest", "essentially none"), which should be Overstated per finding 1; row 14
  ("small utilities with small, rarely released trees") has no number behind it and should be Not addressed or
  backed by graph sizes; row 9 should note the repository-level meaning of p. The new `monthly_nomono.py` is correct
  (same monorepo definition as `analyse.py`; 21%/25% reproduced).
- **G6**: `attribution.py check .` passes (10 claims). Spot-checked S1 (AIDev: 932,791 agentic PRs from five agents,
  MSR 2026, now with a published DOI 10.1145/3793302.3797249) and S5 (the 180M-repository census, arXiv 2606.24429,
  495 hand labels) against OpenAlex: both supported. The census's abstract also reports that bot-account lookup
  recovers only a few percent of Claude Code commits found by multi-method detection, which supports this study's
  choice to rely on trailers and its lower-bound framing; worth one sentence.
- **G7**: not applied; single auditor. My re-audit stands in as a second labeller for the sample (99 genuine, 1
  uncertain) but was not blind to the rule.
