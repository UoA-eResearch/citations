# Adversarial review: port-cyclone recovery (pre-review draft 1ad81ca)

Reviewer: Fable 5.1, 2026-10-17. Scripts, logs, plots and CSVs are under `review/reviewer_checks/`
(`check_events.py`, `check_h1.py`, `check_forecast.py`, `check_recovery_events.py`, `placebo.py`,
`partial_sim.py`, `borderline_seeds.py`, `check_arms.log`). Nothing outside `review/` was modified.

## Recommendation: fix first

The preregistered verdicts stand (H1 Inconclusive, H2 Inconclusive) and every number I recomputed from the
results files matches. The pipeline ran in the order the commits claim. But the report's strongest surviving
claim, its plain-language summary, and its interpretation of the import-share sign are not supported as
worded, and three things the report leans on turn out differently when checked against the data rather than
the simulation:

- **The "two-week complete closure would have been seen" claim rests on power averaged over 17 events, 11 of
  which never saw hurricane-force winds at the port.** At the two measurable ports Melissa hit directly,
  event-specific power for a complete 14-day closure is 0.27 (Santiago de Cuba) and 0.77 (Montego Bay). The
  claim holds for four events, not seventeen.
- **The real false-alarm rate is 10.5%, not "3–10%".** Running the identical pipeline (with the reference index)
  at storm-free placebo dates flags 27 of 258 runs, rising to 16% at ports above 2 calls a day, with spurious
  "recovery times" of median 33 days (10 of 27 censored at 120). Roughly 7 of the 27 non-SIDS detections are
  expected false alarms. The small-island detection rate (1/17) equals the small-island placebo rate (3/49).
- **Import share is a country-size variable.** It correlates −0.79 with log(number of PortWatch ports in the
  country); adding that one covariate reverses the share coefficient's sign in the primary arm (+2.6, p = 0.24)
  and erases it in the Cat 1+ arm (−0.37, p = 0.72). The report's two mechanisms ("ships cannot divert",
  "residual detectability") are not the leading explanation.

None of this needs recovery.py rerun. The fixes are to report.md/report.html, deviations.md, score_forecast.py
and a supplementary table or two. After them, publish.

## Issues

### 1. The headline surviving claim overreaches (report §"What this does and does not show", §H2, §Post hoc, "In plain terms")

The report says: "at the small-island ports busy enough to measure, complete closures of two weeks or more …
were not what happened … The method's power for such a closure was about 0.95, and 16 of 17 events showed no
disruption at all."

Two findings against it.

(a) *Exposure.* Using IBTrACS's USA 64-kt wind radii (quadrant of the port at closest approach), only 6 of the
17 small-island events had the port inside hurricane-force winds, against 23 of 57 non-SIDS events with radii
available (`check_events.log`, `exposure_primary_ok.csv`). Harold's three Fiji/Tonga events were 103–115 km
from the eye with R64 of 70–74 km; Beryl's Kingstown, St George's and Montego Bay events were outside R64; so
were Fiona/Providenciales, Ian/Mariel and /La Habana, Rafael/La Habana. "Category 3+ within 150 km" is the
storm's intensity, not what the port experienced. Inside R64: SIDS 0/6 disrupted vs non-SIDS 14/23 (Fisher
p = 0.017). Outside: 1/11 vs 8/34 (p = 0.42). The small-island gap is real but it rests on six direct hits.

(b) *Event-specific power.* I simulated closures under each event's own fitted counterfactual, window and
threshold (300 paths, `sids_event_power.csv`). Mean power for a complete 14-day closure is 0.93 (the report's
grid interpolation gives 0.95; they agree). But per event: Santiago de Cuba/Melissa 0.27 (window 27 days,
threshold 0.17), Montego Bay/Melissa 0.77, Montego Bay/Beryl 0.86. For a 10-day complete closure the mean is
0.81 and six events are below 0.75. Santiago de Cuba's calls were *above* its counterfactual after Melissa
(dip ratio 1.28: a burst of calls on days 10–15, consistent with relief shipping), which is not evidence of
no closure at a port with 0.55 calls a day.

