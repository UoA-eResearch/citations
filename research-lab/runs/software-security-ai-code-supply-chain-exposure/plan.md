# Plan (preregistration): how much of what npm and PyPI users install was touched by AI coding agents?

Lead: `software-security-ai-code-supply-chain-exposure`. Written before any package list, repository or dependency
graph is downloaded. Six repositories were cloned only to time the method, and the sources were probed for access.

## 0. Question and hypotheses

AI coding agents (Claude Code, the GitHub Copilot coding agent, Cursor's agent, Devin, Aider, Jules and others) now
commit to popular open-source repositories. This study asks how far their commits reach registry releases, and through
dependency trees, the people installing packages.

- **H1a.** In each ecosystem, the download-weighted probability that a top package's resolved dependency tree contains
  at least one AI-flagged release (P_w) is at least 5 times the unweighted share of top packages whose own latest
  release is AI-flagged (p).
  - **Supported** if the bootstrap 95% lower bound of R = P_w / p is at least 5 in both ecosystems.
  - **Refuted** if the upper bound is below 5 in either.
  - **Inconclusive** otherwise.
- **H1b.** P_w exceeds 30% for npm.
  - **Supported** if its 95% lower bound exceeds 0.30.
  - **Refuted** if its upper bound is below 0.30.
  - **Inconclusive** otherwise.
- **H1** is Supported if H1a and H1b both are, Refuted if either is, and Inconclusive otherwise.
- **H2.** AI-attributed commits reach a published release faster than matched human commits in the same repositories:
  the median latency ratio (AI / human) is at most 0.5.
  - **Supported** if the 95% upper bound of the ratio is at most 0.5.
  - **Refuted** if the lower bound exceeds 0.5.
  - **Inconclusive** otherwise.

All attribution is a lower bound: unmarked AI-written code is invisible to the method.

## 1. Population and snapshot

- **Packages.** The top 10,000 npm and the top 10,000 PyPI packages by last-month downloads, from the ecosyste.ms
  packages API, fetched once and frozen (`data/raw/top_{npm,pypi}.json`). Downloads are the weights.
- **Repositories.** GitHub repository URLs from ecosyste.ms metadata, falling back to the registry's own metadata
  (npm `repository`; PyPI `project_urls` / `home_page`). Packages without a GitHub repository are excluded and
  counted; they stay unflagged in dependency trees.
- **Clones.** Bare, treeless and shallow since 2024-01-01 (`git clone --bare --filter=tree:0 --shallow-since=2024-01-01`),
  at up to 8 in parallel. Failed clones are retried once, then excluded and counted.
- **Releases.**
  - **npm:** versions in the registry `time` map. **PyPI:** releases in the JSON API, with the earliest file
    upload time as the publish time.
  - Pre-releases (a semver pre-release tag, or a PEP 440 a/b/rc/dev) are excluded.
  - Releases published on or after 2024-06-01 are analysed. Earlier releases are unflagged (§2).
  - "Latest" is npm's `latest` dist-tag, or PyPI's `info.version`.

## 2. AI attribution and release flags

- **A commit is AI-attributed** if any of the following matches (case-insensitive; fixed list in
  `code/attribution.py`, written before the clones):
  1. **A `Co-authored-by:` trailer** naming:
     - Claude, or `noreply@anthropic.com`;
     - Copilot (name "Copilot", or a `+Copilot@users.noreply.github.com` address);
     - Cursor Agent, or `cursoragent@cursor.com`;
     - aider;
     - Devin, or a `devin-ai-integration` address;
     - Jules, or a `google-labs-jules` address;
     - OpenHands, or `openhands@all-hands.dev`;
     - Amp, or `amp@ampcode.com`;
     - Codex (name contains "codex", or a `chatgpt-codex-connector` address);
     - Gemini, with a google.com or gemini address;
     - Junie.
  2. **A message line** "Generated with [Claude Code]" / "Generated with Claude Code", or "Generated with" followed by
     another agent above.
  3. **An author or committer identity** of a known agent account: `copilot-swe-agent`, the Copilot noreply address,
     `devin-ai-integration[bot]`, `claude[bot]`, `google-labs-jules[bot]`, `chatgpt-codex-connector[bot]`,
     `openhands-agent`, `cursor[bot]` / `cursoragent`, or an author name ending "(aider)".

  Dependency and maintenance bots (dependabot, renovate, github-actions, pre-commit-ci and the like) are **not**
  AI agents.
- **Release commit ranges.**
  - The release is matched to a git tag. The tag patterns are `v{ver}`, `{ver}`, `{name}@{ver}`, `{name}-v{ver}`,
    `{name}-{ver}`, `{name}/v{ver}` and `release-{ver}`, plus the same with the unscoped npm name.
  - **Range:** commits reachable from this release's tag and not from the previous release's tag.
  - Without a previous tag: commits reachable from the tag and committed after the previous release's publish time.
  - **No tag at all (date fallback):** commits on HEAD committed between the previous and this release's publish
    times.
  - The method used is recorded per release.
- **A release is AI-flagged** if its range contains at least one AI-attributed commit.
- **p** is the share of packages with a cloned repository whose latest release is AI-flagged.

## 3. Dependency exposure (H1)

- **Graphs.** For every top package (the "root"), deps.dev v3 `:dependencies` gives the resolved graph of its latest
  version.
- **Exposure.** A root is exposed if any node of its graph, the root included, is an AI-flagged release.
  - A node is flagged only if its exact version is an analysed release (§1–2) of a package in the study set.
  - Nodes outside the set are unflagged, and the share of nodes covered is reported.
  - Roots without a graph are excluded and counted.
- **The statistics.** P_w = Σ downloads × exposed / Σ downloads over roots with a graph. R = P_w / p.
- **Intervals:** 2,000 bootstrap resamples of packages within the ecosystem, recomputing p and P_w on each resample.
  Node flags stay fixed.

## 4. Release latency (H2)

- **Latency** is a commit's release publish time minus its committer time, for commits in tag-based ranges only
  (§2). A commit belongs to the first release whose range contains it.
- **Matching.**
  - Each AI-attributed commit is matched, without replacement, to the human commit in the same repository with the
    nearest committer time within ±14 days.
  - Human means not AI-attributed and not a bot (an author name ending "[bot]", or a dependency or maintenance bot).
  - Unmatched AI commits are excluded and counted.
- **The ratio** is the median AI latency over the median matched human latency. Its 95% interval comes from a
  bootstrap over repositories (2,000 resamples).

## 5. Secondary analyses (labelled as such)

1. AI-attributed commits as a share of commits by month, and by agent, from 2024-06 onward, in each ecosystem.
2. Flagged releases as a share of releases by month.
3. H1 without packages whose repository hosts more than one top package (monorepos), and with tag-based ranges only.
4. Detector precision: 100 randomly drawn flagged commits with their matching rule, labelled by whether the matched
   text is an agent signature rather than a coincidence (for example a person named Claude). The labels are
   reported; recall is not estimable here.
5. The most-downloaded flagged releases and the paths by which they enter trees: package names and aggregate
   counts only, never commit text.

## 6. What would change the plan

- **Rate limits.** If ecosyste.ms or deps.dev limit access, the run waits. If that is impossible, the top-N is
  reduced to the same N in both ecosystems, logged before any flag is computed.
- **Detector errors.** If the precision audit (§5.4) finds a pattern with mostly false matches, that pattern is
  dropped and H1/H2 recomputed. This is logged as a post-result deviation with both results shown.

## 7. Limits stated in advance

- **Undercounting.** Attribution relies on voluntary or default trailers and bot identities. Agents used without
  trailers (much Copilot autocomplete, Codex CLI, ChatGPT pastes) are invisible, so every share is a lower bound.
- **Ranges are imprecise.** Monorepos make ranges over-inclusive: a commit to one package can flag a sibling's
  release. The date fallback is less precise than tags.
- **Downloads are inflated** by CI and mirrors, and only proxy installs.
- **Exposure measures provenance, not harm.** AI-touched code is not thereby insecure, and the study measures where
  agent commits go, not their quality.
