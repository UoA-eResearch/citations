# Independent review: astronomy-ztf-wd-debris-transit-occurrence

Reviewer: Fable 5.1 (fresh independent reviewer), 2026-11-09.

## Verdict: **publish with edits**

The pipeline reproduces exactly. I re-ran both rules on all 117,193 stored light curves and got 0 mismatches in faint
and bright counts, low bins and flags. I re-ran all 150,000 injections and every recovery flag matched. The rate
sums and intervals in primary.json also re-derive exactly. **H1 Inconclusive** follows the preregistered rule, and it
holds under every variant I tried:
- dropping the i band;
- more realistic injection noise;
- summing the class rates;
- a confirmed-only numerator.

Before publication, four things need fixing:
1. **The headline "floor" is overstated.** Ten of its 15 systems are candidates or come from an unrefereed preprint.
2. **ZTF i-band epochs entered every statistic without disclosure.** The plan says g and r.
3. **The stated reason SBSS 1232+563 was missed is not what the data show.**
4. **The plan's g/r coincidence check (G4) was never run.**

None of these needs new data. The numbers below come from my checks, so the edits can be made directly.

Checks referred to below (all in `reviewer_checks/`):
- c1: sample, IDs and light curves;
- c2 and c3: rule re-run and positive controls;
- c4: injection realism;
- c5: rates;
- c6: candidate spot checks and calendar test;
- c7: report numbers;
- c8: git timeline.

## Findings

### 1. The "floor" of 2.1 × 10⁻⁴ counts mostly candidates and preprint systems (major)

**Evidence** (c5_rates.txt, known_systems.csv, ledger rows A6, A9 and A10).

The 15 recovered "known systems" come from these sources:

| source | recovered systems | status |
|---|---|---|
| Bhattacharjee et al. 2025 | 5 | paper title: "Six New Candidates" |
| van Roestel et al. 2026 | 5 | unrefereed preprint |
| Guidry et al. 2021 | 3 | candidates in that paper; only J0328 was later confirmed (Vanderbosch 2021) |
| Vanderburg 2015 and Vanderbosch 2020 | 2 | confirmed |

Only three recovered systems (WD 1145+017, ZTF J0139+5245 and ZTF J0328−1219) have refereed, follow-up-confirmed
transits. Using them alone, the lower rate is **4.1 × 10⁻⁵** (95% 0.85–12 × 10⁻⁵), five times below the reported
"floor". Adding the Guidry candidates gives 6.9 × 10⁻⁵.

Where the report goes too far:
- The title calls these "known systems alone".
- "What this does and does not show" calls the number a floor.
- Its own "What was asked" section does call the Bhattacharjee six "candidates".

A floor needs a numerator of real systems. Here, two-thirds of the numerator is not established.

**Fix:**
- Retitle along these lines: "Published debris-transit systems and candidates, 15 of them recovered, give about 1 in
  5,000 …".
- Report the tiered lower rates (confirmed only: 4.1 × 10⁻⁵; all published: 2.1 × 10⁻⁴).
- Describe 2.1 × 10⁻⁴ as "the rate implied by published systems and candidates", not a floor.
- The verdict is unaffected, since the lower limit is below 5 × 10⁻⁴ either way.

### 2. Undisclosed deviation: ZTF i-band (zi) epochs are pooled into eligibility and both rules (major)

**Evidence** (c1 and c3 §2).

What the plan says:
- eligibility is "100 good ZTF epochs … in g and r combined";
- the short rule is "pooled over g and r".

What the code does:
- `fetch_lc.py` keeps every filtercode;
- `detect.py` pools all filters.

77,254 stars have zi epochs, 6.8% of all eligible epochs. Restricting to g and r as planned changes the results:
- eligible: 108,493 (581 stars were eligible only because of zi);
- flagged: 1,006 instead of 914;
- 152 stars flagged only under g + r, and 60 flagged only as run;
- known systems recovered: still 15 of 18.