Fix: restate the claim as what it is. Of the six measurable small-island ports inside hurricane-force winds,
four (Nouméa/Niran, Apra Harbor/Mawar, Kingston/Beryl, Mariel/Rafael) had power ≈ 1 for a two-week complete
closure and showed none; at the two Melissa direct hits (Montego Bay, Santiago de Cuba) the method could not
have seen one. Add the per-event power table (complete 7/10/14/21 days; halved 14/28 days) to the case series
or supplementary.json, and the R64 exposure column to recovery_events.csv or a supplementary table. Replace
"about 0.95" with the per-event range.

### 2. Import share is a proxy for how few ports the country has (report §H1, §Post hoc, §"does not show")

PortWatch's `share_country_maritime_import` is a within-country share, so a port in a one-port country has
share 1 by construction. Across the 85 events, corr(share, log n_ports_in_country) = −0.79; corr(share,
SIDS) = 0.59. Adding log(ports in country) to part A gives share +2.65 (p = 0.24) and log_nports +1.26
(p = 0.008): ports in countries with many PortWatch ports (China 18 events, US 12, Japan 8, Taiwan 7,
Philippines 6) were more often detectably disrupted. In the Cat 1+ arm (n = 435) the same covariate takes
share to −0.37 (p = 0.72). With share and SIDS together, both lose significance (p = 0.21 each). Disruption
rate by region: E/SE Asia 15/45, USA 9/12, SIDS 1/17, other 3/11.

So the consistent negative sign the report reads as "ports carrying more of their country's imports were less
often detectably disrupted" is at least as well described as "ports in China, the US and Japan were more
often detectably disrupted than ports elsewhere". Candidate reasons the report does not list: typhoon-season
operating rules (Chinese and Japanese ports close pre-emptively on signal, which is exactly a short, clean,
detectable dip), AIS density and PortWatch polygon quality, storm type (landfalling typhoons at 10–60 km vs
hurricanes passing 70–115 km offshore), relief shipping raising calls at disaster-hit island ports, and the
model misfit at busy ports found in issue 4.

Fix: add this confound to §H1 and §Post hoc (it is a one-line logistic refit; label it post hoc), list the
alternative mechanisms, and weaken "That fits one of the two mechanisms plan.md set out in advance" to a
statement that the sign is not interpretable as a port-level import-concentration effect.

### 3. ΔAIC = 2.33 is inside the noise, and the report should say so (report §H1, Verdict)

A port-level permutation of share (400 shuffles; preserves storm clustering and repeated ports) gives a null
ΔAIC with 90th percentile 3.8, 95th 6.0, 99th 11.7; P(null ≥ 2.33) = 0.15; 16% of shuffles land in the
Inconclusive band and 2% reach "Supported". The clustered Wald p of 0.032 for the part-A coefficient is
therefore optimistic (the naive p is 0.031; clustering by storm barely moves it, because the share variation
is between ports within the same storms). "Inconclusive, close to Refuted" should read "Inconclusive, and
indistinguishable from a null model by permutation". In the Cat 1+ arm the permutation p is 0.003 for
ΔAIC 9.5, so there is a real association there, but issue 2 says what it is.

Fix: report the permutation p beside ΔAIC; drop "close to Refuted".

### 4. Real false alarms are 10.5%, rising with traffic, and long (report §How it was done, §H2, F1 caption; plan §4.3)

Placebo test (`placebo.log`): the 85 computed primary events rerun at d0 ± 365 and ± 200 days, skipping
placebo windows with any Cat 1+ storm within 250 km. 258 valid runs; 27 flagged (10.5%, 95% CI 7–15%) with
the reference index, 25 (9.7%) own-history. By traffic: 0.5–1 calls/day 7.7%, 1–2 5.5%, 2–5 15.6%, >5 16.0%.
By group: non-SIDS 11.5%, SIDS 6.1%. The simulation (F1) has the opposite traffic gradient (2–6% at busy
ports) because it draws iid NB noise; the real series at busy ports have serially correlated level changes
(Yantian, Shekou, Mawan, Hong Kong, Naha, Kinwan, Henza all fire at placebo dates). 55 of 85 fitted
dispersions are ≤ 1e-4 (the NB MLE goes to the Poisson boundary, or `fit_nb` falls back after
non-convergence), so the band is Poisson-narrow. Spurious recovery times at placebo dates: median 33 days,
10 of 27 censored at 120, not the "10–16 days" of plan §4.3.

