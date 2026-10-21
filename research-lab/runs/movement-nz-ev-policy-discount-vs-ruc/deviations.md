# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-20 21:33 NZDT — data coverage, a placebo year added, and the prior preprint

Recorded after the registration series was built and before any effect was interpreted.

1. **The register service runs to September 2026, not March.** NZTA's ArcGIS service is named `MVR_Mar26` but
   carries first registrations through September 2026, so the window is 2021-01 to 2026-09 (1,419,410 light-vehicle
   first registrations) rather than ending in early 2026. That is 2.5 years after the road-user-charge change,
   which lets the report follow the recovery as well as the shock.
2. **A fourth placebo year.** The plan named placebo difference-in-differences at 1 April 2022, 2023 and 2025. The
   code also runs 2026, because the window reaches it. It is reported with the others and, as it happens, is the
   largest of them.
3. **Closest prior work could not be read in full.** The novelty recheck found a 2026 Research Square preprint
   (rs-11080967) estimating the Clean Car Discount's removal by regression discontinuity in time, reported as an
   immediate and lasting fall of about 24 percentage points in battery-electric share. Only its title was
   retrievable, so this study compares against the figure reported in secondary sources and does not claim
   priority on the Clean Car Discount effect. Its "lasting" characterisation is testable here, because this window
   extends to September 2026.
4. **Everything else is as preregistered**: the groups, the two events, both hypotheses and their decision rules,
   the estimation window for the baseline, the donut around April 2024, and the block bootstrap.

## D2 — 2026-10-21 17:57 NZDT — after independent review

An independent adversarial review (`review/review.md`) matched the counts to NZTA's service cell for cell and
reproduced both Inconclusive verdicts exactly. No pipeline code or result table changed. Each figure taken from the
review was checked against its outputs, and the preprint claim against OpenAlex, before use.

1. **The prior preprint was readable all along.** D1 item 3 said only the title of Hoang (2026, Research Square
   rs-11080967) could be retrieved; OpenAlex lists an open-access PDF (CC BY), verified here. The preprint does quantify
   pull-forward (1,206 vehicles in the final eight weeks), uses weekly registrations to December 2025 split by fuel
   type (including plug-in hybrids) and by new versus used import, and does not
   consider road user charges. The report's prior-work section and its claim that no study had quantified the
   December 2023 pull-forward are corrected; the separation of the two shocks remains new.
2. **"It did not last" is withdrawn.** Over the preprint's window the plug-in share averaged 6.6% (January 2024 to
   December 2025) against 13.4% before, consistent with "lasting". Recovery begins in March 2026, after that window;
   "back to 18–22%" was 13.7–21.7% by month, and a nine-month total had been compared with a twelve-month one.
3. **H1's "about a tenth" is replaced by a range.** The ratio runs from 0.09 to 0.46 across defensible baselines, the
   preregistered one being the most aggressive extrapolation; the argument against H1 rests on a break-even, which is
   now given, and on the minimum detectable effect (about 1.0), now reported.
4. **H2 is confounded as well as underpowered**: the rebound from the January trough, the battery-electric versus
   plug-in hybrid contrast, a broader placebo distribution, contamination of the control by mild-hybrid utilities, and
   the opposite-signed market-share version. The draft's placebo dates were described as policy-free; they are not.
5. **Preregistered analyses the draft omitted**: H1 on new vehicles only (plan §5.1), a market-share outcome for H2,
   and the minimum detectable effect for H1, all reported from the review's reanalysis.
6. **The ute series** now counts diesel utilities of 3,500 kg or less; the study's universe includes about 37,300
   heavier vehicles, which do not affect H1 or H2.
7. **Snapshot attrition** is quantified against NZTA's May 2023 snapshot (the April 2021 service suggested in the review brief does
   not exist): about a point a year, too small to drive the results.
8. **D1 item 1 was not a deviation**: the plan already specified September 2026.

## D3 — 2026-10-21 18:10 NZDT — confirmation pass

The confirmation review (publish with edits) found every revised number matched. Corrected here: the prior preprint
includes used imports and plug-in hybrids (verified against its text), so this study's additions are the road-charge
separation, the combined plug-in treated group and the data to September 2026; it is described as a preprint not yet
peer-reviewed; the one point of disagreement (petrol and diesel registrations at the deadline) is stated; F2's title and
F3's caption were regenerated (F3 no longer calls the placebo dates policy-free); and smaller wording fixes. The review's
scripts and raw service outputs are committed under `review/reviewer_checks/`, except its excerpts of the preprint's
text.
