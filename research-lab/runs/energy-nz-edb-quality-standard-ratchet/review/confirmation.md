# Confirmation pass: energy-nz-edb-quality-standard-ratchet (D3 fixes)

Reviewer: Fable 5.1. Date: 2026-10-25. Scope: verify the D3 fixes against review/review.md findings 1–10, check every
number in the rewritten report against the tables, and flag anything the fixes introduced. Supporting script:
`review/reviewer_checks/04_confirmation.py` (with `.log` and `.json`). Nothing outside `review/` was modified.

## Verdict: publish with edits

All ten findings are addressed in code, tables and text, and every number I checked in the new report matches
`primary.json`, `decomposition.csv`, `panel_checks.json`, `validation.json` and `icp_flags.json`. Including 2025
introduced no data error: the 2025 disclosure's timestamps are on the same clock as the model files (0 of 11,986 rows
fall before 1 April 2024 on the stored clock; the SAIDI-weighted hour-of-day profile correlates with 2024 at shift 0
and is negatively correlated at a 12–13 h shift), and Top Energy's omission moves the raw trend only from −4.11 to
−3.98. What the fixes left open is reporting: a preregistered sensitivity that materially qualifies the new headline
is missing, the recording-basis check is summarised as "comparable" when its own detail is not, and the figure
captions were not regenerated. None changes a verdict (H1 and H2 Inconclusive, H3 Supported under both windows).

## Findings 1–10: status

| # | Finding | Status | Evidence |
|---|---|---|---|
| 1 | ICP weights | Fixed | `panel.py` guard (1/3–3× median, interpolated); `icp_flags.json` lists 5 (Alpine 2017, TLC 2020, and three 2025 values: Invercargill, OtagoNet, TLC). Alpine's 2017 weight share now 1.9%; 2017 national raw 183.0. Report table (lines 105–111), sensitivities (117–122) and index ranges (14–15, 123) match `primary.json`. |
| 2 | 2025 | Fixed, with new issues 1–3 below | `panel_checks.json`: "All" rows, 26 of 28 within 5%, usable; Horizon alias in `ALIAS`; Top Energy 2025 excluded in `build` and `MISSING`/H3 years; study-distributor filter before `_std`; `national()` NaN-aware. Timestamp basis verified (check 04). |
| 3 | DPP3 cap | Fixed | D3 item 3; `validation.json["dpp3_vs_stata"]` max 0.052%, all 17; report lines 87, 144–146. |
| 4 | H3 conventions | Fixed | `primary.json` H3: exclude variant 4 (Invercargill, Firstlight, OtagoNet, TLC), inert {Invercargill, Nelson, Network Tasman}, range 1.285–24.57, `margin_a`; determination limits 2; report lines 21–29, 152–171 match. |
| 5 | Decomposition order | Fixed | `decomposition.csv` has `target3_at_bv4`, `d_boundary_first`, `d_boundary_shapley`; sums +11.22 / −4.88 / +3.17; report lines 31–33, 133–136. F2 caption not updated (new issue 4). |
| 6 | Section 0 median | Fixed | Report lines 34–35, 131–132: −1% (15), Aurora +57%. |
| 7 | Contravention wording, Table E3 | Fixed | Report lines 88–89, 187–189. E3 check is cited from the review rather than computed in the study (new issue 5). |
| 8 | Sign-blind H1 | Fixed | Report lines 17–18, 118–122. |
| 9 | Title | Fixed | Narrowed to what is shown; the ±5% cap "since 2020" is supported by Table J1 (12 of 17 adjusted) and 13 of 15 in 2025. |
| 10 | Small items | Partly | Stata comparison added to the gate; the ref `>=` / assessment `>` mix is still not stated in the report (new issue 6). |

## New issues

### 1. Moderate. The preregistered "window ending in 2024" sensitivity is missing, and it qualifies the new headline

- **Evidence.** `plan.md:106` lists "trend windows ending in 2024" as a sensitivity. `primary.json["sensitivity"]` has
  only `no_2023` and `no_aurora`. Check 04, same code and weights: 2014–2024 raw −1.79%/yr (−5.62 to +2.50), H1 path
  "Inconclusive (raw trend interval includes 0)", rolling-excluded −0.06 (−2.26 to +2.12), H2 +0.156 pp (−0.013 to
  +0.388); SAIFI 2014–2024 raw −1.91 (−3.66 to −0.69), Refuted. The 2014–2025 headline (raw −4.11, −7.27 to −0.48)
  therefore rests on the single 2025 point, the lowest in the series (88.4 min against 99.5–426 before).
