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

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

I checked the D2 fixes (commit 8bf5ae5) against the stored outputs and my own re-implementations. I used one IRSA
query (SBSS 1232+563). The scripts and outputs are in `reviewer_checks/confirm_*`; the IRSA CSV and the per-star
re-run table are in scratch, not committed.

**What I checked, and where the evidence is**

- **g + r re-run** (`confirm_redetect_gr.py` / `.txt`). I re-implemented both rules and ran them on every
  `data/lc_v2` light curve, keeping only g and r. Against the new `detect.parquet` (116,911 stars) there are
  0 mismatches in epochs, faint, bright, low_bins, short or long.
  - Eligible 108,493; short 233; long 802; flagged 1,006.
  - Compared with `withzi_detect`: 152 stars are flagged only under g + r and 60 only as first run; 581 stars were
    eligible only because of zi.
  - `candidates.csv` has 970 rows, all flagged in my re-run. Flagged minus candidates = 36 (15 known + 21 CVs).
- **Rates, tiers and design limits** (`confirm_rates.py` / `.txt`).
  - `inject.parquet` was regenerated for g + r:
    - the seeded pick equals the 5,000 g + r unflagged eligible stars;
    - it is not the withzi file (308 of 5,000 stars overlap);
    - a replay of 200 stars × 30 injections with `detect.inject_one` and my rules gives 0 mismatches in 6,000.
  - Re-derived from scratch: ΣC_best 71,571.9. Every completeness cell has at least 250 injections, so no fallback
    was used.
    - Lower rate 2.096e-4 (1.17–3.46e-4).
    - Upper rate 1.376e-2 (1.29–1.46e-2).
    - H1 Inconclusive.
    - 15 of 18 known recovered (3 short-only, 6 long-only, 6 both).
  - Tiers: confirmed 3 → 4.19e-5 (0.86–12.2e-5, 1 in 23,857); plus Guidry 5 → 6.99e-5; all published 15 → 2.10e-4.
    All three match `posthoc_review.json`.
  - Design limits: Supported needs N_upper ≤ 24, and Refuted needs ≥ 49 recovered known systems. The data have 1,006
    flags and 18 known systems in the sample.
  - Asymmetry under g + r: 77.0% of stars have a negative excess, median −6. So the report's "77%" still holds.
- **SBSS 1232+563** (`confirm_sbss.py` / `.txt`; IRSA CSV in scratch).
- **G4 and the calendar test** (`confirm_gr_calendar.py` / `.txt`).
- **Gates** (`confirm_g5_verify.txt`, `confirm_g6_check.txt`): G5 passed (48 rows) and G6 passed (11 claims), both
  exit code 0. git status shows the run untouched.
- **report.html** carries the same text as report.md for every phrase I spot-checked.

### Final verdict: publish with edits

Every number D2 reports reproduces exactly, and the verdict (H1 Inconclusive) is right. What remains is wording:
- a stale "1 in 80";
- SBSS epoch counts that compare different windows and filter sets;
- a "mostly systematics" headline that the calendar null only partly supports;
- the G4 definition;
- a stale coverage.json;
- some leftover first-draft sentences.

None of these changes a number in the verdict.

**Findings 1–6**

- **1. Floor overstated: fixed.** The tiered rates re-derive exactly (`confirm_rates.txt`). The title, the verdict
  table and "What this does and does not show" say "rate implied by published systems and candidates", and no
  sentence calls 2.1e-4 a floor any more.
  - My first review's 4.1e-5 and 6.9e-5 were computed on the with-zi ΣC. On the g + r ΣC, 4.2e-5 and 7.0e-5 are
    correct.
  - Small wording point: the title's "leave the rate unbounded above" is loose, since there is an upper rate of
    1.4e-2. "Poorly bounded above" would be accurate.
- **2. i band: fixed.**
  - `FILTERS = zg,zr` is in place.
  - Detection, injections and occurrence were all genuinely re-run, and the figures quoted in D2 and the report
    reproduce: 108,493 eligible, 1,006 flagged, 970 candidates, 15/18, 2.1e-4, 1.38e-2.
  - The as-run outputs are kept as `withzi_*`.
  - The F1 caption ("pooled over ZTF g and r … 108,493") is now true.
  - Leftover: `results/tables/coverage.json` still carries the with-zi counts (117,193 with light curves, 109,074
    eligible). The report's G2 line points to that file, but the report's text gives 116,911 and 108,493.
- **3. SBSS 1232+563: fixed. The study is right and my first review was wrong.**
  - The star is in `shard_0017.parquet` (1,555 rows). It has 29 stored good epochs in MJD 60068–60849 (24 g, 4 r,
    1 i), and 33 at MJD ≥ 60068.
  - My c6 table printed only bins with ≥ 5 epochs. That is why it showed nothing between 60068 and 60848 and why I
    called it a 26-month gap. The epochs are there, spread one or two per 30-day bin.
  - The 2023 event is visible in them: g relative flux 0.84, 0.91, 0.85, 0.56, 0.65, 0.73 and 0.82 between MJD 60073
    and 60250. But it falls in bins of 5 (the one low bin, 13.8% deep, 7.3 standard errors), 2, 2 and 1 epochs.
    Five bins are ≥ 5% deep but have fewer than 5 epochs.
  - So "one qualifying low bin, the rule needs two", caused by sparse sampling, is correct.
  - IRSA: 4 g/r objects across fields 790 and 1824, and 34 good g/r epochs at MJD ≥ 60068 (35 counting the one zi
    epoch). 32 of the 34 are stored. The 2 that are not come from the second field's g object (1824102200002193),
    which loses to the most-epochs object under the one-object-per-filter choice. One of them (MJD 60092, rel 0.86)
    falls in the event, but it would only lift that bin from 2 to 3 epochs, so the conclusion stands.
  - The other 22 rows have catflags 32768 and are correctly excluded.
  - Wording fix needed: "29 good epochs … after April 2023" against "only 35 good epochs after April 2023" compares a
    windowed, all-filter stored count with an unwindowed, all-filter IRSA count. Like for like, in g + r at
    MJD ≥ 60068, it is 32 stored against 34 in IRSA.
  - Separately, "What this does and does not show" still lists the three missed systems as "shallow or sporadic
    dimming". SBSS is neither.
