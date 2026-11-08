# Review: ecology-biodiversity-herbarium-velocity-effort-null

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py/.txt`: independent null re-implementation, Pareto inclusion probabilities, effort-surface displacement,
ratio statistics; `absorption_test.py/.txt`: synthetic identification test). Checks used `venv/bin/python -I` with
`code/velocity.py` imported; the primary was not re-run in full.

## Verdict: fix first

The computation is right and I could reproduce it: an independent plain-loop implementation of both nulls on 150
random species matches the stored null medians (correlation 0.998 noise, 0.999 effort; median absolute difference
0.08 and 0.11 km/yr), the hand traces are genuinely independent (pandas filters, explicit thinning, haversine), the
cleaning counts reconcile, every number in the report matches its table, and the timeline holds (D2 committed
09:14:14, `clean.parquet` 09:13:45, `observed_primary.parquet` 09:15:44). What does not hold is the interpretation
that the preregistration, title and plain-terms section put on the effort null. The null's effort surface is the
thinned records of all other species, so it contains their range shifts; it cannot tell "collectors moved" from
"plants moved together". A synthetic world in which every species really moves 1° north under uniform effort is
scored by this null as 99% reproduced with 7% exceedance, i.e. as no movement at all. H1 is therefore "Supported"
only in the literal sense that the statistic cleared 0.5; the claim that fixed ranges plus noise and effort
reproduce two-thirds of the velocity is not identified by the design. The noise-only null (ratio 0.41) is the part
that is.

## Findings

### 1. (Major) The effort null absorbs real coordinated range shifts; "keeps every range fixed" is not what it does

Evidence: `absorption_test.txt`. Using the study's own `velocity.py` on synthetic data (300 species, 150 records
each, ranges 40–50°N, collecting effort uniform and identical in both periods):

| world | group | observed | noise null | effort null | ratio (effort) | exceed p95 |
|---|---|---|---|---|---|---|
| none move | all | 1.82 | 1.89 | 1.90 | 1.04 | 0.05 |
| all move 1° N | movers | 4.33 | 1.88 | 4.27 | **0.99** | **0.07** |
| half move 1° N | movers | 4.20 | 1.89 | 3.08 | 0.73 | 0.20 |
| 20% move 1° N | movers | 4.12 | 1.85 | 2.67 | 0.65 | 0.22 |

With no effort change at all, a real shift shared by many species is reproduced by the "effort" null in proportion
to how many share it, because the leave-one-species-out surface is built from the other species' records, which
moved. The study's own `test_effort.py` scenario is the same data as scenario B relabelled: "P2 collecting
concentrated in the north" and "every range moved north" are indistinguishable to this null. The observed ratio
of 0.67 is what scenarios C–D produce with uniform effort, so the report's "With no real movement at all, this
produced 4.6 km a year" and "most of the headline speed is noise and changing collecting effort" are not supported
as causal statements, and the 36% exceedance is a lower bound on species with real movement, not an estimate.

What the data do identify: (a) the noise-only null, 2.8 km/yr, ratio 0.41 (0.40–0.41); (b) the poleward
component. The effort null's median poleward displacement is 0.3 km against 9.4 km observed, and the effort
surface itself moved only mildly poleward (effort-weighted mean |lat| 30.2° → 31.6°; tropical share of units
33.8% → 30.9%, boreal 10.7% → 13.0%, `checks1.txt` §2), so whatever coordinated signal the null absorbs is not a
predominantly poleward one. The median poleward excess, 9.4 km per 28 years (0.34 km/yr), is the one directional
real-shift figure the study can state.

Fix: rewrite the title and verdict around the identified quantities ("at least 41% is sampling noise; a further
26% is reproduced by the redistribution of all other species' records, which mixes collecting effort with shared
range shifts"); add the synthetic absorption table to the report; present the poleward numbers as the identified
shift; move "The effort null may absorb some real movement" from a caveat to the main limitation. An effort proxy
that does not move with plants (collecting events per cell from non-plant or all-kingdom specimens, or
institution-level digitisation counts) would be the real fix and is out of scope here.

### 2. (Moderate) Pareto order sampling does not reach the stated inclusion probabilities for small species

Evidence: `checks1.txt` §3. For three real species with n = 27–51 records, 5,000 draws give empirical inclusion
probabilities whose maximum deviation from the stated target n1·s1/(n1·s1 + n2·s2) is 0.07–0.19, and the targets
sum to 17.8, 38.8 and 19.0 against n1 = 16, 37 and 15 (the target is not a fixed-size design). The ranking is
right (correlation 0.99) and the synthetic effort test reaches 97%, so the direction is fine; but the plan's claim
that weights are "the chance that a record … was collected in P1" is approximate at the per-record level, and
most primary species have fewer than 100 records.

Fix: say "approximately" with the measured deviations, or calibrate the odds by a few iterations so that the
inclusion probabilities sum to n1 (Rosén's own correction).

### 3. (Minor) Statistics and wording

- Ratio of medians 0.667 against median of per-species ratios 0.678 and mean 0.97; 25.8% of species have an
  observed velocity below their null median. The report could give the per-species view in one line.
- The 0.5 bar: with a noise-only floor of 0.41, almost any effort surface would push the ratio past 0.5; the bar
  was preregistered but it is not a demanding test, and the report should say so.
- "36% exceed their null's 95th percentile (5% expected if every range were fixed)": true for the noise null
  (synthetic 5–7%); for the effort null the expectation under real coordinated shifts is also near 5% (scenario
  B), so 36% understates movement rather than overstating it. Worth saying.
- Effort-weight defaults (θ = 1) affect 0.003% of records; counted (G2).
- The SDM variant uses one null replicate per species; the ratio's bootstrap therefore includes replicate noise on
  the null side, which inflates the interval but not the point estimate; "does not remove the effect" is fair.
- Reproduction: 6.9 vs 5.6 km/yr and 101k vs 109k species are compatible with the pipeline differences the plan
  lists; none threatens the observed-versus-null comparison, which uses one record set.

## Gate checks

- **G1:** the audit is real (leave-one-species-out, counts preserved, thinning after assignment). The field it
  misses is the one in finding 1: the other species' period labels enter the focal species' weights through the
  effort surface, which is the mechanism by which shared shifts leak into "effort". Georeferencing precision by
  period (older records georeferenced to coarse localities) is a second period-correlated field the null cannot
  model; the report names it under "What this does not show".
- **G2:** `coverage.json` present; cleaning sums to the input after D2; every species has both nulls; defaults
  counted.
- **G3:** three species traced from the raw extract with an independent implementation; invariants hold.
- **G4, G7:** not applicable, confirmed.
- **G5:** `review/overclaim_check.md` is present and consistent with the tables, but rows 1, 3, 5, 11, 26, 30 and
  31 should be relabelled Overstated after finding 1 (they assert "fixed range" or "no real movement").
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (10 claims)". A3, A5, A7, A8, A9
  resolve to the right works with sensible roles and conditions (A5 Rosén 1997 is the Pareto sampling source; A9's
  condition correctly notes BioShifts). A1, A2 and A10 describe the Daru et al. preprint; I could not read the
  preprint offline, so those rest on the agent's reading; A2's "no minimum record count or code" matches the
  plan's statement of what was seen.

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

What I checked (scripts and outputs in `review/reviewer_checks/confirm_*`; all Python reading data/ or results/ run
with `-I`, paths passed as arguments, cwd outside data/, nothing written to the repo):

- **Stored numbers** (`confirm_numbers.py/.txt`): recomputed from `nulls_primary.parquet`, `absorption_test.json`
  and `effort_surface.json`. Observed 6.906, effort 4.608, noise 2.797 km/yr; ratios 0.6671 and 0.4050, gap 0.262;
  per-species ratio median 0.6778, mean 0.970, 25.83% below their null median; exceedance 36.0% and 52.8%; median
  poleward displacement 9.42 km (0.336 km/yr) against 0.28 (effort) and -0.59 (noise); poleward shares 53.6 / 50.8
  / 49.0%; median per-species excess 1.87 km/yr; 27.6% of primary species have < 100 records. All match the report.
- **Absorption test** (`confirm_absorption.py/.txt`): (a) the study's `velocity.py` on the study's own world
  generator, seed 7, NREP 199, reproduces `absorption_test.json` exactly (1.05 / 1.03 / 0.70 / 0.60; exceedance
  7 / 5 / 18 / 23%); (b) seeds 11 and 23 give all-move 1.01-1.02, half 0.74-0.75, a fifth 0.68-0.75, so the
  finding is stable; (c) my own implementation of thinning, centroids, the noise null and the
  leave-one-species-out Pareto effort null, with no `velocity.py` code, gives 1.05 / 1.01 / 0.70 / 0.59.
- **Effort surface and Pareto on the real data** (`confirm_real.py/.txt`): see findings 1 and 2.
- **Report text** (`confirm_report_text.py/.txt`): each D3 edit is in `report.md` and in the rebuilt `report.html`,
  and the old "With no real movement at all" sentence is gone from both.
- **G5** (`confirm_g5_verify.txt`, `confirm_g5_sync.py/.txt`): `overclaim_check.py --verify` gives "G5 passed
  (43 rows)". Re-extracting the headline sentences with the tool's own `extract()` gives the same 43 sentences as
  the table, with none missing and none stale. The rows I asked to relabel have been rewritten rather than
  relabelled; the only "fixed ranges" phrases left are the disclaimers in rows 13 and 15.
- **G6** (`confirm_g6.txt`): `attribution.py check . --show` gives "G6 passed (10 claims)", and all 10 source IDs
  resolve.

### Final verdict: publish with edits

- **Finding 1 (major, identification): fixed.** The title, verdict and plain terms are now built around the noise
  floor (0.41) and the poleward excess. The verdict line keeps the preregistered "Supported" and puts the
  identification caveat in the same sentence. The absorption table is in the report as the main limitation, and its
  numbers reproduce exactly and hold under two more seeds and an independent implementation. The 26% gap is
  described as a mix of effort and shared shifts. On the effort surface, `effort_surface.py` gives 30.56° -> 31.79°.
  I get the same from my own species x cell x period units, and also from `velocity.load`'s 1° effort dict once its
  keys are decoded correctly (30.56 / 31.79). D3 says the first review's 30.2° -> 31.6° "used a different unit".
  The real cause was a decoding error in my first-round `checks1.py`: `k // 100000` misplaces 40% of 1° cells
  (those with negative longitude) by one degree of latitude. The report's numbers are the right ones. With the
  correct decoding, the tropical share at 1° is 33.7% -> 31.6%, against the report's 34.5% -> 32.3% at 5 arcmin;
  both describe the same mild drift.
