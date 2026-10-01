# Deviations log: temporary-accounts vandalism deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D1. Preregistration (2026-10-01 15:02:47)
`plan.md` committed as 9304dc7, before any edit or revert data were downloaded.

### D2. Sample selection needed retries (2026-10-01 15:48:52)
The first two runs of `code/select_wikis.py` lost wikis to API throttling. A request that failed silently dropped its
wiki from the ranking: English and German Wikipedia in the first run, Persian, Hebrew, Indonesian and Bengali in the
second. Neither partial ranking was used.

The script now retries each request with back-off, then re-queries any remaining gaps. The final run has counts for all
348 open Wikipedias (`results/tables/wikis_all.csv`). The top 40 by 2024 anonymous content edits
(`results/tables/wikis.csv`) run from enwiki (6.80 M) to hrwiki (16,864).

Note: ptwiki is absent because it has restricted IP editing since 2020, so its 2024 count is near zero.

### D3. Download source and analysis window (2026-10-01 15:56:06)
**Download source.** The main dump server (dumps.wikimedia.org) rate-limited the parallel downloads with HTTP 429 and
saved 169-byte error pages under dump file names. Those files were deleted by exact path.
- Downloads now come from the ftp.acc.umu.se mirror of the same 2026-08 snapshot, about 3.5 MB/s per connection
  (`code/fetch_dumps.sh`).
- Every file must pass `bzip2 -t` before use.
- The file list is the mirror's index, filtered to the 2024, 2025 and 2026 (or all-time) files of the 40 sampled wikis.

**Analysis window.** The snapshot ends at the end of July 2026, so edits in the last two days of July cannot have a
complete 48-hour revert window. Analysis months therefore end at 2026-06; this fixes the plan's "last complete month".

### D4. Primary results, robustness, and an exploratory seasonal adjustment (logged 2026-10-01 20:51:16)
**Extraction check.** enwiki 2024-01 logged-out content edits from the dumps: 608,902, exactly the Analytics API
figure.

**Treatment dates** (`results/tables/treatment_dates_primary.csv`). Five waves:

| Wave | Wikis |
|---|---|
| 2024-11-05 | 5 |
| 2025-06-17 to 06-30 | 17 |
| 2025-09-02 to 09-23 | 14 |
| 2025-11-04/12 | enwiki, eswiki, huwiki |
| 2026-03-25 | ruwiki |

enwiki's inferred date (2025-11-04) matches the documented date.

**Primary results** (`results/tables/did_primary.csv`, 2,000 wiki-cluster bootstrap draws):
- **Y_LO:** ATT +2.0 points [-2.9, +5.3]; relative +7.3% [-10.3%, +19.0%]. H1 is inconclusive.
- **Pre-trends.** The joint pre-trend test rejects (p = 0.001), so per plan §4 the verdict is conditional on parallel
  trends.
- **Y_REG placebo:** -0.28 points [-0.73, +0.16]; pre-trend p = 0.90.
- **GAP:** +2.3 points [-2.7, +5.6].
- **Logged-out edit volume:** -3% [-10%, +7%].
- **Self-created accounts:** +10.1% [+1.3%, +18.8%], with pre-trend p = 0.043.

**Robustness** (`code/robustness.sh`). Relative effect on Y_LO, all inconclusive:

| Variant | Relative effect |
|---|---|
| 24-hour window | +6.9% |
| 10% threshold | +7.3% |
| Without enwiki | +8.1% |
| Leave-one-wave-out | +2.1% to +10.0% |

- Pre-trends pass only when the 2025-06 wave (p = 0.35) or the 2025-11 wave (p = 0.17) is dropped.
- Dropping ruwiki, the only control after November 2025, moves the estimate to +2.1%.

**Not run.** The plan's weekly-aggregation robustness check was not run: the estimator is month-based, and the
sensitivity checks above cover the same concern. This is a deviation.

**Exploratory, after seeing the pre-trend failure.** Raw Y_LO has a strong seasonal cycle: about 30% falling to 23% in
June-August of both 2024 and 2025, plausibly school holidays. The largest wave switched in June 2025.
- A year-over-year version (`code/extra_models.py`) applies the same estimator to Y(m) - Y(m-12), removing each
  wiki's own seasonality.