- **4. G4 and the calendar test: numbers fixed; wording partly fixed.**
  - The calendar numbers reproduce exactly: 769 long-dip candidates, 454 with a low bin in the ten busiest windows,
    140 at MJD 59010, quiet-star depths 0.10–0.74% against −0.02%.
  - I added a null in which each candidate's low bins are re-drawn at random among its own ≥ 5-epoch bins. It gives
    215 (95%: 194–238) against the observed 454. The ten windows hold 10.9% of quiet stars' usable bins but 39% of
    candidates' low bins.
  - So the clustering is real, about twice coverage. But only about 240 of the 769 are in excess of what coverage
    alone produces. "Many long-dip flags track survey-wide trends" is supported; "mostly systematics" (the bullet
    heading, G5 row 27) is stronger than this test shows.
  - g/r coincidence, 94% against 71%: same data and same bins, so the difference is purely the threshold. D2 uses
    both bands > 2.5% below the pooled median; my first review used both bands ≥ 5% below their own median. The binning
    scheme hardly matters (93% and 71% with detect.py's bins).
  - Of the two, the ≥ 5% per-band version is the faithful translation of the rule's 5% depth. D2's 2.5% halves the
    threshold.
  - Neither is the plan's G4 rule, which is "dip epochs coincide in g and r within a night", on 30 random flags. Run
    as written, 25 of 29 testable random flags pass (1 untestable). Over all flags, 88% of the testable flagged stars
    have a coincident night, exactly as many as the known systems (88%).
  - The conclusion ("barely discriminates") therefore holds under every definition. The report should say its 94%
    is a bin-level analogue at a 2.5% threshold, or quote the plan's own rule (25 of 29).
- **5. "Unreachable by design": fixed.** The verdict paragraph states it plainly, and the numbers check: at most 24
  flags for Supported, and about 49 recovered known systems for Refuted against 18.
- **6. G5: partly fixed.**
  - The title, floor, standfirst (rows 1–3) and i-band rows are rewritten and the tool passes.
  - Row 3 is still labelled Supported, although D2 item 6 says it was relabelled "partially supported". Because the
    sentence now discloses the ID correction, Supported is defensible, but D2 misdescribes it.
  - Row 47 ("about 1 in 80") cites "1/81", which is the with-zi upper rate. Under g + r it is 1 in 73, so the text
    should say about 1 in 70.
  - Row 27 ("mostly systematics") should be Partially supported (see 4).
  - Rows 21 and 23 should carry the like-for-like SBSS counts (see 3).

**Findings 7–12 (not in the brief).** D2 does not mention them: they are neither addressed nor declined.
- **7 (hand traces).** Open. `plausibility.md` still calls the traces three plain re-fetches and adds no long-rule
  trace. It does now note that the traces predate the g + r re-run.
- **8 (ZTF and Gaia magnitude mismatch, about 257 stars).** Open. No veto, list or limitation was added.
- **9 (sum-of-class variant; approximate class labels).** Open.
- **10 (injected dips carry no added noise and no magerr cut).** Open. This is not stated in the report's
  completeness description.
- **11 (asymmetry by G).** Open. The 77% sentence is still correct under g + r, but the G-binned table is absent.
- **12 (provenance).** Partly addressed: the standfirst and D2 now say the IDs were corrected after the first pass.
  Still open: the `source_location` wording and the hard-coded 13 failures in `handtrace.py`.

All six are minor and none changes the verdict. Declining them with one line each in D2 would be acceptable.
Leaving them unmentioned is not.

**Remaining issues**

1. Report and G5 row 47: "about 1 in 80" should be about 1 in 70 (1/1.38e-2 = 73).
2. SBSS wording (report and G5 rows 21 and 23): give like-for-like counts (g + r, MJD ≥ 60068: 32 stored, 34 in
   IRSA, the 2 missing from the second field's g object). Remove SBSS from the "shallow or sporadic dimming"
   sentence.
3. "Mostly systematics" (report heading, G5 row 27): soften to "many". The calendar null puts about 215 of the 454
   in the crowded windows by coverage alone.
4. G4: state that the 94% is a bin-level analogue at 2.5% (71% at the rule's 5%), or report the plan's own
   night-level rule (25 of 29 random flags pass; 88% of flags against 88% of known systems).
5. `results/tables/coverage.json` still holds the with-zi counts (117,193 and 109,074). Regenerate it for g + r
   (116,911 and 108,493) or note the difference.
6. Stale text:
   - "Independent review: queued" should be done (D2).
   - The Process section lists only D1; add D2.
   - D2 item 6 says row 3 was relabelled, but it was not.
   - "Unbounded above" is loose.
7. Findings 7–12: address them, or decline each in one line in D2.