Consequences the report must state: at 10.5%, ~9 of 85 detections are expected false alarms, ~7 of the 27
non-SIDS ones; the non-SIDS median of 6 days and p90 of 34 are computed over a mixture; the 1/17 small-island
detection rate equals the small-island placebo rate (3/49), which is the cleanest statement of "nothing to
time" available and stronger than "about the method's false-alarm rate".

Fix: add the placebo check (it is cheap and uses only committed code) as a post-hoc deviation; correct
"False alarms run at 3–10%" (the simulation itself gives 2–15% by cell, 12% at 0.25 calls/day); state the
expected false-alarm count among detections; note the iid-noise limitation of F1.

### 5. The D4 guard changed the verdict the fixed code would have produced; disclose the counterfactuals (deviations D4; report §H2, §Process)

The guard (`MIN_SIDS_DISRUPTED = 3`) was written after the descriptive table (1 of 17) was seen, so any
threshold ≥ 2 was known to trigger. I ran the alternatives:

- d12c3f0 code with only `cluster_col` removed (lifelines Wald CI): time ratio 0.40 (0.06–2.61) → **Inconclusive**.
- D4 code (storm bootstrap) with the guard removed: 253 of 400 draws fit; 95% interval 0.16–1.29 → **Refuted**
  (upper end below 2).
- A pooled estimand (mean recovery days including zeros, SIDS/non-SIDS): 0.12 vs 5.84 days, ratio 0.02
  (storm-bootstrap 0.000–0.097) → Refuted by a wide margin.

The guard is scientifically defensible (a time ratio fitted to one event is meaningless), and it moved the
verdict *away* from the one favourable to the lab's framing, but it is post hoc and the report presents it as
"the preregistered guard (D4)". It was not preregistered; plan.md d12c3f0 has no guard.

Fix: in §H2 call it "the guard added in D4 after the descriptive table was seen", give the three counterfactual
outcomes above, and say plainly that the lead's directional claim (small-island ports slower) is refuted in the
pooled sense and untestable in the conditional sense.

### 6. Two of the three longest recoveries are two-hurricane events (results part B; report §H2 median/p90; forecast medians)

Lake Charles/Laura (T = 56) and Calcasieu Pass LNG/Laura (T = 60) were hit by Delta on day 43–44 (Cat 1 at
41 km; Cat 2 at 23 km). The Lake Charles plot (`figs/Lake_Charles_LAURA.png`) shows calls still at ≤ 1/day
against 2.3 expected when Delta arrived, so "56 days" is Laura-then-Delta. Beaumont, Port Arthur and Sabine
Pass recovered before Delta; Huizhou/Mawan before Koinu; Zhuhai before Matmo. No small-island event had a
second storm in its window. Part B's category coefficient (×3.2 per category step) is fitted to 11 Cat-4
events, five of them Laura, so the forecast medians inherit the compound events.

Fix: flag the two events in recovery_events.csv and the report; run part B with them censored at day 43 as a
sensitivity; mention second storms in "does not show".

### 7. Cebu/Rai's 120-day censoring is a level shift, not clearly a recovery (report F2, §H2 p90; forecast)

Cebu's monthly mean fell from 7.5–8.7 calls/day (Jun–Nov 2021) to 3.7–4.7 for all of 2022 (yearly mean 4.0
vs 7.1), recovered to 6.2 in 2023, fell to 4.0 again in 2024. Cebu is also flagged at a placebo date
(+200 days, T = 120). Rai damaged Cebu's ports and Omicron hit the Philippines in January 2022; which of these,
or a PortWatch counting change, kept calls at half for a year cannot be told from the series. It is the only
censored event in part B and sets the Weibull tail that puts nine forecast medians above 120 days.

