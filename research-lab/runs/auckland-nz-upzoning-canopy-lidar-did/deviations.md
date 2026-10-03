# Deviations and implementation details

The plan (plan.md) was committed in d5c6e85 at 2026-10-03 22:37 NZDT, before any 2013 or 2024 tile was processed.
Entries are timestamped with `date`.

## D1. One unit without an SA2 (2026-10-04 01:48 NZDT)

One analysis unit's centre falls outside the simplified SA2 and local-board polygons (a coastline gap). It is dropped,
leaving 163,303 units; 160,209 of them are in strata with both high-dose and Single House units.

## D2. Long difference added after seeing the results (2026-10-04 01:48 NZDT; code/secondary_trend.py)

**Why.** Mean canopy is 3-4 pp higher at E1 (2016-18) than at both E0 and E2 in every zone. That suggests an
epoch-specific measurement difference. The E0 -> E2 long difference (2013 -> 2024) avoids E1 altogether, so it is
reported as a post hoc estimate.

**Result.** High dose -0.54 pp (95% CI -0.94 to -0.14); low dose -0.24 pp (-0.61 to 0.13). These are superseded:
with the corrected data (D4) the high-dose long difference is -0.48 (-0.88 to -0.08).

**Preregistered secondaries.**

- Trend-adjusted estimate (beta_post minus beta_pre x 7.36 / 3.74 years): -3.0 pp. It is withdrawn (D5). It assumes the pre-period trend
  would have continued, which an E1 artefact would make invalid.
- Annualised rates: -0.19 pp per year post and +0.22 pp per year pre.

## D3. Tiles without ground points (2026-10-04 01:48 NZDT)

Three tiles have no class-2 points and produced no cells; they are likely water or harbour tiles:

- NZ16_NAuckland CL3_BA32_2016_1000_1204;
- NZ24_Auckland CL2_AZ31_2024_1000_4947;
- NZ24_Auckland CL2_BA32_2024_1000_1204.

## D4. 2024 overlap points kept: undeclared until review (2026-10-04 02:13 NZDT)

- **The plan's intent.** Plan section 3 drops overlap points in every epoch.
- **What happened.** The 2013 and 2016-18 tiles mark overlap as class 12, which was dropped. The 2024 tiles are LAS
  1.4 point format 6, which marks overlap with a flag that process_tiles.py did not test. 2024 overlap points (about
  45-55% of points) were therefore kept.
- **Correction (reprocessing completed 2026-10-04 03:44 NZDT).** process_tiles.py gained a "noov" option that also drops flagged overlap points for formats >= 6,
  and all 2024 tiles were reprocessed into data/cells/2024_noov.
- **Which version is primary.** The overlap-free version is the faithful implementation of the plan and is reported
  as primary. The originally processed version is kept as a sensitivity.

## D5. Regression to the mean in the preregistered strata (2026-10-04 02:13 NZDT; found in review; code/review_checks.py)

- **The problem.** The preregistered strata include the E1 canopy band, while both outcomes are differences from
  E1. Conditioning on the start epoch of a difference induces regression to the mean (Oldham 1962; Daw & Hatfield
  2018).
  - It biases the post (E1->E2) high-dose estimate negative and the pre (E0->E1) estimate positive, as mirror images.
  - Matching on the end epoch (E2 band) flips the sign, which a real treatment effect cannot do.
- **Re-estimates.** The post, pre and long differences are re-estimated with:
  - no canopy band;
  - an E0 band;
  - an E2 band (placebo);
  - an endpoint-mean band (Oldham), which matches each difference on the mean of its two epochs;
  - the endpoint-mean band plus the change in raw point density.
- **How these are reported.** The preregistered estimate is reported for the record, labelled as not causally
  interpretable. Applying the preregistered decision rule to the artefact-free specifications is a post hoc
  sensitivity, not the preregistered verdict.
- **The trend-adjusted estimate (-3.0 pp, a preregistered secondary) is withdrawn.** It extrapolates the artefactual
  pre-trend.
- **The mechanism split** conditions on redevelopment, itself an outcome of upzoning. It is now reported under
  endpoint-mean strata and as a descriptive Kitagawa decomposition.

## D6. Tile-seam double counting (2026-10-04 02:13 NZDT)

1 m cells whose points lie exactly on a tile edge appear in both adjacent tiles, so their counts were summed twice.
About 5.9% of 2016-18 units, and one 2013 unit, have n_valid above 900, at most 912.

The review checks rescale each unit's counts so that n_valid is at most 900. Rescaling cannot change canopy shares,
so the double counting is bounded rather than removed. At most 12 of 900 cells (1.3% of the denominator) are counted
twice with the same canopy flag. The share bias is therefore at most 1.3% x |strip share - unit share|, typically
well under 0.1 pp, and unrelated to zone. Removing it would need a per-1 m OR across tiles, which was not done.

## D7. Wording and assumptions (2026-10-04 02:13 NZDT)

- **Zone-boundary fixed effect.** It is the 500 m grid block of the nearest boundary point, not "boundary-segment
  pairs".
- **E1 capture years** (north 2017.5, south 2016.75) are assumptions, used only for annualisation.
- **Point density differs by epoch.** Tile-header density, before overlap points are removed, is about 4 points/m2
  at E0 and 16-19 at E1 and E2. Effective density after removal, from six tiles, is about 2 (E0), 5-24 (E1) and
  about 10 (E2). The
  review found that thinning lowers detected canopy by about 1 pp per halving, so no epoch pair is
  density-comparable.