Elsewhere the report says "pooled over g and r", and so does the F1 caption (`figures.py:52`). Both are false
descriptions of what was run, and deviations.md has no entry for this.

**Fix:**
- Add a D-entry.
- Correct the report text and the F1 caption.
- Either re-run with g + r as the primary analysis (it is preregistered), or report the g + r variant beside the
  as-run one. The H1 verdict does not change: about 1,000 flags gives an upper rate of about 1.4 × 10⁻².

### 3. The explanation for the missed SBSS 1232+563 is not supported (moderate)

**Evidence** (c6 SBSS table, c3 §4).

The report attributes the miss to "sporadic dimming". The stored light curve tells a different story:
- From MJD 59744 the bins are sparse: 5 to 14 epochs per 30 days, almost no r band.
- After MJD 60068 (April 2023) there are no epochs at all until MJD 60848 (mid-2025), a 26-month gap. That gap
  covers the 8-month, >40% 2023 event that defines the system.
- The one bin from the start of that event (MJD 60068) is 14% low, but it is the star's only low bin, and the rule
  needs two.
- The general light-curve span runs to MJD 60969, so the release is not the cause.

The likely causes are on the data-selection side:
- the per-filter "one object with most epochs" choice dropping a second field's object;
- or the event epochs failing catflags = 0 or magerr < 0.25.

I did not re-fetch, because my rules forbid new survey downloads.

**Fix:**
- Re-query this one star, keeping all objects and flags, to find where the 2023 epochs went.
- State the actual reason in the report.
- If the one-object-per-filter choice drops other fields' epochs in general, say so as a completeness limitation (D1
  item 2).

### 4. The planned G4 g/r coincidence check was not run, and the calendar pattern shows the long rule is mostly systematics (moderate)

**Evidence** (c6).

plan.md section 4 promised a script-only check of 30 random flags (do the dip epochs coincide in g and r?). Section 5
counts it as a mitigation for blending and calibration artefacts. It appears nowhere in results/ or the report.

I ran the equivalent on all 673 long-flagged candidates:
- 71% of their low bins with at least 3 g and 3 r epochs are low in both bands;
- 508 of 673 candidates have at least one coincident bin.

So the planned check would not have removed most flags. A calendar test is far more telling:
- 444 of 673 long-flagged candidates have a low bin inside the same ten 30-day windows;
- 136 of them fall in MJD 59010–59040 (June 2020) alone;
- in those windows, 2,000 random quiet stars are also systematically faint (median bin depth 0.1–0.6%, against
  −0.03% overall).

This backs the report's hedge ("probably slow photometric trends") with real evidence. It also shows that the plan's
named mitigation is weak.

Spot checks of five random long-only candidates:
- one has g-only 20% dips with no r coverage;
- three have 5–9% dips in both g and r inside the crowded 2020 windows.

**Fix:**
- Report the missing G4 check as not run, or add these numbers to plausibility.md.
- Add the calendar-coincidence result as an exploratory note supporting the "systematics" reading.
- Drop the plan's g/r check from the list of mitigations, since it barely discriminates.

### 5. H1 could never have been Supported with this design (moderate, interpretation)

**Evidence** (c5).

Supported needs the 97.5% upper limit of the upper rate to be below 5 × 10⁻⁴. With ΣC = 72,748, that means at most
about 25 flags in total (Poisson limit below 36.4). With a 0.8% flag rate from 109,074 stars, that was never
reachable.

Refuted, at the observed completeness, would need at least 50 recovered known systems. Only 18 are in the sample.

"Inconclusive" is therefore what the design guaranteed, not something the data revealed.

**Fix:** say this in the verdict block: the upper-rate construction makes Supported structurally unreachable without
vetting. That is the real limitation, and it should not read like a near miss.

### 6. G5 overclaim check is incomplete and too generous (moderate)

**Evidence** (review/overclaim_check.md; c3, c5).