Fix: say so in the report; give part B without Cebu as a sensitivity; label the >120-day forecast medians as
driven by one censored event and by extrapolation to Category 5 (no Cat 5 event is in the fitting data).

### 8. D5 changed the frozen forecast by a factor of about four; the report says only that it dropped a term (deviations D5; report §Forecast)

With the small-island indicator kept in part B as plan §7 specified, its coefficient is −1.90 (time ratio
0.15) and the Cat 4 / 75 km medians become: Port Moresby 4.0 (frozen 17.0), Lae 3.7 (16.5), Nouméa 6.2
(19.3), Suva 5.2 (18.1), Apia 12.2 (23.4). The frozen medians are *longer* than the historical non-SIDS
median because part B without the indicator applies the mainland category effect (issue 6) to island ports.
D5 is defensible, but it was made after H1/H2 were seen and it is the difference between forecasting
"about four days" and "about seventeen". The forecast.py edit (00:35:55) was committed together with its
outputs in 0c928af, not before.

Fix: state the magnitude and the alternative medians in §Forecast and D5; keep the frozen file as is.

### 9. The forecast table is a traffic ranking presented as a vulnerability table (report §Forecast; plan §11)

Part A's log_activity coefficient is 1.11, so "chance of a detectable disruption" is dominated by how busy
the port is (PNG ports top, Apia bottom). Sorting the table by that probability produces a port-by-country
ranking, which plan §11 said the report would not assemble.

Fix: sort alphabetically or by country; say that the probabilities mostly reflect detectability at each
port's traffic, not storm vulnerability; the same caveat belongs in the scoring plan.

### 10. The scoring procedure is not runnable as written without judgement calls (code/score_forecast.py, events.py; report §Forecast)

- `events.py` has `RAW` and `PROC` hard-coded to `data/raw` and `data/processed`; re-running it "on the 2027
  vintage" (step 2 of the docstring) either reads the sealed 2026 data or, if the scorer edits the path,
  overwrites the sealed `data/processed/events_all.csv`. `score_forecast.py` sets `E.RAW = raw` but then
  reads `E.PROC / "events_all.csv"`.
- Port covariates (`vessel_count_total`, `share_country_maritime_import`) and mean calls are taken from the
  2027 ports.csv/daily.csv, not frozen, so the scored p differs from forecast_table.csv for the same storm;
  the port set (≥ 0.5 calls/day over 2019–2027) can also change.
- The log-T error treats a censored T = 120 as observed; a 167-day median against a censored 120 is penalised
  0.33 when it should not be penalised at all.
- The Brier benchmark (historical share disrupted 0.329, all ports) is beaten by any low forecast whenever
  nothing happens: Brier 0.108 for the benchmark vs 0.006 at p = 0.08. The relevant climatology is the
  small-island rate (1/17 = 0.059) or the Pacific measurable rate (0/5). With one disruption in three events
  the forecast loses to the benchmark (0.29 vs 0.22). "Beats the benchmark" as defined is nearly automatic in a
  quiet season and nearly impossible otherwise.
- `hourly()` is applied to tracks truncated at the season boundary; a storm straddling 1 Nov or 30 Apr loses
  fixes.

Fix (allowed: the scorer is not frozen, the forecast is): take raw and output directories as arguments in
events.py; write the frozen per-port covariate rows into forecast_model.json and score from them; score
recovery with censoring (e.g. compare the forecast median with min(T, 120) only when the event is observed, or
use a censored log score); report Brier against both 0.329 and 0.059; interpolate full tracks then filter by
closest-approach date.

### 11. The detectability simulation differs from the real pipeline in the direction that matters (code/detectability.py; report F1, §Post hoc S1–S3)

The simulation draws iid NB noise at α = 0.25 and 1.0 with no reference index. Real fits give α ≈ 0 (so the
real band is narrower and real power for a complete closure is, if anything, higher than F1: event-specific
0.93 vs grid 0.95 for 14 days, 0.61 vs 0.66 for 7 days, so S1–S3 are not misled), but the real false-alarm
rate is 10.5% and rises with traffic (issue 4), because the real excess variation is serial, not iid. The
"traffic as a straight line" vs "power as the control" comparison in S2 is therefore a comparison between two
imperfect detectability controls; neither captures the busy-port misfit.

