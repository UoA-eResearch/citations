# Deviations from plan.md

## D1 — 2026-10-25 03:44 NZDT — the COVID-19 Forecast Hub secondary is not run

The archived `reichlab/covid19-forecast-hub` repository is 13.8 GB. Clones from GitHub ran at roughly 0.3–3 MB/s
today, so it could not be obtained within the run. As the plan allows, plan §1's secondary and §3.4 are logged as not
run. No other change; the primary FluSight analysis is as planned.

## Pre-review gate (G5, G6, plus a G3 point) — 2026-10-25 22:59 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title's "top model changed" now notes it happens in about half of bootstrap resamples;
  - "the top-ranked team changed" became "model", since one change is between two variants of the same team;
  - "leaderboards mostly reflect forecasting skill" became "mostly not an artefact of data revisions", as skill was
    not measured.
- **G3 point.** 2022–23 also had heavy revisions (27% of location-weeks revised by more than 10%) but no net bias and
  0.7% reversals. The revisions bullet and the closing sentence now say that the downward bias of first reports, not
  the size of revisions, goes with reversals.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 3 claims, passes): Mathis et al. 2024 (Nat. Commun.)
  resolves.

## D2 — 2026-11-07 — fixes after the independent review (verdict: fix first)

Everything here follows the first review (`review/review.md`). The preregistered H1 and H2 rules and their verdicts
are unchanged; the first draft's table is kept as `results/tables/primary_v1.json`.

1. **Revision statistics (finding 1).** These are now computed per scoring hub (old hub for 2022–23, new hub from
   2023–24) on forecast target weeks only. The first draft pooled both hubs' truth rows for the same weeks. The
   revisions bullet, results table and title are corrected; the "bias, not size" reading survives with new numbers.
2. **H2 (finding 2).** The verdict follows the preregistered rule, but `code/posthoc_review.py` adds two checks:
   - the leader when only the hub's own models (FluSight-*) and baselines are excluded;
   - how often the leader differs from its own point estimate under a single truth, beside the first-vs-final
     criterion (B = 200).

   The verdict line now says H2 is not robust to the rule and not distinguishable from that instability.
3. **Late first reports (finding 3, G1).** `code/score.py late7` drops location-weeks whose first hub version is more
   than 7 days after the week's end (8.1% of 2023–24 and 4.6% of 2024–25 scored forecasts). H1 gives 6.4%, and the
   2024–25 leader also changes at h0.
4. **Finality of 2022–23 (finding 4).** The old repository's last values are compared with the new hub's latest
   values, and 2022–23 is re-scored against the latter.
5. **Numbers (finding 5).** Lags are now computed on forecast target weeks: 1.5 and 4.5 days. The dropped units
   (186) and the models without quantile forecasts are stated.

## D3 — 2026-11-09 — edits after the confirmation pass (verdict: publish with edits)

- **Late first reports by season.** In 2023–24, the last four weeks appeared a median 194 days late (97% identical to
  final). In 2024–25, two weeks were about 11 days late (41% identical).
- **The late-drop variant.** With late first reports dropped, the 2024–25 h2 first-report leader becomes
  FluSight-lop_norm, a hub ensemble the name rule misses. This is now stated.
- **Units.** The 7 dropped 2022–23 units are MIGHTE-Nsemble units with a missing quantile, not missing truth.
- **The instability table** is labelled B = 200, post hoc, and distinguished from the preregistered B = 500 shares.
- **Wording:** the finality sentence now says "all 2,540" location-weeks.
