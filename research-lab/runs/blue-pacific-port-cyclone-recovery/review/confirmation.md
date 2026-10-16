# Confirmation pass on the review response (commits e230de9, 7b6ad5f; deviations D8)

Reviewer: Fable 5.1, 2026-10-17. Checks for this pass are under `review/reviewer_checks/` (`dryrun_scorer.py`,
`dryrun_scorer.log`, `dryrun_tab/`). Nothing outside `review/` was modified; no state-changing git command was run.

## Recommendation: publish with edits

Every one of the 21 issues is resolved or honestly disclosed (table below). Every new number in report.md and
report.html matches `results/tables/review_response.json` and the new CSVs; the rewritten surviving claim and the
plain-language summary are now supported by the event-power and exposure tables; the revised scorer runs
end-to-end on a sealed vintage without edits. Three small wording edits remain, none touching a number, a verdict
or a frozen file.

## Remaining edits

1. **Verdict paragraph, sentence 4** ("Measured instead as average days disrupted, small-island ports showed far
   less disruption than other ports, not more."). The pooled measure inherits the detectability gap (small-island
   ports: median 0.99 calls/day, mean power 0.61 for a week-long closure; other ports 1.83 and 0.86). Write
   "far less *detectable* disruption", and add "part of that gap is detectability" or point to the exposure
   stratum (0 of 6 vs 14 of 23 inside hurricane-force winds), which is the part that is not.
2. **"It shows", second point** ("its signal is within chance and is carried by country port counts"). Within
   chance is true of the primary arm (p = 0.14); in the Cat 1+ arm it is not (p = 0.003) but is carried by port
   counts (share −0.37, p = 0.72 with log port count). Write "within chance in the primary arm and, where it is
   not (Cat 1+), carried by country port counts"; "not a usable predictor" → "not a usable predictor in these data".
3. **Forecast scoring rule.** The revised scorer reports two Brier benchmarks and a censoring-aware log error but
   no longer states what counts as success, and the dry run shows why that matters: with 0 of 3 events
   disrupted the forecast's Brier (0.0018) beats both the all-port (0.109) and small-island (0.0035) benchmarks
   trivially. State the decision rule now, before the season, in the report's forecast section and D8: for
   example, "better than climatology if its Brier is below the small-island benchmark and, if any event is
   disrupted, its log error is below the benchmark median's; with no disrupted event only the Brier part is
   assessed; with fewer than three events, reported and not interpreted." Otherwise September 2027 still holds a
   judgement call.

Trivial: "Only six of those ports actually took hurricane-force winds" (plain terms) — six of the 17 *cases*,
at six ports; "cases" is the precise word.

## Issue-by-issue