Fix: add the placebo false-alarm rate by traffic band as the empirical companion to F1; note that the
dispersion rows in F1 bracket neither the fitted α (≈ 0) nor the real false-alarm gradient.

### 12. Partial disruptions are mostly invisible, and the numbers belong in the report (report §"does not show" item 4; "In plain terms")

Simulation with calls thinned rather than zeroed (`partial_sim.log`): at 1 call/day, α = 0.25, calls halved
for 14 days are detected 53% of the time, for 28 days 47%; at 0.5 calls/day, 27% and 48%. Event-specific at
the 17 small-island events: halved for 14 days, mean power 0.45; halved for 28 days, 0.58; cut to a quarter
for 14 days, 0.77. Fifteen of the 17 events have power below 0.8 for a month at half capacity.

Fix: put these numbers in item 4 and in the plain-language summary.

### 13. Plain-language summary (report §"In plain terms")

- "If a port had been fully shut for two weeks, we would very likely have noticed": true on average (0.93),
  false at the two Melissa direct hits. Say "at most of them" and name the exceptions.
- "long, complete port closures were not what happened at the main island harbours we could see": restrict to
  the four harbours that took hurricane-force winds and were measurable with power near 1.
- "we almost never saw a disruption": add "the one we saw (Kingston, two days) is the same rate as at dates
  with no storm".
- "We worked out exactly how long a closure each port could reveal before looking at any result": the grid was
  pre-outcome; the per-port numbers (S1, case series) are post hoc (D7). Drop "exactly".

### 14. Monte Carlo noise in the disruption threshold (code/recovery.py)

The threshold is the 5th percentile of 2,000 paths drawn from one global generator, so it depends on event
order and carries simulation noise; at quiet ports the depth statistic is discrete. Re-running borderline
events with eight seeds (`borderline_seeds.log`): Shekou/Ragasa is disrupted in 7 of 8 seeds, Manila/Noru in
3 of 8 (study: not disrupted); Suva/Harold's threshold ranges 0.235–0.330 (no effect, dip 0.88). The
detection count is 28 ± 1. No small-island verdict is within noise of its threshold.

Fix: note it; for reproducibility, seed per event (e.g. `default_rng([SEED, hash(portid, date)])`).

### 15. Stale docstring in recovery.py

The docstring still describes a pointwise 7-day test ("falls below L_t on some day t in [0, 14]") and
recovery "after the first drop"; the code implements the familywise deepest-dip test with a traffic-scaled
window and starts recovery from the deepest dip (the variable is misleadingly named `first_drop`). plan.md §5
(d12c3f0) does state the deepest-dip rule, so the timing is clean; D2 discloses the test change but not the
start-point change. Fix the docstring and add one line to D2.

### 16. Numbers and wording to correct (report.md and report.html)

- Nuku'alofa, Cat 4 / 75 km: p = 0.0250 → "0.02", not "0.03".
- "False alarms run at 3–10%": the grid gives 2–15% by cell (12% averaged at 0.25 calls/day); real 10.5%.
- "deepest dip in the first two weeks": the window is days 0–max(14, k), up to 27 days at the quietest ports.
- "At one call a day, 78% … At half a call, 30%, and a two-week closure 85%": these are the α = 0.25 rows
  (α = 1: 63%; 15% and 76%). Say which dispersion.
- "the post-hoc power control halves the signal": the log-odds shrink from −2.54 to −1.61 (37%).
- The H1 table's per-arm odds-ratio intervals are not in primary.json or supplementary.json. I recomputed them
  (table below) and they are right; store them.
- The F2 title "Small-island ports almost never showed a detectable disruption" is accurate; consider adding
  "(the same rate as at storm-free dates)" once issue 4 is in.

### 17. The "does not show" list is incomplete (report §"does not show")

