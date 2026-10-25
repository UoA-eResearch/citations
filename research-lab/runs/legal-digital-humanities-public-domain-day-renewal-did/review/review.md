# Review: legal-digital-humanities-public-domain-day-renewal-did

Reviewer: Fable 5.1 (independent, adversarial). Date: 2026-10-25. Scripts and outputs: `review/reviewer_checks/`
(`checks_did.py`, `checks_data.py`, `checks_extra.py`, `checks_binary.py`, each with a `.json` and `.log`).

## Verdict: fix first

The verdict label "Inconclusive" can stand, but the reasoning that supports it is wrong in four places, one data bug
misclassifies about 1,300 renewed books as never renewed, and the linkage precision is mis-measured. The robustness
"failures" the report leans on (RR 794; two failing pre-trends) are an unhandled separation in the reference cell, not
evidence. The result the report calls rule-passing rests on a single cohort and, within it, largely on one work. The OLS
secondaries are read backwards. An outcome the study never looked at (any new edition in the year) is robustly positive
under every variant, so the plain-terms conclusion "we cannot tell" is not a fair summary either. Timeline, data and
code are otherwise in order: plan.md (12:51) precedes all linkage and editions; the regex pre-filter is safe; the
renewal date window does what it should.

## Findings

### 1. [Major] The D1 primary (RR 1.86) rests on the 2024 cohort, and within it on one reference cell and one work

- Leave-one-cohort-out (`checks_did.json: leave_one_cohort_out`): dropping 2024 gives RR **1.15 (0.62–2.14)**; dropping
  any other cohort gives 1.64–2.48. Dropping the 2024 and 2025 cohorts: 1.26 (0.67–2.37). Restricting calendar years
  to ≤2023, which is the report's own diagnosis of the thin years: **0.98 (0.52–1.84)**; ≤2022: 1.07 (0.55–2.08).
- The 2024 cohort's reference cell (event −1, calendar 2023) holds **1 edition across 26 works**; its event-0 cell holds
  18 editions, 9 of them one work (`/works/OL5124546W`, 8 from one reprint publisher) (`checks_extra.json:
  cohort_2024_editions_2021_2025`). The 2024 cohort's event-0 coefficient is +4.96 log points
  (`pyfixest_separation_check_fe_ir.coefs_abs_gt_2.5`); its stand-alone RR is 53 (`secondary.json`). The report lists
  the by-cohort RRs but never says that the pooled result disappears without this one.
- Calendar 2024 has 53 editions in the whole linked panel and 2025 has 15 (`checks_data.json:
  editions_by_pub_year_2000_2026`), so a cohort whose post period lies in 2024–2025 cannot carry a count estimate.

Fix: report leave-one-cohort-out and the ≤2023 / ≤2022 restrictions in the results table, and say plainly that the
rule-passing number depends on the 2024 cohort.

### 2. [Major] The "explosions" in the print-on-demand and lag variants are unhandled separation of the reference cell, not robustness failures

- D1 (`code/did.py:69`) tests only the estimated dummies (e ≠ −1). It never tests the omitted reference cell. If a
  cohort's −1 cell sums to zero, every other dummy of that cohort is identified only against zero and goes to +∞.
- No-POD: cohorts **2022, 2023 and 2024 have 0 editions at event −1** (`checks_did.json: nopod_reference_cell_sums`).
  Their stand-alone log RRs are 13.7 each (`nopod_by_cohort`). That is where RR 794 and "pre-trend p < 0.001" come
  from. Without those three cohorts: **RR 1.32 (0.50–3.47), pre-trend p = 0.44**.
- Lag: cohort **2025 has 0 editions at event −1**. Its pre-period dummies explode (event path −8..−3 at +1.4 to +2.1),
  which is the "failing pre-trend". Without 2025: **RR 1.15 (0.57–2.29), p = 0.39**. Under the lag filter the 2023,
  2024 and 2025 cohorts also have no identified post cell at all (`secondary_lag.json: separated_cells_dropped`), so
  the RR is a 2019–2022 estimate; the report does not say so.
- The report's sentences "the model breaks down: RR 794" and "with a failing pre-trend" are therefore misdiagnoses. The
  corrected variants are null, not exploded, and they are a weaker argument against H1 than the report makes them.

Fix: extend D1 so that a cohort whose reference cell is all zero is dropped (or re-referenced) and recorded as
separated; rerun nopod, lag and by-cohort; rewrite the robustness paragraph and the title.

### 3. [Major] The OLS secondaries are read backwards

- Report: "Sun–Abraham OLS +0.004 (−0.001 to +0.008) … Both are tiny on a scale where most work-years are zero." The
  scale is the point. The treated pre-period mean of log(1 + editions) is 0.0089 (`checks_did.json: ols_scale`), so
  +0.0036 is a **+40%** change with a CI from −11% to +92%; it is uninformative, not null. The TWFE OLS (+0.0055, SE
  0.0015) is **+62%** and significant. Neither contradicts RR ≥ 1.5; the report lists them under "does not survive its
  checks".
