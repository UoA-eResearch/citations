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