| # | issue | status | evidence |
| --- | --- | --- | --- |
| 1 | headline claim overreaches | resolved | new "Post hoc" section: 6/17 inside R64, power 0.33/0.79 at the Melissa hits, claim narrowed to four harbours; case series carries R64 and power columns; `event_power_sids.csv`, `exposure_primary.csv` |
| 2 | share is a country-port-count proxy | resolved | H1 section: r = −0.79, share +2.6 (p 0.24), log_nports +1.26 (p 0.008), Cat 1+ −0.37 (p 0.72); mechanisms paragraph replaced; `review_response.json` P4 |
| 3 | ΔAIC within noise | resolved | permutation p = 0.14, q95 5.0 (P5); "close to Refuted" removed; verdict says "indistinguishable from chance" |
| 4 | real false alarms 10.5% | resolved | P1: 10.1% (26/258), 6% SIDS, 15% >2 calls/day, spurious T median 34, 10 censored; in H2 table, external check, F1/F2 captions, methods |
| 5 | D4 guard post hoc | resolved | H2 section calls it post hoc with three counterfactuals (0.14–1.34 Refuted; 0.06–2.61 Inconclusive; pooled 0.02); D8 corrects D4; D4's own text left as logged |
| 6 | Laura→Delta compound events | resolved | "Two influential events"; sensitivity: category TR 3.06 vs 3.14 (P7); item 7 of "does not show" |
| 7 | Cebu level shift | resolved, new finding | without Cebu the category TR falls 3.1 → 0.9 (P7); stated in H2 and in the forecast caveats |
| 8 | D5 changed forecast ~4× | resolved | P8: Port Moresby 17 → 4, Suva 18 → 5, Apia 23 → 12; stated with "D5 was made after H1 and H2 were seen" |
| 9 | forecast table a traffic ranking | resolved | alphabetical, "this is not a ranking", log_activity 1.11 explained |
| 10 | scoring not runnable | resolved, one edit (above) | hash check, frozen covariates (sha256 30e8a4c1… matches D8), 108-row self-check passes, events.py takes directories, censoring-aware error, two Brier benchmarks, per-event seeds; dry run on 2019–20 reproduces the three Harold events in 17 s with outputs only where directed |
| 11 | simulation vs real pipeline | disclosed | methods paragraph and F1 caption state the iid-noise limitation and the real 10% |
| 12 | partial closures | resolved | 45% / 57% / 0.74 in the post-hoc section and item 3 of "does not show" |
| 13 | plain-language summary | resolved | three sentences rewritten; "exactly" dropped; false alarms mentioned |
| 14 | Monte Carlo noise in threshold | disclosed | item 11 of "does not show" (28 ± 1); recovery.py's global generator unchanged, correctly, since rerunning would alter preregistered outputs; the scorer seeds per event |
| 15 | stale docstring | resolved | recovery.py docstring rewritten, code byte-identical to d12c3f0 (checked) |
| 16 | numbers and wording | resolved | Nuku'alofa 0.02; "about 10%"; window "up to 27 days"; "dispersion 0.25" named; "about a third"; per-arm intervals stored (P4) and matching |
| 17 | "does not show" list | resolved | 11 items incl. small vessels, relief shipping, second storms, Pam/Winston/Gita, metering gaps |
| 18 | SIDS list, Guam | resolved | territories paragraph; Bahrain noted as immaterial |
| 19 | prior art | resolved | Verschuur 2023 added (NCC 13:804–806, 1,320 ports — verified); US DOT "Gulf and Florida storms of 2022" |
| 20 | timing | resolved | D8 corrects D4, D2 and D5; response code committed unrun at e230de9 01:10:39, unchanged through 7b6ad5f, outputs 01:11–01:18 |
| 21 | event table | resolved | "Saffir–Simpson from 1-minute winds, not the regional scale" added |

## Numbers checked this pass

| report statement | results file | match |
| --- | --- | --- |
| permutation p = 0.14, 95th pct 5.0 | P5: 0.14, 5.03 | yes |
| placebo 3/49 (6%), 23/209 (11%) | P1 by_group | yes |
| ~7 of 27 expected false alarms; spurious T median 34, 10 of 26 censored | P1: 6.85; 34.0; 10; 26 | yes |
| F2 caption ~9 of 28 | P1: 8.57 | yes |
| r(share, log ports) −0.79; +2.6 (p 0.24); +1.26 (p 0.008); Cat 1+ −0.37 (p 0.72) | P4 | yes |
| H2: 0.40 (0.14–1.34); 0.40 (0.06–2.61); 0.12 vs 5.84, ratio 0.02 (0.00–0.09) | P6 | yes |
| exposure 6/17 (0 disrupted) vs 14/23; p 0.017; 1/11 vs 8/34; p 0.42; 11 missing | P2 | yes |
| power 14 d mean 0.93, Santiago 0.33, Montego Bay 0.79; 7 d mean 0.61, 10 below 0.8; halved 45%/57%; 15 of 17 below 0.8 | P3 | yes |
| case series: 1.00/0.41, 1.00/0.52, 0.96/0.51, 1.00/0.63, 1.00/0.51; R64 no/no/no/yes/yes | event_power_sids.csv | yes |
| category TR ×3.1 → ×0.9 without Cebu; Delta-censored 3.06 | P7 | yes |
| D5 alternative medians 4/5/12 | P8: 4.04, 5.22, 12.22 | yes |
| forecast table (alphabetical) incl. Nuku'alofa 0.02 | forecast_table.csv | yes |
| hashes: model 0cbaa6e1…, table 26e6c7aa…, covariates 30e8a4c1… | sha256sum | yes |
| scorer self-check reproduces 108 rows; hash check passes | run read-only | yes |
| dry run 2019–20: three Harold events (Suva, Lautoka, Nuku'alofa), none disrupted; Brier 0.0018 vs 0.109 / 0.0035 | `dryrun_scorer.log` | yes |
| report.html numbers = report.md numbers | all present | yes |
| leftover pre-review phrases ("preregistered guard", "very likely have noticed", "about 0.95", "3–10%", "close to Refuted", "halves") | grep | none |
| plan.md unchanged since d12c3f0; D4 text retained | git diff, grep | yes |