All 39 rows are labelled Supported. I disagree with four of them:
- **Row 1 (title) and row 14:** "Known systems alone … 1 in 5,000" should be Overstated (finding 1).
- **Row 3:** "committed before detection was run" should be Partially supported. known_systems.csv was edited after
  the first detection pass: 8 Gaia IDs changed from rounded to true values in commit a6c616b (c8). This is
  disclosed only obliquely in D1.
- **Row 2:** "two preregistered rules" should be Partially supported. As run, they pool the zi band (finding 2).

The "What this does and does not show" section is outside the tool's scope, and it carries the main "floor" claim.

**Fix:**
- Re-label these rows and rewrite the sentences.
- Extend the check by hand to the "floor" bullet.

### 7. G3 hand traces are not random and skip the long rule (minor)

**Evidence** (code/handtrace.py:31-33).

METHODS G3 asks for three random units traced end to end. Here, two of the three are chosen (WD 1145+017 and the
largest-excess candidate). Only the short-rule statistics are traced. The long rule produces 653 of 878 candidates
and is never hand-traced. My full re-implementation (c3 §1) matches the long rule exactly, so this is a gap in the
gate, not a bug.

**Fix:** add a hand trace of `low_bins` for one long-only candidate, and label two of the traces as chosen, not
random.

### 8. Some ZTF matches are probably a different, brighter object (minor)

**Evidence** (c3 §6).

257 stars have a median g or r more than 0.75 mag brighter than Gaia G predicts. Nearly all of the deviations are in
the bright direction (robust scatter 0.03–0.04 mag). These stars are flagged at **9.0%** against 0.82%. 15 of them
are candidates; none is a known system.

The likely cause is that the most-epochs object within 2 arcsec is a neighbour or a blend. Separately, g and r can
come from different objects, because the choice is made per filter.

**Fix:** veto (or list separately) candidates whose ZTF median magnitude disagrees with Gaia by more than 0.75 mag.
Mention it under limits.

### 9. Combined rate and class assignments (minor)

**Evidence** (c5; `detect.py:194-200`).

The preregistered "best class per star" denominator gives the smallest possible combined rate. Correcting each known
system by its own class completeness gives **2.5 × 10⁻⁴**, not 2.1 × 10⁻⁴.

Class assignment is a keyword rule. As a result:
- ZTF J0347−1802 and WD J1302+1650, both described as a single dip, go to J0139-like. Moving them to one-off gives
  per-class lower rates of 5.5 × 10⁻⁵ (J0139-like) and 1.4 × 10⁻⁴ (one-off), against 9.2 × 10⁻⁵ and 1.0 × 10⁻⁴.
- The class prototypes are recovered by the other rule: ZTF J0139+5245 by the short rule only, WD J1650+1443 by the
  long rule only (c3 §4).

**Fix:**
- Report the sum-of-class-rates variant beside the preregistered one.
- Note that class labels are approximate, and give per-class rates with that caveat.
- The verdict is unaffected.

### 10. Injection realism: noise and the magerr cut are not applied to dimmed epochs (minor; tested, small effect)

**Evidence** (c4).

How the injections were made:
- dimmed epochs keep their original magnitude residual;
- their errors are rescaled but never used;
- they are not subject to the magerr < 0.25 good-epoch cut that the real data passed.

I re-scored the identical 150,000 signals with consistent noise and the 0.25 cut:
- **Source-limited scaling (V1):** recovery is unchanged (66.6 / 49.6 / 53.8%).
- **Background-limited scaling (V2, more realistic at G 19–20):**
  - one-off recovery falls from 53% to 45% overall, and from 40% to 30% at G 19.5–20;
  - the combined lower rate moves only from 2.06 to 2.13 × 10⁻⁴;
  - H1 stays Inconclusive.

Other checks: the box shapes, 60-day seasons, flagged-star exclusion and G × epoch binning are all as stated. Every
cell had at least 250 injections, so the class-mean `fillna` fallback in `detect.py:230` was never used (c5).

