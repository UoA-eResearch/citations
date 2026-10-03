# Did Auckland's 2016 upzoning cost tree canopy?

*A preregistered comparison of tree canopy from three city-wide LiDAR surveys (2013, 2016–18, 2024) on residential land upzoned to Mixed Housing Urban or Terrace Housing and Apartment Buildings versus matched Single House land*

Run directory: `research-lab/runs/auckland-nz-upzoning-canopy-lidar-did` · Preregistration: [`plan.md`](plan.md) ·
Every departure from it: [`deviations.md`](deviations.md) · 4 October 2026, revised after independent review

## In plain terms

Auckland's 2016 Unitary Plan allowed terraces and apartments on large areas of existing suburbs, while other areas
stayed zoned for single houses. A common worry is that building more homes on the same land costs trees.

We measured tree cover taller than 3 metres on built-up residential blocks, using three laser scans of the whole city
(2013, 2016–18 and 2024). We compared blocks that were upzoned with blocks kept for single houses.

**The comparison we planned first is misleading.** It matched blocks on their 2016–18 tree cover, and found upzoned
blocks lost 1.3 percentage points more cover by 2024. But the same comparison showed them gaining 0.8 points more
before the upzoning took effect. That mirror image is the signature of a statistical artefact called regression to
the mean, not a real effect. The plan's pre-trend check caught it.

**Better comparisons find little or no extra loss.** Comparisons that avoid the artefact put the extra loss on upzoned
land between about 0.4 points and nothing. Their uncertainty includes zero, and they rule out a difference of one
point.

**Redevelopment itself does remove trees.** Redeveloped blocks lost about 6–8 points of cover in every zone. Upzoned
land was redeveloped about twice as often, which explains most of the small raw difference.

**Why the verdict stays open.** The scans are not directly comparable: the 2013 scan has about a quarter of the later
scans' point density, and part of 2024 was flown as leaves were falling. So by the preregistered rule the verdict is
inconclusive.

## What was done

**Plan.** The plan was committed (d5c6e85) before any 2013 or 2024 data were processed.

**Canopy measurement.**

- Classified LiDAR point clouds from OpenTopography's mirror of LINZ and Auckland Council surveys: 6,822 tiles,
  about 133 GB, processed one tile at a time and then deleted.
- A 1 m cell counts as canopy if it holds a vegetation-classified point at least 3 m above ground.
- Overlap and noise points are dropped. In 2024 overlap is marked by a flag rather than a class; that was fixed after
  review (D4).

**Units.**

- 30 m grid cells lying at least 90% in one residential zone, covered in all three scans, and built up (at least 10%
  building cells) in both 2013 and 2016–18.
- That gives 163,285 units, of which 160,193 fall in matched strata.

**Groups.**

- Upzoned: Mixed Housing Urban + Terrace Housing and Apartment Buildings (51,511 units).
- Control: Single House (28,258 units).
- Mixed Housing Suburban is a lower dose.

**Model.**

- Change in canopy share between scans, regressed on zone.
- Stratum fixed effects: local board × distance to the city centre × 2016–18 survey block × **2016–18 canopy band**.
- Distance to the nearest train station as a covariate.
- Standard errors clustered by SA2 (525 clusters).

**Decision rule.**

- **Supported:** the post-period (2016–18 → 2024) estimate ≤ −1.0 pp with its CI below 0, and the pre-period
  (2013 → 2016–18) estimate within ±0.5 pp.
- **Contradicted:** the CI's lower bound > −1.0 pp, with the pre-period check passing.
- **Inconclusive:** otherwise.

## Preregistered result

| | Upzoned vs Single House (pp) | 95% CI |
|---|---|---|
| **Post: 2016–18 → 2024** | **−1.32** | **−1.65 to −0.98** |
| **Pre-trend: 2013 → 2016–18** | **+0.83** | **+0.49 to +1.17** (fails the ±0.5 check) |

**Verdict: Inconclusive.**

The originally processed 2024 data, with overlap points kept, give −1.37 and +0.83 (D4).

**This estimate is not causally interpretable.** The plan matched units on their 2016–18 canopy band, while both
outcomes are changes *from* 2016–18 (D5). Blocks matched at an unusually high 2016–18 reading tend to fall back
afterwards and to have risen before. Upzoned and Single House blocks sit at different points of the canopy
distribution, so this regression to the mean shows up as a negative "post effect" and a mirror-image positive
"pre-trend".

The preregistered trend-adjusted estimate (−3.0 pp) extrapolates that artefact and is withdrawn.

## What the data show once the artefact is removed