- **Fix.** Add the sensitivity to `analysis.py` and the report; write the decline as conditional on 2025 ("fell 4.1%
  a year over 2014–2025; −1.8% with an interval including zero over 2014–2024"). Verdicts do not change.

### 2. Moderate. The recording-basis check is summarised as "comparable" but its own detail says otherwise

- **Evidence.** Report lines 191–192 and D3 item 2 quote the medians (count ratio 0.93, SAIDI per interruption
  0.86). `panel_checks.json["id2025"]["basis_2024_vs_2025"]["by_edb"]`: 6 of 15 distributors change by more than 1.5×
  from the 2024 model file to the 2025 disclosure in rows per year or SAIDI per row (Firstlight rows 0.51×, SAIDI per
  row 2.06×; Network Tasman rows 2.02×, SAIDI per row 0.32×; Orion 0.36×; Alpine 0.54×; Unison 0.58×; Invercargill
  1.59×). The 2025 file carries 1.24 rows per `interruption_identifier`, so row counts are not like-for-like with the
  model file. Annual totals, which the analyses use, match disclosed Class C within 5% for 14 of 16, so this is a
  caveat rather than a reason to re-exclude; but the granularity change can shift SAIDI across half-hours and days,
  and the check cannot tell a quiet 2025 from a basis effect on the level.
- **Fix.** Replace "comparable" with the per-distributor facts; restate the `plan.md:115-116` caveat next to the
  2014–2024 sensitivity (issue 1).

### 3. Minor. Top Energy's missing 2025 lowers the 2025 point by composition

- **Evidence.** Check 04: with Top Energy's disclosed Class C 2025 total (258.06, "All" row) imputed, the 2025 national
  raw index is 91.7 instead of 88.4, and the raw trend −3.98%/yr (−7.02 to −0.34) instead of −4.11. Top carries 1.7% of
  the weight but the highest SAIDI.
- **Fix.** Either use the disclosed annual total for Top Energy in the raw series (it needs only the annual value;
  the IEEE-excluded series cannot) or state the composition change in the report.

### 4. Minor. Figure captions and the F1 title were not regenerated

- **Evidence.** `figures.py` has no diff in the fix commit. `F1_national.txt` says "Trends 2014-2024" for 2014–2025
  numbers (`figures.py:48`); the F1 title "No trend to mask ... the storm-excluded index is flat" now sits beside text
  that says "fell 4.1% a year" (`figures.py:42`); `F3_compliance.txt` says "Assessment years 2021-2024" and "3 of 15"
  (`figures.py:91`); `F2_decomposition.txt` gives only the outcomes-first split ("+11 from the boundary").
- **Fix.** Parameterise the years and the H3 count, retitle F1 ("No rising trend to mask"), add the second ordering to
  the F2 caption, and re-run `figures.py`.

### 5. Minor. The Table E3 validation is cited, not reproduced

- **Evidence.** Report line 89 cites "review check 2"; `rules.py validate` and `validation.json` do not compute the
  comparison, so "Reproducing it" (lines 214–220) does not reproduce the assessment-mode validation.
- **Fix.** Add the Table E3 comparison (hard-coded values from DPP4 Attachment E) to `validate()`.

### 6. Minor. The strictness mix in H3 is still undocumented

- **Evidence.** `analysis.py:135` (reference, `strict=False`, the Stata convention) and `:138` (assessment,
  `strict=True`, the determination's "exceeds"); immaterial by review check 2, but the report's "How it was done" does
  not say so.
- **Fix.** One sentence under "The Commission's rule".

### 7. Minor. Wording on interpolated weights

- **Evidence.** Report lines 93–95: "Five distributor-years ... are interpolated". The guard also fills missing
  distributor-years (Alpine 2020, Nelson 2021 and 2025, Top Energy 2025) by the same interpolation.
- **Fix.** "Five flagged distributor-years, plus missing ones, are interpolated."

## Checks run

- `04_confirmation.py`: 2025 timestamp basis (stored clock, year-boundary rows, hour-of-day profile by shift);
  Top Energy 2025 composition (imputation and `h12()` re-run); the 2014–2024 window for SAIDI and SAIFI with the new
  weights; per-distributor recording-basis ratios and rows per interruption identifier; `validation.json` Stata
  comparison.
- Report numbers read against `primary.json`, `decomposition.csv`, `panel_checks.json`, `validation.json`,
  `icp_flags.json`, `transcription_check.json`; figures F1 (viewed) and captions F1–F3.
