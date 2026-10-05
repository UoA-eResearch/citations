# Deviations log: wastewater FluSight-value deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D1. Preregistration (2026-10-01 04:41:59)
`plan.md` committed as 1f0956b, before any hospital admission data were downloaded or examined.

### D2. Real-time vintage rule corrected (2026-10-01 04:43:56)
`plan.md` §3 said: use the vintage with the latest `as_of` ≤ R before 2025-07-05 (reading the hub README's
"as_of represents the reference_date"), and the latest `as_of` ≤ D after. Checking against the data shows the
first half of that rule would leak one week of future data.

- **Saturday-labelled vintages** (60, to June 2025) contain data up to their own `as_of` date. They are labelled by
  their last data week, not by the forecasting round that used them.
- **Check against the hub's own real-time forecasts.** The FluSight-baseline median at horizon 0 equals the last
  observed value it saw. At every location it matches:
  - for rounds 2023-12-02, 2024-01-06, 2024-02-10 and 2025-02-15, the vintage labelled R − 7, and 0–4% of locations
    for the vintage labelled R;
  - for 2025-12-20 and 2026-02-07, the Wednesday vintage labelled R − 3, with data through R − 7.

Corrected rule, identical in intent to the plan (data as available at the due date D = R − 3):

- a vintage's release date is `as_of` + 4 days for Saturday-labelled vintages and `as_of` for Wednesday-labelled ones;
- a round uses the latest vintage released on or before D.

For 81 of the 85 rounds this gives data through R − 7. For 4 rounds (2024-11-30, 2024-12-14, 2025-01-11, 2025-12-06)
the hub has no vintage for that week, and the data end at R − 14. Following the plan's fallback, those rounds use the
earlier vintage; their forecasts are one step further ahead.

### D3. Preregistered results, then exploratory analyses (2026-10-01 04:47-05:12)
**Validation (plan §6), run before the hypotheses were scored** (04:47-04:51). All three checks passed.
- V1, oracle leading indicator: relative WIS 0.820 [0.759, 0.883].
- V2, deranged states: 0.997 [0.951, 1.053].
- V3, leakage assertions on 12 random rounds (`results/tables/leakage_checks.csv`).

**Preregistered results.** `results/tables/relwis_*.csv`, `h3.csv`, `h4.csv`, `comparators.csv`, `by_group.csv`.

| Analysis | Relative WIS [95%] | Verdict |
|---|---|---|
| H1, primary (16 locations, 4,052 tasks) | 0.995 [0.946, 1.045] | inconclusive; lower bound just below 0.95 |
| H2, coverage ≥ 20% | 0.987 [0.940, 1.038] | inconclusive |
| H4, ensemble average (ens + wastewater vs ens + base) | 0.992 [0.964, 1.020] | contradicted |

- **H3:** slope -0.047 [-0.149, +0.045] per unit coverage over 141 state-seasons; inconclusive.
- **Sensitivity analyses**, primary panel:
  - lag 5 days: 0.981 [0.937, 1.031];
  - lag 17 days: 1.005 [0.944, 1.069];
  - flow-normalised: 1.007;
  - level only: 1.005;
  - base model trained on all rows: 1.009;
  - WVAL-based signal: 1.045;
  - holiday weeks excluded: 0.980.
- **Benchmark.** The base model without wastewater scores 0.98 [0.92, 1.08] against the FluSight ensemble and 0.67
  against the FluSight baseline.

Intervals are from the 5,000-draw runs (`relwis_*.csv`); `timeliness.csv` and `by_group.csv` use 2,000 draws, so
their bounds can differ in the third decimal.

**Code fixes during the run** (no change to any specification):
- the WVAL export has display-name columns and full state names; the mapping was fixed and S6 rerun;
- a panel filter in `analyze.py` passed a mask instead of a frame, and was fixed before any output was used.

**Exploratory analyses, not preregistered** (05:04-05:12), prompted by the null result:
1. **Lead-lag** (`code/explore_leadlag.py`, `leadlag.csv`). Final data, no reporting delay, weekly windows aligned with
   epiweeks, primary state-seasons. The correlation of weekly changes peaks at lead 0 (0.25; 0.22 at a 1-week lead).
   The correlation of levels peaks at leads 0-1 (0.75). The state signal is roughly coincident with admissions, not
   two weeks ahead.