Add: (6) PortWatch counts AIS-equipped cargo and tanker vessels, so the small inter-island vessels that carry
much Pacific domestic supply are outside the data; (7) relief and naval shipping can raise call counts after a
disaster (Santiago de Cuba, Melissa); (8) a second storm inside the 120-day window (Laura→Delta); (9) the
strongest Pacific main-harbour hits predate PortWatch: Winston 2016 (Suva, Lautoka), Gita 2018 (Nuku'alofa),
Pam 2015 (Port Vila), not only Dorian 2019; (10) AIS coverage loss at the port, PortWatch revisions, and
anchorage calls not counted inside the port polygon; (11) category at closest approach excludes Judy and Kevin
at Port Vila (Cat 2 at approach, Cat 3–4 lifetime), though Port Vila is below 0.5 calls/day anyway.

### 18. The SIDS list and the Guam case (code/recovery.py SIDS; plan §10.6)

The code's 58-entry list is the UN-OHRLLS list plus Bahrain, which is no longer on it (verified at
un.org/ohrlls/content/list-sids: 39 SIDS incl. Singapore, Cook Islands, Niue; 18 associate members incl. Guam,
CNMI, Puerto Rico; no Bahrain). Immaterial here: Singapore and Bahrain have no events; Puerto Rico and USVI
appear only in the Cat 1+ arm (Dorian, Fiona at Cat 1). Worth a sentence: Apra Harbor is a US Navy base and
the three Guam/CNMI events plus Nouméa and Providenciales are territories of the US, France and the UK, so
"small island developing state" is the UN label, not a description of the port's resources.

### 19. Prior art (report §What was already known)

Verified: Verschuur, Koks & Hall (2020), *Transp. Res. D* 85, 102393, DOI 10.1016/j.trd.2020.102393; "median
disruption duration of six days with a 95th percentile of 22.2 days"; 141 disruptions, 74 ports, 27 disasters.
Their disasters include earthquakes and floods and their detection rule differs, so "the same as the main
earlier AIS study" should stay hedged as it is. arXiv:2509.22656 is "U.S. Port Disruptions under Tropical
Cyclones: Resilience Analysis by Harnessing Multiple-Source Dataset" (CyPort dataset; 145 principal US ports,
90 TCs, 2015–2023; 1,927 interaction records in the appendix) — correct. US DOT/MarTREC "Prediction of Port
Recovery Time after a Severe Storm" (Texas A&M, Aug 2023; AIS vessel counts; test storms Alex, Ian, Nicole 2022,
so Gulf *and* Florida Atlantic) — "Gulf of Mexico" is approximate. IMF WP 26/99 (May 2026, Arslanalp et al.,
validation includes Jamaica and Samoa) — correct. Add Verschuur et al. (2023), *Nature Climate Change*
(systemic port risk; names SIDS and Guam as most exposed), which is the closest prior work on small-island
port downtime, model-based rather than observed. I found no AIS/PortWatch recovery estimate for Pacific
island ports; the novelty claim stands.

### 20. Timing (git and mtimes)

Every output postdates the code that produced it: detectability.json 00:09:43 (simulation only) before plan
d12c3f0 00:10:26; recovery.csv 00:15:22; analysis.py fixed 00:27:27, test_analysis.py 00:17:05, committed
3c194e6 00:28:18, primary.json 00:35:14; forecast files 00:36:03, committed 0c928af 00:36:27; supplementary.py
committed 7ff8873 00:37:21, run 00:37:58 (the clamping addendum touched only the case-series column).
recovery.py, events.py, detectability.py and test_recovery.py are byte-identical to d12c3f0. Two caveats: the
D5 edit to forecast.py was committed with its outputs, not before them (issue 8); and the D4 guard is
post hoc (issue 5).

### 21. Spot checks of the event table (code/events.py)