- **Finding 2 (moderate, Pareto): partly fixed.** The report now says the weights are approximate per record, and
  the five-species numbers reproduce: max |dev| 0.04-0.16 against D3's 0.04-0.17, target sums 8.6-13.2,
  correlations 0.992-0.999. My recomputed odds agree with `velocity.weights` for every species tested. But the five
  smallest species are not the worst cases. Over a random 150 of the primary species with < 100 records, the
  median max |dev| is 0.105, the 90th percentile 0.24 and the maximum 0.46. 28% of those species exceed the 0.17
  the report gives as the upper end, and the mean |dev| median is 0.07. Species with 30-50 and 50-100 records look
  alike (median 0.10 and 0.11), so the deviation does not come from small samples. It comes from targets that do
  not sum to n1: median 12% off, up to 75%. Ranking holds (median corr 0.996, min 0.92). The report's sentence,
  "for the smallest species (20–22 records) ... up to 0.04–0.17", therefore reads as a small-sample effect with a
  bound that does not hold. The 28% (not "most") correction to my first review is right.
- **Finding 3 (minor, statistics and wording): fixed.** The per-species ratios (0.68 / 0.97 / 25.8%), the
  undemanding 0.5 bar and 36% as a lower bound are all in the verdict, and all three recompute.
- **G5 and G6 claims: confirmed** (43 rows in sync, all Supported; 10 claims resolve).

Remaining issues:

1. **Pareto sentence understates the deviation (edit).** In "How it was done", replace the 20–22-record range with
   the general picture. Suggested wording: "across a random 150 primary species with fewer than 100 records, the
   largest per-record deviation has a median of 0.10 and reaches 0.46, because the stated targets do not sum to
   the period's count (median 12% off); the ranking is preserved (median correlation 0.996)". Alternatively, run
   the D3 check on a random sample and report that. Add the same correction to D3 item 2.
2. **Reproducing section (edit).** `code/absorption_test.py`, `code/effort_surface.py` and
   `code/build_report_html.py` are missing from "Reproducing it". Also correct D3's note on the 30.2° figure: it
   came from a decoding error in the reviewer's script, not a different unit.