2. **Timeliness curve** (`code/explore_timeliness.py`, `timeliness.csv`). Lags 0, 2 and 7 days were added to the
   preregistered 5, 10 and 17. Primary-panel relative WIS:

   | Lag (days) | 0 | 2 | 5 | 7 | 10 | 17 |
   |---|---|---|---|---|---|---|
   | Relative WIS | 0.937 [0.882, 0.991] | 0.962 | 0.981 | 0.983 | 0.995 | 1.005 |

   The secondary panel gives 0.930 [0.895, 0.971] at lag 0. The gain is largest at horizon 0 (0.919 at lag 0).
   - Lag 0 means samples collected up to the due date, four days into the horizon-0 target week. It is a best-case
     bound, not a realistic delay.
   - Real reporting delays could not be measured: `date_updated` holds one refresh date, and no public vintages exist.

### D4. Independent review and revisions (2026-10-01 05:16-05:30)
A separate reviewer agent (Fable 5.1), given the plan, log, code, data and draft, returned PUBLISH WITH EDITS.

**What it verified.**
- No leakage, scoring or statistical bug. It re-derived the vintage rule for all 96 vintages, the window alignment for
  every lag, the controls, quantile regression convergence and WIS.
- Every number in the draft matches the tables.
- Its own robustness check: both models trained only on the 16 primary states give 1.010 [0.949, 1.066].

**Changes made:**
1. **Exploratory results no longer stated as fact.** The report's plain-terms section, abstract and discussion had
   stated the timeliness results as established. They are now labelled exploratory.
   - Only lag 0 (0.937 [0.882, 0.991]) and the secondary panel at lag 2 (0.943 [0.913, 0.976]) exclude 1.
   - Lag 0 is an unreachable bound that partly observes the horizon-0 target week.
   - The claim that timeliness matters "more than how many sites" is withdrawn: H3 is inconclusive, so coverage cannot
     be ranked.
2. **The 10-day delay is described as an assumption** throughout. WastewaterSCAN, 29% of samples, is said to publish
   faster.
3. **The primary panel is described accurately** as 16 states, not "all states".
4. **Plan §4 statement corrected.** It said tasks without wastewater features are outside the primary panel "by
   construction". That is false: 96 of 4,052 primary tasks (2.4%) use the base forecast (DC 2023-24: 64; DC 2024-25: 28;
   NE 2023-24: 4). Reported in the report. `code/review_checks.py`, `results/tables/review_checks.csv`.
5. **Stale-vintage rounds.** In the 4 rounds with data ending at R − 14 (D2), the wastewater window is aligned to that
   older week, one week earlier than the cutoff would allow. This is conservative.
6. **Censoring caveat added.**
   - 70% of samples are non-detects, recorded at exactly half the detection limit.
   - 93% of series are mostly non-detects.
   - In the primary states in December-February since October 2023, 24% of samples are non-detects: state and local
     programmes 33%, CDC-Verily 19%, WastewaterSCAN 5%.
7. **Added:**
   - the ensemble-average intervals: ens+base vs ensemble 0.966 [0.930, 1.018]; ens+wastewater vs ensemble 0.959
     [0.912, 1.024];
   - the note that H4's 50/50 averaging halves any effect;
   - the paired win share: the wastewater model is better in 55.0% of tasks, 56.8% at horizon 0 and 52.8% at horizon 3;
   - the season pattern: mean WIS difference −1.46, −2.24 and +2.05 in the three seasons, so the losses are in
     2025-26;
   - one-way bootstrap intervals: locations only [0.966, 1.021], dates only [0.966, 1.023]. California carries 22% of
     base WIS, and with 16 clusters percentile intervals may under-cover slightly.
   - the lead-lag bootstrap over state-seasons (`leadlag_bootstrap.csv`, 2,000 draws):
     - the peak is at lead 0 in 78.5% of draws, lead 1 in 12.9%, lead −1 in 8.6%, and never at 2;
     - corr(0) − corr(2) = 0.086 [0.014, 0.165];
     - corr(0) − corr(1) = 0.030 [−0.030, 0.091];
     - so "not two weeks ahead" is supported, but "coincident" cannot be separated from "one week ahead".

## Correction after publication (2026-10-06 02:39 NZDT)

The lab's self-audit (`research-lab/paper/`) noted an imprecise phrase. The report summarised relative WIS at
reporting delays of 10 days or more as "1.00". The values in `results/` are 0.995 at 10 days and 1.005 at 17 days, and
0.9949 rounds to 0.99. The text now gives both values. No conclusion changes.