**Fix:** state that injected dips carry no added noise and no magerr cut, and quote the V2 sensitivity as a limit.

### 11. Faint-outlier asymmetry is strong and should be quantified (minor)

**Evidence** (c3 §3).

The report's 77% is confirmed (76.6%; median excess −6). The asymmetry grows steeply with magnitude:

| G | share with negative excess | short-rule flag rate |
|---|---|---|
| < 17 | 28% | 0.82% |
| 19.5–20 | 92% | 0.018% (about 45 times lower) |

The injections capture part of this, since they use real light curves, but finding 10 shows they miss the censoring
of faint epochs.

**Fix:** add this table. Say the short rule is effectively blind to shallow hour-scale dips at G > 19.5, beyond what
C_wd1145 (0.49 there) implies.

### 12. Provenance details (minor)

**Evidence** (c8; known_systems.csv).

- The committed control list carried float-rounded Gaia IDs for 8 systems, while its `source_location` column says
  the IDs came from Bhattacharjee+2025 tables. So the IDs were in fact matched from the sample, not transcribed.
- The first detection pass cannot be audited: its outputs were overwritten (inject.log at 16:34 belongs to it).
- `handtrace.py:22` hard-codes the 13 failed queries. The number is right (c7), but it should be read from the .done
  files.

**Fix:** state in D1 that known_systems.csv IDs were corrected after the first pass, and fix the `source_location`
wording.

## Answers to the brief's questions

1. **Sample and light curves.**
   - The cuts reproduce exactly from the FITS (121,838; c1).
   - The ID fix is complete:
     - 41 colliding pairs (82 stars), none with more than 2 stars;
     - all 82 present only in shard_fix;
     - no star in two files;
     - no ID outside the sample;
     - no duplicate MJDs within a series;
     - epochs under 30 s apart are high-cadence fields, not merges.
   - The 2-arcsec cone is right (0.000556°).
   - Not right: one object per filter allows g and r from different objects, the i band is included (finding 2), and
     about 257 matches are probably the wrong object (finding 8).
   - Coverage counts reconcile: 117,193 with light curves, 109,074 eligible, 13 failures.
2. **Rules.**
   - Robust σ per filter, the binomial test, floor-MJD nights and 30-day bins with std/√n standard errors all match
     the plan and re-implement exactly.
   - The asymmetry strongly suppresses the short rule for faint stars (finding 11).
   - Two recovered controls clear p < 10⁻⁶ only narrowly: WD 1145+017 at 9.7 × 10⁻⁷ and ZTF J0139+5245 at 8.3 × 10⁻⁷.
3. **Positive controls.**
   - All 20 systems the report names are present and matched (WD 1054−226 at 4.9″, explained by proper motion).
   - Whether the list is complete I could not verify independently beyond van Roestel's list.
   - Class assignment is a keyword rule (finding 9).
   - Why the three are missed:
     - WD 1054−226: 207 epochs and few-per-cent dips, so the excess is 2.
     - SDSS J0107+2107: excess 3, p = 0.23, one low bin.
     - SBSS 1232+563: the 2023 event is almost absent from the stored light curve (finding 3).
4. **Completeness.** The study's own injection set-up reproduces exactly. It is optimistic only modestly (finding 10).
   The G × epoch bins are well populated. Excluding flagged stars is minor. The best-class combination biases the
   combined rate low by about 18% (finding 9).
5. **Rates and verdict.**
   - The Garwood intervals are correct.
   - Inconclusive is right by the rule, but it was guaranteed by construction (finding 5).
   - The lower rate is not a floor in the sense of confirmed systems (finding 1).
6. **Candidates.** Yes, most long-dip flags are plausibly systematics: the calendar clustering shows it (finding 4).
   The short-only candidates (205) were not spot-checked beyond the largest-excess hand trace.
