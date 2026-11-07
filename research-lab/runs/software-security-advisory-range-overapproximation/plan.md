# Plan (preregistration): do npm and PyPI advisories declare affected ranges that start too early?

Lead: `software-security-advisory-range-overapproximation`. Written before any advisory, commit or package file is
downloaded.

**Seen before this plan:**
- the OSV schema (`affected[].ranges[].events` with `introduced`, `fixed`, `last_affected`; `references[]` with type
  FIX or commit URLs);
- two example records, from search results: one with an unknown introduction point treated as "all previous
  versions affected", and one with an unknown introducing commit;
- abstracts of related work: affected-version identification tools for C/C++ and Java (ASE 2025; VERJava; Global-SZZ)
  and an OSV-derived ground-truth dataset that takes the published ranges as truth (arXiv 2604.21111).

## 0. Hypotheses

**H1.** Among GitHub-reviewed npm and PyPI advisories with a usable fix commit, at least 25% declare an affected lower
bound that starts before the vulnerable code existed in the package's releases.
- The share is computed among advisories whose lower bound is classified tight or over-approximated (section 3),
  with a Wilson 95% interval.
- **Supported** if the interval's lower limit is above 0.25; **Refuted** if its upper limit is below 0.25;
  **Inconclusive** otherwise.
- The share over all sampled advisories (undetermined counted as not over-approximated) is reported beside it as a
  lower bound. If more than 40% are undetermined, the report says the primary share rests on a minority.

**H2.** Correcting the over-approximated lower bounds reduces the number of affected (package version, advisory)
pairs by a factor of at least 1.5.
- F = Σ declared in-range released versions / Σ corrected in-range released versions, over the classified
  advisories (tight advisories contribute equally to both sums). The corrected range starts at the first release in
  which the vulnerable code is present.
- 95% interval by bootstrap over advisories (2,000 resamples, seed 20261107).
- **Supported** if the interval's lower limit is above 1.5; **Refuted** if its upper limit is below 1.5;
  **Inconclusive** otherwise.
- **Secondary (npm only):** the same factor weighted by each version's current weekly downloads (npm downloads API,
  read once on a fixed day): the share of current installs that are flagged only because of the lower bound.
- The lead proposed dependency-graph snapshots (deps.dev). Bulk access needs BigQuery, which this lab does not use,
  so the version-pair count and the download-weighted share are the operationalisation fixed here.

## 1. Data

- **Advisories:** the OSV export for the npm and PyPI ecosystems (`https://osv-vulnerabilities.storage.googleapis.com/
  {npm,PyPI}/all.zip`), downloaded once; the download date fixes the snapshot. Only GHSA records (id starting
  `GHSA-`) that are not withdrawn are used.
- **Eligible:** an advisory with exactly one affected package in the ecosystem; an ECOSYSTEM range with an `introduced`
  event and a `fixed` event; and at least one fix commit, meaning a reference of type FIX or a URL of the form
  `github.com/{owner}/{repo}/commit/{sha}`. Advisories with several fix commits use the one whose repository matches
  the package's source repository, else the first listed.
- **Sample:** a seeded random sample (seed 20261107) of 400 eligible npm and 400 eligible PyPI advisories.
- **Fix commits:** unified diffs from the GitHub REST API (authenticated, at most 1 request per second).
- **Releases:** the registry's version list with publish dates (registry.npmjs.org; pypi.org JSON API). For each
  advisory, every release that the declared range covers is downloaded (npm tarball; PyPI sdist, else a pure-Python
  wheel), processed, and deleted. Releases are ordered by publish date. Pre-releases are included only if the range
  covers them under the ecosystem's comparison rules (`semver` for npm, PEP 440 for PyPI).

## 2. Signatures and presence

- **Files.** Only source files the fix touches: `.js .mjs .cjs .ts .jsx .tsx` for npm; `.py` for PyPI. Tests,
  examples, docs, minified and generated files (paths containing `test`, `spec`, `example`, `doc`, `dist/`, `.min.`)
  are excluded.
- **Normalisation.** Strip whitespace, comments (`//`, `/* */`, `#`, docstrings left in) and trailing semicolons;
  drop lines shorter than 8 characters after normalisation and lines that are only imports, braces or keywords.
- **Signature.** The normalised lines the fix deletes. If the fix only adds lines, the signature is the 3 normalised
  context lines before each added hunk, and the added lines form a patch signature.
- **Presence in a release.** s = the share of signature lines found anywhere in the release's corresponding file
  (matched by path relative to the package root; if that path is absent, any source file).
  - **present:** s ≥ 0.8 and, for add-only fixes, fewer than half of the added lines present;
  - **absent:** s ≤ 0.2, with the release's source extracted successfully;
  - **undetermined:** anything else, or a download or parse failure.
- Package layouts differ between the repository and the published artefact (for example `src/` vs `lib/`). Path
  matching therefore uses the longest common suffix, and transpiled artefacts are handled by the "any source file"
  fallback.

## 3. Classifying a lower bound

For each advisory, the releases inside the declared range are walked in publish order.
- **Tight:** the earliest in-range release is present.
- **Over-approximated:** at least one in-range release before the first present release is absent, and some release
  is present. The corrected lower bound is the first present release.
- **Undetermined:** no in-range release is present (the signature never matches), or the releases before the first
  present one are all undetermined.
- `introduced: 0` advisories and advisories with an explicit lower bound are reported separately (secondary).

## 4. Secondary analyses (labelled as such)

1. The over-approximation share by ecosystem and by `introduced: 0` versus explicit lower bounds.
2. How far declared lower bounds sit before the corrected ones, in releases and in years.
3. Upper-bound check: the share of advisories where the vulnerable code is still present in the first release at or
   after `fixed` (the fix would then not be in the declared fixed version).
4. Sensitivity of H1 and H2 to the presence thresholds (present ≥ 0.6 / absent ≤ 0.4).

## 5. Gates

- **G1 (leakage).** No label enters the classification: presence is computed from released code only, and the
  declared range defines which releases are examined, not their classification. Withdrawn advisories are excluded
  before sampling.
- **G2 (coverage).** Every stage (eligible, sampled, commit fetched, signature built, releases fetched, classified)
  is counted with reasons for drops in `results/tables/coverage.json`.
- **G3 (plausibility).** Three advisories (one tight, one over-approximated, one undetermined) are traced by hand
  from the registry and the commit.
- **G4 (label audit).** A stratified sample of 60 classified advisories (30 over-approximated, 30 tight) is
  re-judged by a separate session, without the pipeline's label, from the commit diff and the earliest in-range and
  first-present releases. Agreement is reported. If agreement on "over-approximated" is below 80%, H1 is reported
  as unreliable.
- **G5 and G6** as in METHODS.md.

## 6. Limits stated in advance

- **Presence of vulnerable code is not exploitability.** The study measures whether the code a fix removes or
  guards existed in a release, not whether the release was exploitable.
- **Refactoring can hide code.** It produces undetermined classes, not false over-approximation, as long as an
  absent release lacks the signature and a later release has it. A rename between those releases could still mislead;
  the G4 audit checks this.
- **Fix commits can be incomplete or wrong.** An advisory whose fix commit does not touch the vulnerable code will be
  undetermined, or tight by coincidence.
- **The snapshot is one day's OSV export.** Advisories are edited over time.