- Plan §3.2 asks for Sun–Abraham OLS; `did.py ols` is a two-way FE post/other regression and `secondary.py sa_ols` is
  the Sun–Abraham one. Both are reported, which is fine, but the labels in the report table should say which is which.

Fix: express the OLS coefficients relative to the base rate and move them out of the "fails" list.

### 4. [Major] On the extensive margin the effect is robust; the plain-terms summary and title are not fair

Exploratory, not preregistered: outcome = 1[any new edition in the year], same PPML/D1 machinery
(`checks_binary.json`):
- RR **3.45 (2.04–5.83)**, pre-trend p = 0.98; event path −0.09, +0.41, −0.06, +0.03, +0.11, −0.00, −0.05 before, then
  +0.87, +1.51, +1.58, +0.65, +0.94 after.
- Leave-one-cohort-out 2.6–4.4 (all intervals exclude 1). Years ≤2023: 2.29 (1.32–3.98). Without 2024–25 cohorts:
  2.84. Lag: 3.03 (1.65–5.55) once the 2025 zero-reference cell is handled. No-POD without zero-reference cohorts: 2.15
  (0.88–5.27). Placebo: 0.98 (0.62–1.56).
- The count outcome is fragile because single works flood single years: one work has 426 of 4,164 editions in the
  window; the 2021:−2 cell is 28 of 38 editions from one work and 2023:−2 is 45 of 95 (`checks_data.json:
  treated_cells_ev_m3_p3`), almost all "Independently Published". Capping editions at 5 per work-year gives RR 2.78
  (1.58–4.89).

The honest summary is: the preregistered count estimate is fragile and depends on one cohort; the probability that a
newly freed book gets any new edition roughly doubles to triples and that is stable. "We cannot tell whether expiry
raises new editions in this catalogue" and "fails its robustness checks" overstate the negative. Keep the verdict
Inconclusive by rule (the prereg outcome is counts) but add this as a labelled exploratory result and reframe.

### 5. [Major] Linkage precision is mis-measured: the labeller never saw the matcher's choice in 16 of 90 cases

- `validate_links.py:42` shows the top 8 candidates by title similarity, ties broken arbitrarily; `score()`:73 counts
  `linked_letter is None` as an incorrect link. For 16 of the 90 linked items (8 renewed, 8 not) the linked work was not
  among the 8 shown; these registrations have 16–584 candidates at similarity 100 (`checks_extra.json:
  validation_precision.not_shown_detail`). Each was scored as a false positive although the labeller's "none" says
  nothing about the linked work.
- Among the 74 evaluable items, precision is **73/74 = 0.99**; the one genuine error is R289 (a different compilation).
  The reported 0.81 is an artefact of the sampler.
- Recall is conditional on the shown candidates: 40 items had no candidates at all (33 never renewed, 7 renewed) and 128
  hit the 8-candidate cap. Report and deviations present "recall 0.38" as if unconditional. Of the 120 recall misses,
  104 are the equal-best ambiguity drop (70 renewed, 34 not), 10 are surname failures (e.g. a Clemens/Twain case).

Fix: re-score with the 16 unshown items excluded (or re-sample with the linked work always among the shown candidates,
still blind) and label recall as conditional. The deviations and report numbers change.

### 6. [Major] Renewal matching reads the wrong title column for half the renewal rows

- The NYPL renewal TSVs have two schemas: 120,776 of 245,589 A-class rows have no `title`, and 112,460 of those carry it
  in `titl` (`checks_binary.json: renewal_rows`). `registrations.py:58,61` uses `title` only, so for those rows the
  similarity is 0 and `ren_ok` is False even when number and date match.
- Result: **1,262 registrations with a number match and a date within ±1 year are classified as never renewed**
  (1927: 196; 1928: 341; 1929: 311; 1930: 297), 122 of them in the linked control group (`checks_extra.json:
  renewal_false_negatives_missing_title`). A further 425 registrations fail the title rule at similarity 50–59 because the
  renewal title is prefixed with the author's name (e.g. "SURNAME, GIVEN. Title"), 94 of them in linked controls.
- Treated books misfiled as controls attenuate the estimate and show the expiry response inside the control group.

Fix: coalesce `title`/`titl`, strip a leading author prefix from the renewal title before scoring, rerun
registrations.py and everything downstream.

### 7. [Minor] Renewal pre-counts reconcile; the date window is doing real work

The plan's number-only pre-counts (~5,550 for 1929 and 1930) were inflated by number reuse: for rejected matches the
renewal's original year minus the registration year peaks at +17 to +19 (3,428 at +18, i.e. 1946–48 numbers) and at
+9/+10 (`checks_data.json: year_fail_oyear_minus_reg_year_dist`). The ±1 year window removes these correctly. Renewed
shares are 17–18% in every year, which is plausible. 1,886 registration numbers are duplicated within the CCE
(306–560 a year for 1927–1930); the renewal flag is then attached to whichever entry's title matches, which is fine.

### 8. [Minor] Unlogged deviation in blocking; the date check is nearly vacuous

Plan §1: blocking on "normalised author surname plus the first title token". `link.py:33–35, 63` blocks on the first two
non-article title tokens and applies the surname only at `resolve()`. Log it. Separately, 85.5% of links have no Open
Library first-publish year (`links_first_year_missing`), so the date rule rarely binds.