7. **Report numbers.** Every number checked against the tables matches:
   - 109,074, 914, 21, 878 and the 653/205/20 split;
   - the 3/6/6 recovery split;
   - median 1,049 epochs and 207 epochs for WD 1054−226;
   - the rates, intervals and distance bins;
   - threshold variants 326/158/7,130/138;
   - 77%;
   - geometry 4–8 × 10⁻⁴.

   The problems are in the title and the "floor" wording (finding 1), and in "g and r" (finding 2).

**Gates.**

| gate | status | notes |
|---|---|---|
| G1 | present | Detection is a uniform rule with no labels; no leak found. The control list was edited after the first pass, IDs only (finding 12). |
| G2 | present | Coverage reconciles; the fallback was never used. |
| G3 | partial | Finding 7. |
| G4 | not applicable as a label gate | The plan's own G4 g/r check is missing (finding 4). |
| G5 | passes the tool but is not honest on 4 rows | Finding 6. |
| G6 | passes | 11 claims resolve. Spot-checked A3, A6, A8, A9 and A10 against resolved titles: A9's "Six New Candidates" and A6's "candidates" contradict the report's "known systems" framing (finding 1). |
| G7 | not applicable | |

## G5 re-labels

| row | sentence (short) | new label | rewrite |
|---|---|---|---|
| 1 | title "Known systems alone give about 1 in 5,000" | Overstated | "Published debris-transit systems and candidates give about 1 in 5,000 (confirmed systems alone about 1 in 25,000) …" |
| 2 | "searched … with two preregistered rules" | Partially supported | add "pooling ZTF g, r and i (the plan named g and r; see D2)" |
| 3 | "committed before detection was run" | Partially supported | "… committed before the reported detection run; Gaia IDs were corrected after the first pass (D1)" |
| 14 | "known systems alone already amount to about 1 in 5,000" | Overstated | "published systems, two-thirds of them candidates or from a preprint, amount to …" |
| (outside tool) | "Known systems alone set a floor of about 2 × 10⁻⁴" | Overstated | "Confirmed systems alone give 4 × 10⁻⁵; all published systems give 2 × 10⁻⁴" |

## What to do

1. Rewrite the title, the verdict bullets and "What this does and does not show" with tiered lower rates (finding 1).
2. Add a D-entry for the zi band. Correct the report text and F1 caption. Report the g + r variant: 1,006 flagged,
   15 of 18 recovered (finding 2).
3. Re-query SBSS 1232+563 with all objects and flags, and correct the explanation for the miss (finding 3).
4. Add the G4 g/r and calendar-coincidence results to plausibility.md, and drop the g/r check as a claimed mitigation
   (finding 4).
5. Say in the verdict that Supported was unreachable by construction (finding 5).
6. Apply the G5 re-labels and re-run `--verify` (finding 6).
7. Add a long-rule hand trace (finding 7). Add the Gaia-vs-ZTF magnitude veto or list (finding 8). Add the
   sum-of-class-rates variant (finding 9). Add the injection-noise limitation (finding 10). Add the asymmetry table
   (finding 11). Fix the provenance wording (finding 12).

## In plain terms

The search code does what the study says it does. I re-ran it from scratch and got identical numbers, and the
"cannot tell yet" verdict is right. But the headline figure of about 1 in 5,000 counts 15 stars as known debris
transiters, and only 3 of them are confirmed by follow-up. The rest are published candidates or come from a paper
not yet peer reviewed. Counting only confirmed systems gives about 1 in 25,000. So the report should present a range
of floors, not call 1 in 5,000 a floor.

The study also quietly used a third ZTF colour band that the plan did not include. This changes about 200 flags but
not the verdict.

One known system was missed mainly because its light curve has a two-year hole across its big 2023 dimming, not
because its dimming was too sporadic.

Most of the roughly 900 unexplained flags are probably instrumental. Two-thirds of the long-dip flags dim during the
same few months, and so, slightly, does the average quiet star.

The test as designed could never have shown the rate is low. Only vetting the candidates can do that.