These analyses were added after review (D5) and are post hoc. All use the corrected 2024 data. The estimate is
upzoned vs Single House, in pp, with 95% CIs.

| Matching on canopy | 2016–18 → 2024 | 2013 → 2016–18 | 2013 → 2024 |
|---|---|---|---|
| 2016–18 band (preregistered) | −1.32 (−1.65 to −0.98) | +0.83 (+0.49 to +1.17) | −0.48 (−0.88 to −0.08) |
| No canopy band | 0.00 (−0.40 to +0.41) | −0.42 (−0.74 to −0.09) | −0.41 (−0.82 to 0.00) |
| 2013 band | −1.11 | −0.46 | −1.57 |
| 2024 band (placebo) | **+0.75** | +0.59 | +1.35 |
| Mean of the two scans compared (Oldham) | −0.37 (−0.74 to 0.00) | +0.28 (−0.04 to +0.60) | −0.03 (−0.46 to +0.40) |
| Oldham + change in point density | −0.22 (−0.57 to +0.12) | +0.04 (−0.25 to +0.32) | −0.02 (−0.46 to +0.41) |

**Matching on the start of a change pushes the estimate down; matching on its end pushes it up.** With a 2024 band
the "effect" becomes +0.75, and a real treatment effect cannot flip sign like that.

**Specifications that avoid the artefact give −0.4 to 0.0 pp for 2016–18 → 2024.** These are no canopy band, or
matching on the mean of the two scans compared. Their pre-period estimates are small, and they rule out a 1-point
excess loss. Applied post hoc, the preregistered rule would read "Contradicted" for all three of these
specifications. That is a sensitivity analysis, not the study's verdict.

**The lower dose behaves the same way.** For Mixed Housing Suburban, −0.84 under the preregistered strata becomes
−0.25 (Oldham) and −0.11 (no band).

## Redevelopment

| Post hoc, corrected data | Estimate |
|---|---|
| Not-redeveloped upzoned blocks vs Single House (Oldham strata) | +0.01 pp (−0.33 to +0.34) |
| Redeveloped upzoned blocks vs Single House (Oldham strata) | −2.46 pp (−3.70 to −1.21) |
| Mean canopy change on redeveloped blocks: Single House / upzoned / lower dose | −6.5 / −8.1 / −7.3 pp |
| Share of blocks redeveloped (building share changed ≥ 10 points): upzoned / Single House | 10.8% / 5.4% |
| Raw upzoned − Single House gap, 2016–18 → 2024 | −0.33 pp |
| … due to more redevelopment (Kitagawa composition) | −0.28 pp |
| … within redevelopment status | −0.05 pp |

Redevelopment removes trees wherever it happens, and upzoning roughly doubled how often blocks were redeveloped.
Redevelopment is itself an outcome of upzoning, so this split is descriptive, not a separate causal effect.

## The surveys are not like-for-like

Average canopy is 3–4 points higher in the 2016–18 scan than in both 2013 and 2024, in every zone.

- **2013 under-detects canopy.** Its tiles have about 4 points/m², against 16–19 in the later scans. Thinning the
  later scans lowers detected canopy by about 1 point per halving of density, so 2013 under-detects by roughly
  3–4 points.
- **2024 may read low for seasonal reasons.** The fall from 2016–18 to 2024 happens despite higher density, so it
  reflects real change, season (part of 2024 was flown in May and June, as leaves fell) or vendor classification.
- **Density differs by zone.** Upzoned blocks sit in denser 2016–18 tiles within strata. Adjusting for density
  change moves the artefact-free estimates further toward zero (table above).

## Limitations

- **Zoning was not random.** Upzoned land is nearer centres and transit. The zone-boundary comparison, units within
  100 m of a Single House / upzoned boundary, gives +0.13 pp (−0.43 to +0.69) for 2016–18 → 2024.
- **Timing.** The 2016–18 baseline straddles the plan's start in November 2016, and intensification rules from 2022
  may have reached Single House land late in the window.
- **Current zoning.** The current zoning layer was used, not a reconstruction of 2016 zoning.
- **Tile-seam double counting** affects up to 12 of 900 cells in 6% of units (D6). It changes estimates by less
  than 0.01 pp.

## Independent review

An independent reviewer re-processed six tiles from scratch and matched the stored counts exactly. The review judged
the study "fix first":

- it found the regression-to-the-mean artefact, and the matching table that exposes it;
- it found the undeclared handling of 2024 overlap points (D4), which was then reprocessed;
- it found the point-density differences between surveys;
- it required the trend adjustment to be withdrawn and the redevelopment split to be presented descriptively.

All are included above and logged in deviations D4–D7. The code is in `code/review_checks.py`.
