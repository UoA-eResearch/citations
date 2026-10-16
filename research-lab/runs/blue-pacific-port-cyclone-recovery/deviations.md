# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 00:02 NZDT — the lead's primary hypothesis cannot be tested; restated before any outcome

Counting events and port activity - neither involves a recovery time - showed the lead's first claim ("Pacific
island ports' median recovery is >= 14 days and >= 2x that of matched non-island ports") has no usable sample.
The primary arm has 32 Pacific events, but 50 of 62 Pacific ports average under 0.5 calls a day, where a
disruption cannot register; with >= 0.5 calls a day and 90 days of follow-up, 5 events remain at 5 ports from 3
storms, three of them Cyclone Harold during COVID's onset. Changes, all made before plan.md:

1. **Primary hypothesis = import concentration** (the lead's second claim, the critic's "genuinely new" part),
   tested on 94 events / 42 storms.
2. **The island comparison widened to all UN small island developing states** (18 events, 14 ports, 9 storms),
   with Pacific ports a reported subgroup. It is underpowered (plan section 8) and the plan says so.
3. **"Non-island" replaced by "not a small island developing state"**: Japan, the Philippines and Taiwan are
   islands, so the lead's term did not define a comparison.
4. **The lead's matched-comparison design replaced by a covariate-adjusted two-part model**, because with nine
   island storm clusters, matching would discard most of an already small sample; adjustment uses all of it.
5. **The forecast is scored about mid-September 2027, not July**, because the recovery window needs 135 days
   after the season's last possible event (30 April).

## D2 — 2026-10-17 00:02 NZDT — two flaws in the recovery algorithm, found by its tests before any real event

1. **False alarms.** "Disrupted if below the pointwise 5% band on any day 0-14" flagged 23% of simulated busy
   ports with no disruption: fifteen correlated chances to trip. Replaced by one familywise test - the deepest
   dip of observed over counterfactual in days 0-14 against the 5th percentile of the same statistic across
   the simulated paths. False alarms in the same test: 0 of 40.
2. **The COVID adjustment did nothing.** The reference-port index first entered with an estimated coefficient,
   fitted to pre-event years that contain no shared shocks; it came out near zero and absorbed nothing, so a
   global shock still read as storm damage. It now enters as an offset (coefficient 1), modelling the port's
   share of regional traffic, and a shared synthetic shock is absorbed (check 4 of test_recovery.py).
3. Also: the forecast-scoring script first left the counterfactual choice open ("own history now, reference
   index if refactored"). Reference-port selection is now a shared function, used identically for the
   historical events and the 2027 scoring.

## D3 — 2026-10-17 00:07 NZDT — traffic-scaled windows, and a simulation bug that would have hidden the problem

The first detectability run (fixed 7-day window) found that at 0.5 calls a day the method detected nothing -
not even a 28-day closure, which is about a one-in-a-million event by chance at that traffic. That was partly a
defect in the statistic: it looked only at the deepest 7-day window, zero-call weeks occur often enough by chance
that its threshold sat at zero, and a statistic floored at zero can never fall below zero. Recovery time failed
the same way, since the band's lower edge was zero. Windows now scale with traffic so that each holds about ten
expected calls (plan section 5). A test for a quiet port with a 28-day closure was added: 20/20 detected, 1/20
false alarms with no closure.

Fixing it exposed a second bug, in the simulation itself: its synthetic series ran 134 days after the event, too
short for a 21-day window, so quiet-port runs returned "short_followup" - and detectability.py skipped them while
still dividing by the full number of runs, silently scoring them as undetected. It would have reported zero
detection at low traffic for a reason that had nothing to do with detectability. The series now runs long enough
for the widest window, detection rates divide by valid runs, and a cell with any invalid run raises an error.

## D4 — 2026-10-17 00:16 NZDT — analysis.py crashed on first run: an untested code path

On its first run every model call failed: lifelines 0.30.3's WeibullAFTFitter.fit() has no `cluster_col` argument
(only CoxPHFitter does). test_recovery.py exercised the recovery algorithm but never analysis.py, so the bug
reached the real run. The error was caught per model, so only the descriptive tables were produced - those had
been seen when this was logged: small island states 1 of 17 events disrupted, other ports 27 of 68, Pacific 0 of 5.

The fix keeps what plan.md specified - errors clustered by storm - with the closest available implementation:
part A keeps statsmodels' cluster-robust covariance; part B's intervals come from a cluster bootstrap that
resamples storms (1000 draws). AIC uses no standard errors, so H1's preregistered decision quantity is unaffected
by this choice. A guard is added: with fewer than 3 disrupted small-island events, part B cannot estimate a
small-island time ratio, so H2 is reported as not estimable, which under plan section 6 is Inconclusive rather
than a number fitted to one event. A synthetic check of analysis.py is added to the tests before the rerun.

## D5 — 2026-10-17 00:35 NZDT — the forecast's part B drops the small-island indicator; made before forecast.py ran

plan.md section 7 puts the small-island indicator in both parts of the forecast model. The primary arm has one
disrupted small-island event (D4), so part B's coefficient for it would be fitted to a single recovery time, and
every Pacific forecast - all small-island ports - would inherit that one number. forecast.py now keeps the
indicator in part A (disrupted or not: 17 small-island events, 8 storms) and drops it from part B when fewer than 3
small-island events were disrupted, the same threshold as H2's guard. The model file records which covariates each
part uses, and score_forecast.py reads that list. forecast.py also now checks that the formula the scorer will use
reproduces lifelines' predicted median for every forecast row, so the 2027 score is computed from exactly the
frozen model. Made after H1/H2 were seen (they are in results/tables/primary.json) and before any forecast existed.

## D6 — 2026-10-17 00:36 NZDT — the 2026-27 forecast is frozen

forecast.py ran once, after D5. The two files below are committed now, before the season opens on 1 November 2026.
Before scoring, score_forecast.py prints the model file's sha256; it must match.

    forecast_model.json  0cbaa6e125ad071f05641a2c3ad58f096c4ad993bbef50220ed77ff6e43b8d25
    forecast_table.csv   26e6c7aa3693f2734372e5ca153d38c0daa8ee85b5d3fd19d0c7e73e635f45c3

12 Pacific island ports x Category 3/4/5 x 25/75/125 km = 108 rows. Benchmarks recorded in the model file:
historical share disrupted 0.329; historical median recovery among disrupted events 5.5 days.

## D7 — 2026-10-17 00:37 NZDT — post-hoc detectability checks, written after the results were seen

The preregistered results run against the lead: higher import share, and being a small-island port, go with
FEWER detected disruptions. The obvious worry is detectability. Part A's control for it is log mean daily calls,
a straight line, while the simulation shows detection power is a steep threshold in traffic. code/supplementary.py
(written now, before it is run) gives each event its simulated power to detect a 7- and 14-day closure (S1),
refits part A with that power as the control (S2) and on high-power events only (S3), and writes the Pacific case
series with the shortest closure each port could have shown. These are labelled post hoc in the report and
change no verdict.

Addendum, same session: the first run of supplementary.py clamped power for ports below the simulated range
(0.25 calls/day) to the grid's lowest row, giving 0.38 to ports with 0.01 calls a day. Only the Pacific case
series column was affected (S1-S3 use computed events, all >= 0.5 calls/day); those ports now get no number.