### 9. [Minor] The uniqueness drop selects against renewed books; give the numbers

Among registrations with at least one candidate passing the surname and date rules, **60% of renewed vs 44% of
never-renewed are dropped as equal-best ambiguous** (`checks_data.json: among_has_ok_by_renewal`); linked shares are 36%
vs 49%. The report says this qualitatively; it should state it. Edition splitting among linked works is small: only
2.6–3.3% of linked registrations had a second passing work at lower similarity (`linked_with_other_ok_works`).

### 10. [Minor] Some "treated" works were not newly freed at expiry

Of the 184 treated works in the model, 64 have a known Open Library first-publish year and **17 of those are earlier
than the registration year**, 12 by four years or more (`checks_extra.json: first_year_vs_reg_year.treated_in_model`):
reprints of older works whose 1920s registration covered a new edition, not the text. Consistent with this, 6 renewed
works appear on Gutenberg before their expiry and 4 of 696 renewed-1930 works before 2026. Small, but it dilutes the
treated group and mis-times a few events into the reference year. State it; consider excluding first_year < reg_year.

### 11. [Minor] Gutenberg "about 7 times" overstates; the timing is the evidence

The 1.83% vs 0.25% comparison sets a post-expiry burst in a more popular group against the 3-year hazard of a less
popular group. Overall, 3.0% of renewed vs 0.77% of never-renewed linked works are on Gutenberg at all. Within the
renewed group, releases by years since expiry are 30, 27, 13, 13, 13, 10, 12, 5 for years 0–7 (`checks_data.json:
gutenberg.renewed_pg_year_minus_expiry`): a burst in years 0–1 at roughly 2.5× the later rate. Report the timing
profile and the within-group comparison; the 2024–2025 cohorts' windows are also truncated by the 2026-10 catalogue
date, which the caption notes but the pooled figure does not.

### 12. [Minor] HathiTrust does show timing

The report says a single snapshot cannot show timing, but `secondary.json: hathitrust.renewed_by_reg_year` does: the
1930 cohort (expired 2026-01-01, nine months before the snapshot) is 94.7% full view against ≥99.2% for 1923–1929.
Use it.

### 13. [Minor] Provenance of the "first run" and of cell_counts_d1.csv

File mtimes: `secondary_ols.json` 17:15:33 (the TWFE ran before the primary), `primary_pre_d1.json` 17:16:41,
`cell_counts_d1.csv` 17:16:43, `primary.json` (D1) 17:17:00. Nineteen seconds is not enough to read a result, diagnose
separation, write a diagnostic and implement a fix, so the recorded pre-D1 run is a re-run and the time of the actual
first run is unrecorded. `cell_counts_d1.csv` has no generating code in `code/`. The D1 change to did.py, deviations.md,
all results and the report are in one commit (26ff608). The deviation is honest about being post-result, which is the
right direction; make the sequence explicit and add the cell-count script. Also: pyfixest's own
`separation_check=["fe","ir"]` on the preregistered specification drops exactly the same seven cells and returns RR 1.862
(1.01–3.43) (`checks_did.json: pyfixest_separation_check_fe_ir`), so D1 is the standard fix, correctly implemented for
the estimated dummies; its only gap is finding 2.

### 14. [Minor] Report numbers

All table numbers match `results/tables/` (RR, CIs, p-values, work counts, cohort RRs, Gutenberg shares, HathiTrust
shares, 30,705/30,329, 3.7%, 15 editions in 2025, two-thirds POD). Nits: "almost all in 2024–2025" — five of the seven
dropped cells are 2025, one is 2023, one is 2013, none is 2024. "The model breaks down" and "failing pre-trend" (finding
2), "Both are tiny" (finding 3), and the plain-terms conclusion (finding 4) need rewriting.

### 15. [Minor] Editions step checks out; the parse cannot be audited

Regex pre-filter: on 400,000 dump lines, 269 JSON hits = 269 regex hits, no escaped slashes (`checks_extra.json:
editions_regex_prefilter_sample`). pub_year is missing for 0.8% of editions. `editions.parquet` keeps only the parsed
year, not the raw publish_date string, so the parse rule cannot be audited from outputs; retain the string. Editions by
publish year in the panel: 2021: 823, 2022: 291, 2023: 143, 2024: 53, 2025: 15. 2023–2025 are under-ingested enough that
count-based post periods for the 2023–2025 cohorts are uninformative, which makes finding 1 worse.

## What must change before publication

1. Fix the renewal title column (finding 6) and rerun everything.
2. Extend D1 to the reference cell (finding 2); rerun nopod, lag, by-cohort.
3. Re-score the validation (finding 5).
4. Add leave-one-cohort-out and thin-year restrictions (finding 1); add the binary outcome as exploratory (finding 4).
5. Rewrite the title, the robustness paragraph, the OLS sentence and the plain-terms section accordingly. The verdict
   can remain Inconclusive by rule, with the honest gloss that the count estimate is fragile while the any-edition
   margin is robustly positive.
