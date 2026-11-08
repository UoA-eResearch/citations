# Review: seismology-geophysics-dynamic-triggering-strain-test

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py/.txt`, `checks2.py/.txt`). Checks used `venv/bin/python -I` with the study's `analyse.summarise`
imported, on the stored `pairs_*.parquet`, `null_primary.parquet` and the ComCat files; no proxy or window run was
repeated.

## Verdict: fix first (the H2 verdict does not survive a like-for-like null; H1 stays Inconclusive)

The pipeline is carefully built and I found no arithmetic or bookkeeping error: every number in the report matches
`primary.json`, `coverage.json`, `proxy_counts.csv`, `trigger_dispersion.json` and `strain_check.json` (351
triggers ≥ 1,000 km, 350 with pairs; 9,336 stations with proxy data, 1,496 with ≥ 100 valid pseudo-triggers;
95.6 M pairs, 49.9 M local; 15,042 vs 15,742.2); the window arithmetic, β rule, two-way bootstrap and
per-trigger dispersion are implemented as stated; the timeline holds (plan 10:58, code 11:04, first windows 16:05,
D1 16:10). The problem is the null's design. Pseudo-triggers are rejected within 10 days of any global M ≥ 7 and
3 days of any M ≥ 6.5 (`windows.py:170-175`), but real triggers are not: 282 of the 350 population triggers fail
that rule, and 115 of them have another M ≥ 6.5 inside their own post window. Those windows carry the other
earthquake's surface-wave detection shadow (the study's own "instant" result: −1.4 pp) and aftershock masking,
which the pseudo windows never do. Restricted to the 105 triggers whose baseline and post windows contain no other
M ≥ 6.5, the mean excess is +0.005 (−0.002 to +0.012) and H2 is Inconclusive, not Refuted; the contaminated
post windows alone give −0.013 (−0.018 to −0.007). The headline "no more common than at matched random times" is
therefore not established by a matched comparison.

## Findings

### 1. (Major, G1) The null excludes times near other large earthquakes; the real triggers do not, and that drives the negative excess

Evidence: `checks1.txt` §C, `checks2.txt` §B. By the pseudo-trigger rule, only 70 of 357 catalogue triggers (68 of
the 350 in the population) are "clean". Classifying real pairs by what sits inside their own windows:

| real pairs | triggers | pairs | E1 | E5 | all | H1 / H2 |
|---|---|---|---|---|---|---|
| preregistered (all) | 350 | 228,963 | +0.002 | −0.007 | −0.003 (−0.007, +0.001) | Inconclusive / Refuted |
| no other M ≥ 6.5 in baseline or post window | 105 | 70,010 | +0.004 | +0.006 (−0.009, +0.024) | **+0.005 (−0.002, +0.012)** | Inconclusive / **Inconclusive** |
| another M ≥ 6.5 inside the post window | 115 | 74,008 | −0.011 | −0.014 | **−0.013 (−0.018, −0.007)** | Inconclusive / Refuted |
| M ≥ 6.5 in the baseline only | 130 | 84,945 | +0.010 | −0.007 | −0.001 (−0.007, +0.004) | Inconclusive / Refuted |
| pseudo rule applied to real triggers (10 d / 3 d) | 68 | 43,771 | +0.002 | −0.003 | 0.000 (−0.008, +0.009) | Inconclusive / Inconclusive |

The contamination is strain-correlated: the share of pairs with an M ≥ 6.5 in the post window rises from 21% in
quintile 1 to 36–40% in quintiles 4–5, because big triggers have big early aftershocks. D1's exposure correction
removes only the ±60 s P-arrival masks of M ≥ 4.5 events; it does not touch the hours-long surface-wave shadow
of an M ≥ 6.5 aftershock, which is why E5 stays negative after it (−0.002) and turns positive (+0.006) only when
the contaminated windows are set aside. The plan's section 7 audit lists "bigger triggers have more aftershocks"
and handles it with P masking; it missed that the pseudo-trigger exclusion rule makes the null cleaner than the
data in exactly this respect.

Fix: make the two arms comparable, either by applying the pseudo exclusion rule (or the within-window rule) to
real triggers, or by dropping the rule for pseudo-triggers so that both arms sample the same mixture; recompute
H1 and H2; state the result as primary with the preregistered one beside it. On the comparable set H2 is
Inconclusive with a point estimate at the 0.5 pp bar, so the title and verdict must change.

### 2. (Moderate) The station population is 16% of stations, chosen by availability, and most stations' nulls rest on a few hundred pseudo-triggers

Evidence: `checks2.txt` §A, `coverage.json`. The median station has 3 valid pseudo-triggers of 500 drawn (4,176 of
9,336 have none), because every station-day in a 9-day window must be "loaded"; 84% of real pairs are dropped
for the same reason. The 1,496 population stations have a median of 212 valid pseudo-triggers (10th–90th
percentile 114–385), so a station's p0 carries a standard error of about 0.017 against p0 ≈ 0.07. That is fine
for means over 1,496 stations but means per-station excesses (F2) are noise-dominated and should not be mapped
as if informative. The availability rule is symmetric, as the report says, but the population it leaves is
permanent-network stations with long continuous records; the plain-terms section says this, the title does not.

Fix: say in the title or verdict that the test covers about 1,500 long-running stations; drop or heavily caveat
the station map.

### 3. (Moderate) Recall and detectability bound what "no detectable triggering" can mean

Evidence: `proxy_validation.json`; `primary.json` instant. The proxy catches 46% of ComCat M ≥ 1 events at the
nearest analysable station (52% at M ≥ 3), only 21% of pairs have any local pair in either window, and β ≥ 2
needs roughly a doubling of a station's weekly rate inside 24 h. The design can detect a triggered swarm that
doubles a station's rate for a day; it cannot detect a few extra M ≤ 1 events. The report's closing sentence
says this; the title ("No detectable remote dynamic triggering") reads as a general statement. The instant
window shows the proxy loses 1.4 pp of significant rises during the wave train, so instantaneous triggering,
where most published cases sit, is untestable here (the report says so).

Fix: title → "no detectable excess of day-scale local-event rises after distant M7+ earthquakes at 1,500
western-US stations" or similar.

### 4. (Minor) Things checked and right

- Cleaning: 2,088,914,320 picks read, 18.9 M exact duplicates (3.4%) dropped, 531,327,099 kept; channel merge
  removed 18,069; masking removed 16.2 M (3.0%); 7 partition-edge picks are immaterial.
- Proxy: pairing (first S 0.8–8 s, no P between, three picks ahead), t0, 3-station coincidence in ±2.5 s with
  2,500 ms buckets, neighbours "with picks this month" all as described (`proxy.py:134-163`).
- Windows: hour rounding, 2.5 km/s wave-train end + 2 h, 7-day baseline, β with f = T_post/(T_post + T_base), β = 0
  at N = 0 (21% of pairs), validity rules; `masked()` unions intervals correctly.
- Null: deterministic seeds (crc32), hour matched, ±45 d and ±12 × 365 d, inherited Δ-windows.
- Analysis: product-weight two-way bootstrap; H1/H2 rules as preregistered; quintiles by rank; dispersion ratio
  10.0, 39 above / 55 below 3 SE, reproduced from the pairs table.
- Strain: Prague formula with M capped at 8.3; Spearman 0.47 on 2,546 measured pairs (4,088 of 6,634 requests
  returned no LHZ data). Top quintile is 83 triggers; the five largest contribute 10% of its pairs, so it is not
  dominated by one event.
- G3 traces match but are weak (counts of 0/10, 0/1, 0/1); a trace of a significant pair would be more telling.

## Gate checks

- **G1:** the audit in plan.md §7 is real but incomplete: the pseudo-trigger exclusion rule is a field present
  in the null and absent in the data (finding 1), and it correlates with strain.
- **G2:** `coverage.json` has picks_fetch, picks_proxy and all pairs_* stages; no fallbacks; all drops reasoned.
- **G3:** `plausibility.md` traces three pairs; invariants hold; the traces omit masking and are trivial counts.
- **G4, G7:** not applicable, confirmed.
- **G5:** `review/overclaim_check.md` consistent with the tables; rows 1, 6, 8–10, 34–35 and 39 should be
  relabelled after finding 1 (Overstated: they rest on H2 Refuted and on "matched random times").
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (8 claims)". S4 (van der Elst &
  Brodsky 2010), S6 (Kennett & Engdahl 1991), S7 (Lay & Wallace) and S8 (ComCat) resolve to the right works with
  sensible roles; S1–S3 summarise abstracts I could not read offline; S5's bucket citation is as the plan states.

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

What I checked (scripts and outputs in `review/reviewer_checks/`, `confirm_*.py` / `confirm_*.txt`):

- `confirm_arms.py` / `confirm_arms.txt` (study venv, `python -I`, paths as arguments, only `analyse.summarise`
  imported). It reclassifies the real pairs from scratch using the `windows.py` rules: the pseudo-trigger rule
  (|Δt| < 10 d to another M ≥ 7, < 3 d to another M ≥ 6.5, self excluded within 60 s; each of the 357 triggers
  self-matches exactly once), and per-pair post and baseline windows rebuilt as in `windows.test`. It then reruns the
  preregistered H1/H2 rules and the bootstrap with the same seed, in the same order as `code/comparable.py`. All five
  classes match `comparable.json` exactly: pairs, triggers, every E, every CI, H1 and H2. The script also covers the
  contamination share by quintile, a decomposition of the preregistered mean, station counts, recall,
  `primary.json` and `trigger_dispersion.json`.
- `confirm_gates.py` / `confirm_gates.txt` (`python3 -I`). G5: I re-extracted the headline sentences with the tool's
  own `extract()`. The 49 rows in `overclaim_check.md` are exactly the current report's 49 sentences (none missing,
  none stale), and `--verify` passes. G6: `attribution.py check --show` passes (8 claims); S1–S6 resolve to the right
  titles. The script also checks that each D2 edit is present in both `report.md` and `report.html`; all 15 are.
- I read `deviations.md` D2, `code/comparable.py`, the report in full, and the git history (read-only). D2's code,
  table and report were committed together in 31d6ac3. That is acceptable here: the analysis is labelled post hoc,
  and the corrected primary is the review's own suggestion, with the same 68 triggers and 43,771 pairs the review
  computed.

### Final verdict: publish with edits

- **Finding 1 (Major, comparable arms): fixed.**
  - The corrected primary applies the null's exclusion rule to real triggers: 68 triggers, 43,771 pairs, +0.00004
    (−0.00795 to +0.00847), H1 and H2 Inconclusive. I reproduced it exactly, with 3,014 observed against 3,012.2
    expected.
  - Clean windows: 109 triggers, 72,189 pairs, +0.00415 (−0.0024 to +0.01109).
  - Post-contaminated: 101 triggers, 65,887 pairs, −0.01319 (−0.019 to −0.00641).
  - Contamination share by quintile: 0.163, 0.278, 0.306, 0.360, 0.332.
  - 282 of the 350 triggers fail the rule.
  - The brief's explanation for 109 vs my 105 holds. With per-pair post windows (ending a median 27.6 h after
    origin), the contaminated class is 101 triggers / 65,887 pairs. With my earlier origin-to-+1.6 d window it is
    115 / 74,008, which reproduces the first review's numbers.
  - Decomposition of the preregistered −0.00306: post-contaminated pairs (28.8% of pairs) contribute −0.00380,
    baseline-only −0.00057 and clean +0.00131. So "the negative excess comes entirely from contaminated windows"
    holds.
  - One note, with no action needed. "Post-contaminated" counts an M ≥ 6.5 anywhere from origin to post-window end,
    including the few hours before the counted window opens. The report states that definition. Counting only
    events inside the window itself, the share still rises with strain, from 12% to 23–26%.
  - Title, verdict and plain terms are rewritten, and the preregistered "H2 Refuted" stays beside the correction.
- **Finding 2 (Moderate, station population): fixed.**
  - Title and verdict now say about 1,500 long-running stations. The population is 1,496 of 9,336 (16.0%), with a
    median of 212 valid pseudo-triggers, so the SE of p0 is about 0.017.
  - The Results section caveats the station map ("should not be read station by station"). The figure's own caption
    file is unchanged, which is acceptable.
- **Finding 3 (Moderate, detectability): fixed.**
  - The verdict states the recall: 0.4575, and 0.5238 at M ≥ 3 (`proxy_validation.json`).
  - It also states the doubling-in-a-day size of a detectable rise, and that instantaneous triggering is untestable
    (instant variant −0.01386).
  - The title is scoped to day-scale rises.
- **Finding 4 (Minor, things checked): unchanged and still right.**
  - `primary.json`: 15,042 observed against 15,742.2 expected.
  - `trigger_dispersion.json`: ratio 10.0, 39 above 3 SE and 55 below.
  - Every preregistered variant gives H2 Refuted.
- **Gates:**
  - G5 passes (49 rows, in sync with the current report). The rows the first review flagged are rewritten and
    supported.
  - G6 passes (8 claims).

Remaining issues (text edits only; no reanalysis needed):

1. **H1 "Inconclusive in every analysis"** (verdict bullet) contradicts the report's own results table. The post hoc
   baseline-only row there is H1 Refuted (E5 − 3E1 upper95 −0.00225). Suggested wording: "Inconclusive in the
   corrected primary, the preregistered analysis and every preregistered variant; the contaminated baseline-only
   subset gives Refuted".
2. **"both are measured with about ±0.008 uncertainty"** ("No strain dependence is visible" bullet) is wrong for
   comparable arms. ±0.008 is the half-width of the overall mean. On the corrected primary, the quintile half-widths
   are 0.015–0.023 (E1 ±0.017, E5 ±0.023). Only the preregistered quintiles are about ±0.008. State both.
3. **(Suggested) "nothing grows with strain" in the title** reads close to a refutation of H1, but H1 is
   Inconclusive: E5 − 3E1 ranges from −0.066 to +0.048. "No rise with strain is seen" would match the verdict.