Independent 10-minute great-circle interpolation on unit vectors (no unwrapping needed) agrees with the study
on all 16 events checked: distances within 0–6 km (Lake Charles 10.0 vs 4.2 km, from hourly linear
interpolation at a fast-moving landfall), categories identical, antimeridian cases (Suva, Lautoka, Nuku'alofa)
within 2.5 km. USA_SSHS/USA_WIND is present for every 2019+ fix in every basin (JTWC for SH/WP/IO), so the
category source is consistent across basins; it is 1-minute wind, so "Cat 3" here is not the Australian or
Fiji regional Category 3, which the report should say once. The reference-index construction is sound for
its purpose (COVID absorbed per test 4; event-specific reference sets are harmless because each event is
fitted alone; 24–343 reference ports), and the placebo shows it adds no false alarms over own-history
(10.5% vs 9.7%). Its exclusion covers only Cat 1+ storms in events_all.csv; other regional shocks at
reference ports are not excluded, which is a small, undirected noise source.

## Numbers recomputed

| quantity | report / results | recomputed | note |
| --- | --- | --- | --- |
| primary arm: events, storms, disrupted | 85, 34, 28 | 85, 34, 28 | recovery_events.csv |
| SIDS 1/17 (8 storms); non-SIDS 27/68; Pacific 0/5 | as stated | same | |
| ΔAIC primary (A, B) | 2.33 (+4.17, −1.84) | 2.335 (+4.171, −1.836) | own scipy logit + Weibull-AFT likelihoods |
| ΔAIC Cat 1+ | 9.52 | 9.52 | |
| part A share OR per 10 pp, primary | 0.78 (0.61–0.98), p 0.032 | 0.78 (0.61–0.98), p 0.032 | |
| … Cat 1+; ≤100 km; ≤250 km | 0.84 (0.73–0.97); 0.67 (0.40–1.12); 0.78 (0.65–0.92) | same | not stored in any results file |
| … own-history; excl. Mar–Jun 2020 | 0.79 (0.63–0.99) ×2 | same | |
| permutation P(ΔAIC ≥ 2.33), primary | — | 0.15 (400 port-level shuffles) | 95th pct of null 6.0 |
| permutation P(ΔAIC ≥ 9.52), Cat 1+ | — | 0.003 | |
| part A with log(ports in country) | — | share +2.65 (p 0.24); log_nports +1.26 (p 0.008) | corr(share, log_nports) −0.79 |
| part A share & sids together | — | share −1.45 (p 0.21); sids −1.60 (p 0.21) | matches forecast_model.json part A |
| part B share TR, bootstrap | 1.66 (0.17–670) | 1.660 | |
| H2 unguarded: lifelines CI / D4 bootstrap / pooled | not reported | 0.40 (0.06–2.61) / (0.16–1.29) / 0.02 (0.000–0.097) | Inconclusive / Refuted / Refuted |
| SIDS OR for disruption | 0.09 (0.01–1.43), p 0.09 | same | |
| Cat 1+ SIDS TR | 0.80 (0.15–3.89), 5/53 | same | |
| non-SIDS median T, p90, censored | 6, 34, 1 | 6.0, 33.8, 1 | |
| S1 mean power 7 d / 14 d, SIDS vs non-SIDS | 0.66/0.95 vs 0.86/0.98 | 0.655/0.948 vs 0.862/0.982 | grid interpolation |
| event-specific power 14-day complete closure, SIDS | — | mean 0.93; min 0.27 (Santiago), 0.77 (Montego Bay/Melissa) | 300 paths per event |
| event-specific power, calls halved 14 d / 28 d | — | 0.45 / 0.58 | 15/17 below 0.8 for 28 d |
| S2, S3 odds ratios | 0.85 (0.66–1.10); 0.09 (0.00–1.79); 0.79 (0.58–1.09); 1/6 vs 42% | same | |
| false-alarm rate | "3–10%" (sim 2–15%) | 10.5% (27/258) placebo, CI 7–15%; by traffic 7.7/5.5/15.6/16.0% | own-history 9.7% |
| placebo spurious T | plan: 10–16 d | median 33 d; 10/27 censored at 120 | |
| SIDS inside 64-kt radius | — | 6/17 (0 disrupted) vs non-SIDS 23/57 (14 disrupted) | Fisher p 0.017 inside; 0.42 outside |
| closest approach, 16 spot events | — | within 0–6 km; categories identical | incl. antimeridian |
| Pacific ports ≥0.5 / ≥1 / ≥2 calls/day of 62 | 12 / 5 / 1 | 12 / 5 / 1 | |
| 32 Pacific events: 5 ok, 26 low, 1 short follow-up | as stated | same | |
| 68 SIDS primary events: 17 ok, 49 low, 2 other | 49 quoted | 17 + 49 + 2 | |
| forecast table | hashes 0cbaa6e1…, 26e6c7aa… | hashes match; 108 rows re-derived, max error 3e-16 / 2e-13 | |
| forecast p range; medians > 120 | 0.003–0.56; "exceed 120" | 0.0032–0.558; 9 rows (all Cat 5 at 25 km) | no Cat 5 in fitting data |
| forecast medians if sids kept in part B | — | ×0.15 (Port Moresby 17.0 → 4.0) | D5 effect |
| Nuku'alofa Cat 4 / 75 km p | 0.03 | 0.0250 → 0.02 | rounding |
| Verschuur 2020 | TRD 85:102393; 6 d; p95 22 d | TRD 85, 102393; 6 d; 22.2 d; 141/74/27 | verified |
| UN SIDS list | "UN list" | 39 + 18; Bahrain not on it (code includes it) | immaterial |
| borderline detections, 8 seeds | — | Shekou/Ragasa 7/8 disrupted; Manila/Noru 3/8 | 28 ± 1 detections |
| second storm in window | — | Lake Charles & Calcasieu/Laura: Delta day 43–44 | T 56, 60 |
| Cebu yearly mean calls 2021→2022 | — | 7.1 → 4.0 (2023 6.2, 2024 4.0) | level shift |
| report.md vs report.html | — | all numbers present in both | |

## Answers to the twelve check items, in brief

1. Thresholds: the pipeline's thresholds were fixed before outcomes; the H2 guard (D4) and the part-B
   indicator drop (D5) were not, and D4's guard changed the verdict the D4 code would otherwise have given
   (Refuted → Inconclusive); D5 changed forecast medians about fourfold. Both defensible, both must be disclosed
   with their counterfactuals.
2. Event table: correct on all spot checks; category source consistent; SIDS list has Bahrain in error;
   Singapore/Bahrain immaterial; exposure (wind radii) is the missing variable.
3. Recovery algorithm: sound and matches plan.md; docstring stale; the deepest-dip start is in the plan;
   Cebu's censoring is a level shift of uncertain cause; Lake Charles/Calcasieu are two-storm events;
   threshold has Monte Carlo noise; Kingston/Melissa (2 days), Nouméa/Niran (dip 0.38 vs 0.30) and Montego
   Bay/Melissa (calls back within a week) reproduce.
4. Detectability: the simulation's iid noise gives a false-alarm gradient opposite to the real one;
   real rate 10.5%; a 50% reduction for two weeks is caught about half the time at 1 call/day.
5. H1: ΔAIC recomputed exactly; AIC with 34 clusters is overconfident and the permutation p is 0.15; the sign
   is a country-port-count effect; the report states the sign's interpretation more strongly than warranted.
6. H2: the 17 events are not comparable in exposure (6 vs 23 of 57 inside R64); the headline holds for four
   events; Melissa's direct hits are untestable at their traffic.
7. Post hoc: the power interpolation is correct (grid vs event-specific agree to 0.02); dispersion choice
   is moot at α ≈ 0; "power as the control" is a reasonable but still imperfect control; the report leans on
   S1–S3 appropriately but on "0.95" too hard.
8. Forecast: re-derived exactly; scoring not runnable without judgement (paths, frozen covariates, censoring,
   benchmark).
9. External: citations verified; add Verschuur et al. 2023; novelty stands.
10. Scope: the report does not call island ports resilient, but its surviving claim is worded so that a reader
    would; the "does not show" list needs items 6–11 above; the forecast table is a de facto ranking.
11. Numbers: all match except Nuku'alofa's rounding and the false-alarm range.
12. Plain terms: overstated in the three sentences quoted in issue 13.
