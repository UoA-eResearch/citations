# Preregistration: did hiding editors' IP addresses change vandalism on Wikipedia?

Lead: `comp-social-science-temp-accounts-vandalism` (research-lab/leads.json). Written 2026-10-01 and committed to git
before any edit or revert data were downloaded or examined.

Probes made before writing:

- **Literature and news search** (§1).
- **The mediawiki_history dumps** (2026-08 snapshot):
  - directory listing and file sizes for four wikis;
  - the table definition (column order);
  - a partial download of one tiny wiki (kwwiki), used only to map the 78 TSV columns. Its revert fields were not
    tabulated.
- **The Wikimedia Analytics edits API.** One call (English Wikipedia anonymous content edits, 2024), to confirm the
  endpoint for ranking wikis.

**Prior knowledge (disclosed).** The Wikimedia Foundation's Trust and Safety team reported in December 2025 that it saw
"no concerning trends like relatively more reverted edits or fewer account registrations" after the rollout. That is a
descriptive statement, not a causal estimate.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **The policy.** Until 2024, edits by logged-out Wikipedia users were publicly attributed to their IP address.
  Wikimedia replaced this with "temporary accounts": an auto-generated name, with the IP visible only to vetted
  functionaries. The rollout was staggered:
  - pilot wikis from October 2024;
  - larger pilots in early 2025;
  - most wikis by mid-2025;
  - English Wikipedia on 4 November 2025.
- **The question.** Does weaker public exposure of identity reduce the deterrent to vandalism? This is a long-standing
  question in research on peer production and online anonymity. Related work includes Tor contributions to Wikipedia
  (Tran et al. 2020, arXiv:1904.04324) and the Portuguese Wikipedia study of restricting IP editing (Wikimedia
  Research).
- **The gap.** No causal estimate of the rollout's effect on vandalism or edit quality was found, only WMF's
  operational monitoring.

## 2. Data and sample

- **Edits.** Wikimedia `mediawiki_history` dumps, snapshot 2026-08 (dumps.wikimedia.org/other/mediawiki_history/), one
  TSV per wiki and period.
  - Use revision-create events (columns 3–4) from 2024-01-01 to the last complete month in the snapshot.
- **Sample.** The 40 Wikipedias (language editions) with the most anonymous content edits in calendar 2024, from the
  Wikimedia Analytics edits API (`editor-type=anonymous`, `page-type=content`).
- **Content edits.** Revisions in content namespaces (`page_namespace_is_content`, column 35), excluding revisions
  deleted with their page.
- **Groups**, per edit:
  - **logged-out:** `event_user_is_anonymous` (column 20) or `event_user_is_temporary` (column 21);
  - **registered:** `event_user_is_permanent` (column 22), with no bot flag (`event_user_is_bot_by`, column 16, empty);
  - bots are excluded.
- **Treatment date** per wiki: the first day on which temporary-account edits make up at least 1% of logged-out
  content edits. It is derived from the data; the documented English Wikipedia date (2025-11-04) is a check.
- **Treatment month:** the calendar month containing the treatment date. That month is dropped as a partial month.

## 3. Outcomes (wiki × calendar month)

- **Y_LO (primary).** The share of logged-out content edits identity-reverted within 48 hours
  (`revision_seconds_to_identity_revert` ≤ 172,800, column 75).
- **Y_REG.** The same for registered non-bot editors. It serves as a within-wiki placebo and control.
- **GAP.** Y_LO − Y_REG.
- **Secondary:**
  - log logged-out content edits per month;
  - registered accounts created per month (user-create events, self-created);
  - the 48-hour revert rate of logged-out edits by editors on their first logged-out edit (where identifiable).

## 4. Hypotheses and estimation

- **H1 (primary, from the lead).** The switch increased the logged-out 48-hour revert rate by at least 10% relative to
  the pre-switch level: relative ATT = ATT(Y_LO) / pre-period mean of Y_LO ≥ 0.10.
- **H2.** The switch increased GAP, so the logged-out rate rose relative to registered editors on the same wiki.
- **H3** (secondary, two-sided). Logged-out edit volume and registered-account creation changed.
- **Estimator.** Callaway & Sant'Anna (2021) staggered difference-in-differences with not-yet-treated wikis as
  controls.
  - Cohorts are defined by treatment month.
  - Event time runs from −12 to +6 months; ATT is averaged over event months +1 to +6.
  - Cohorts with no not-yet-treated control in a given month do not contribute to that month.
  - Pre-trends are reported as the leads (−12 to −2), with the joint test.
- **Inference.** Cluster bootstrap over wikis, 2,000 draws, percentile 95% intervals.
- **Decision rule (H1).**

  | Verdict | Condition |
  |---|---|
  | Supported | relative ATT ≥ 0.10 and lower bound > 0 |
  | Contradicted | upper bound < 0.10 |
  | Inconclusive | otherwise |

  H2 and H3 are reported with intervals: "an increase" if the lower bound > 0.
- **Validity checks:**
  - **Placebo.** ATT on Y_REG should be about 0.
  - **Pre-trend leads.** If the joint pre-trend test rejects at 5%, the verdict is reported as conditional on
    parallel trends failing.
  - **Leave-one-cohort-out.**
  - **Excluding English Wikipedia.**

## 5. Robustness

- A 24-hour revert window instead of 48 hours.
- A treatment threshold of 10% instead of 1%.
- Weekly instead of monthly aggregation.
- A two-way fixed-effects event study, as a comparison with the staggered estimator.

## 6. Review and reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section.
- The data are open. Raw dumps are not committed; derived wiki-month tables are.