- It uses months from 2025-01 onward and drops the 2024-11 wave.
- The preregistered two-way fixed-effects comparison runs in the same script.

### D5. Independent review and corrections (logged 2026-10-01 21:44:48)
A separate reviewer agent (Fable 5.1) returned FIX FIRST.

**What it verified.**
- The column mapping, against raw rows.
- Sharp treatment dates.
- An independent implementation reproduces every estimate to 1e-16.
- The report's numbers.

**Changes, all re-run** (`code/run_all.sh`):

1. **Bug in the exploratory year-over-year model.** `matrices()` coded wikis treated before the panel window as "not
   yet treated", so the five 2024-11 wikis served as controls in the year-over-year model, which starts in 2025-01.
   Such wikis are now dropped.
   - Corrected: +0.04 points [-4.8, +3.0]; relative +0.1% [-17.8%, +11.0%].
   - The earliest leads (-12, -11) were artefacts of that bug.
2. **In-time placebo** (`code/placebo_checks.py`). The 2025-26 waves' dates were shifted back 12 months, on
   2024-01..2025-05, with no wiki treated.
   - Logged-out revert rate: +2.7 points [-0.2, +5.7] (+9.4%).
   - Registered: -0.06 points.
   - The design alone produces a spurious +2.7 points from the seasonal cycle. The primary estimate (+2.0) is
     consistent with no effect, and the seasonally adjusted estimate is the better guide to magnitude.
3. **Size of the pre-trend tests**, on that no-treatment panel with randomly reassigned fake dates (100 draws):
   - the preregistered 11-lead Wald test rejects at 5% in 96% of draws (at 1% in 90%), so it is uninformative;
   - a 5-lead test (-6..-2) rejects at 5% in 13%.

   On the real data the 5-lead test gives p = 0.21. The report now shows leads with intervals, reports the 5-lead test
   with its size, and no longer presents p = 0.001 as evidence that parallel trends fail. The "passes when a wave is
   dropped" statements inherit the same problem and were removed.
4. **Cross-wiki imported revisions** ("ar>User", `event_user_is_cross_wiki`, column 23) had been counted as logged-out
   edits. They make up about 20% of dewiki's logged-out edits, and are the cause of its apparent 80-92% adoption.
   - All 128 files were re-extracted, excluding them, into `data/processed/agg_v2`.
   - dewiki now shows 100% adoption after the switch.
   - Estimates barely move (primary +2.0 points, +7.2% [-10.3%, +18.9%]).
5. **Snapshot end.** The 2026-08 snapshot covers August 2026, so the last month with a complete 48-hour window is July
   2026, which is now used. The earlier statement (end of July, analysis to June) was wrong.
6. **Single-control dependence.**
   - 47% of the post-period weight comes from cells whose only control is ruwiki.
   - Per-wave post ATTs: 2024-11 -2.3, 2025-06 +2.2, 2025-09 +3.5, 2025-11 +2.1 points
     (`results/tables/cohort_att_primary.csv`).
   - The cluster bootstrap does not capture this well, so the intervals are probably too narrow. Without ruwiki: +2.1%.
7. **Edit-weighted variant added:** +7.0% [-8.7%, +20.6%].
8. **Wording corrections:**
   - accounts: +10.6% [+1.3%, +20.7%] as a percentage, with pre-switch leads at the same level, so there is no evidence
     of a change;
   - the registered placebo in relative terms: -10.9% [-27.9%, +6.4%];
   - "40 largest" changed to "40 with the most logged-out edits in 2024";
   - the 10% threshold is identical to the primary, because every wiki passes 10% on its first day;
   - the estimator-validation script was added (`code/validate_estimator.py`).
9. **Not run.** The plan's secondary outcome "revert rate of first logged-out edits" was not run: temporary-account
   identity is not linkable to prior IP edits in the dumps. This is a deviation.
10. **Caveats added to the report:**
    - temporary accounts persist via cookie, so repeat vandals are linkable;
    - abuse filters and IP blocks apply differently;
    - ORES / Lift Wing and RecentChanges tooling changed;
    - ruwiki has its own FlaggedRevs regime;
    - fawiki logged-out volume fell sharply in January-June 2026;
    - hrwiki has a volume spike in November 2025.
