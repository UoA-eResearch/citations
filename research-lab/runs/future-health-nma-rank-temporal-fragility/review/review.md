# Independent review: `future-health-nma-rank-temporal-fragility` (pre-review draft, commit 9340e97)

Reviewer: independent adversarial review, 2026-10-18. Scope: plan.md (6152aa8), deviations.md (D1–D3), report.md /
report.html, all code, the released tables, the raw nmadb snapshot, data/std, jobs.json, holdouts.csv, fits.jsonl and
the V1/V3 evidence. Everything I ran is under `review/reviewer_checks/` (scripts, tables; caches under `cache/`).
Nothing outside `review/` was modified.

## Recommendation: **fix first**, then publish

The three verdicts (H1 Refuted, H2 Refuted, H3 Supported) reproduce exactly from fits.jsonl and survive every
correction I could apply. But the released results rest on two defects that must be fixed and the affected numbers
regenerated before publication, because the report describes both as working:

1. the preregistered largest-component rule for disconnected pre-update networks never executed (a bug in
   `code/nma.R`); every disconnected holdout failed instead, which excluded one primary network, dropped 10 secondary
   fits and 687 random-control fits concentrated in 39 networks;
2. two of the 29 contrast-level direction calls (501220, 501274), both labelled "high confidence", are inverted.

The fixes are mechanical (about 700 refits, which I have already run) and move no verdict: with both corrected, H1 is
35/177 = 19.8% (14.6–26.3%), the random control is 15.4% against 19.8%, and the contrast-level sensitivity rate is
18.9% instead of 18.1%. Several framing claims also need softening (issues 9–12).

## Numbered issues

### 1. The largest-component rule is broken; disconnected pre-update networks fail instead of being reduced (serious)

- **Location.** `code/nma.R`, `largest_component()`: `memb <- nc$subnet.comparisons` then
  `tapply(P$studlab, memb, ...)`. In netmeta 3.6.1 `netconnection()$subnet.comparisons` has one entry per *distinct
  comparison* (5 entries for the 11 contrast rows of 501229's T10 network; 10 for 24 rows in 501403), so `tapply`
  stops with "arguments must have same length". The `is.null(memb)` fallback never runs. Reproduced in
  `reviewer_checks/probe_error.R`.
- **Evidence.** fits.jsonl holds 905 failed fits; 702 of them are this error or netmeta's own "Network consists of 2
  separate sub-networks": 2 T10 fits (501229, primary; 501403, iv), 10 secondary fits (S1/S3 of 479807, 480029,
  480492, 481695, 482109, 501283, 501308, 501384, 501403, 481856) and 687 random holdouts. The random failures are
  not spread evenly: 65 of 200 in 479993, 63 in 481588 and 480492, 57 in 501253, 46 in 479531 (`reviewer_checks/
  recompute_verdicts.py` output; 27 primary networks have fewer than 200 usable random fits).
- **Consequences in the report.** "pre-update fit failed: 2" and the counts 176 / 173 / 169 are artefacts of the bug;
  plan §4 says these networks are analysed on their largest component. The negative control silently drops exactly the
  random holdouts that remove a bridging study.
- **Recomputed with a working rule** (`reviewer_checks/refit_failed.R`, components from `netconnection()$D.matrix`;
  `recompute_with_fixes.py`): 697 of the 702 fits now succeed (the remaining 5 are genuine: two singular systems in
  479993 random fits, three one-treatment components). 501229 enters the primary set with no flip (a new entrant takes
  the top). H1: **35/177 = 19.8% (Wilson 14.6–26.3%)**; H2: mean P(best) 0.607 vs retention 0.802; random control
  **15.4%** vs 19.8%, difference 4.4 points (−1.0 to 9.8); the previously failed random holdouts flip 12.4%, so
  dropping them had biased the random rate slightly *upwards*; S1 59/175 = 33.7%, S2 26/177 = 14.7%, S3 57/174 =
  32.8% (P(best) 0.593 vs retention 0.672). No verdict changes.
- **Fix.** Replace the membership lookup (e.g. component ids from finite entries of `nc$D.matrix`, mapped through
  `treat1`), re-run the 702 fits, regenerate primary.json / network_results.csv / figures, and change the report's
  exclusion line and all n's. State explicitly that disconnected pre-update networks are reduced to their largest
  component (the plan's inclusion rule 4 says the *full* network must be connected; the code would also have reduced a
  disconnected full network, though none was).

### 2. Two contrast-level direction calls are inverted, both "high confidence" (serious for the sensitivity set and for D2's credibility)

- **Location.** `code/direction.py` `IV` dict and `results/tables/direction.csv`; the fits of 501220 and 501274 in
  fits.jsonl and network_results.csv.
- **501220 (root coverage, MD in recession reduction).** The sheet carries a treatment table the parser missed
  (names in column I, codes to their right in column J): 1 = CAF, 2 = CAF+CTG, 3 = CAF+BM, 4 = CAF+EMD, 5 = CAF+ADM,
  6 = CAF+PRP, 7 = CAF+CM. The study's basis ("CAF (t1) vs CAF+CTG (t2) +0.44/+0.52 ... so effect = t2 vs t1") has the
  codes backwards: in those rows t1 = 2 (CAF+CTG) and t2 = 1 (CAF). Under the study's `good`, CAF+CTG ranks *below*
  CAF, GTR above CTG (Zucchelli 1998 −0.60, Trombelli 1998 −0.90, Tatakis 2000 −0.40 for GTR vs CTG) and CAF above
  CAF+ADM and CAF+EMD (Woodyard 2004 +1.23, Pilloni 2006 +0.93) — against every anchor in the root-coverage
  literature. The call must be `bad`. Corrected, the network's T10 result changes from no flip to a flip.
- **501274 (advanced colorectal cancer, OS log HR).** Treatment table: 1 = F, 2 = FI, 3 = I, 4 = O, 5 = FO, 6 = FB,
  7 = FIB, 8 = FIO, 9 = FOB, 10 = IO, 11 = B. The Hurwitz 2004 row is t1 = 2 (FI), t2 = 7 (FIB), TE = −0.4155 =
  log 0.66, the published HR for IFL+bevacizumab *vs* IFL; so TE = log HR(t2 vs t1), not t1 vs t2 as the basis says.
  N9741 (t1 = FI, t2 = FO, −0.4155 = log 0.66), NO16966 (t1 = FO, t2 = FOB, −0.1165 = log 0.89) and Saltz 2000
  (t1 = F, t2 = FI, −0.21) agree. Under the study's `good`, 5-FU monotherapy is the top-ranked treatment (P(best)
  0.21) above FOLFIRI+bevacizumab; corrected (`bad`), FIB is top in both fits (P(best) 0.76) with no flip.
- **Effect on reported numbers** (`recompute_with_fixes.py`, together with issue 1): "adding the 28 contrast-level
  networks" 37/204 = 18.1% becomes **39/206 = 18.9%**; "high-confidence calls only" 36/197 = 18.3% becomes
  **38/199 = 19.1%**. No verdict changes (the iv set is a sensitivity set), but D2's "22 calls are high confidence"
  is 20 right of 22, and the released direction.csv and network_results.csv carry two inverted networks.
- **Fix.** Correct both entries and their bases, refit the two networks, regenerate the iv sensitivity block, and
  revise D2 and the report ("Each network was adjudicated from placebo-controlled contrasts and landmark trials"). Add
  two guards: (i) the `treatments()` parser must also accept name-then-code layouts (it found a name table in only 92
  of 178 arm-level networks; a tolerant version finds 104, and it missed 501220's); (ii) after each full fit, flag any
  network whose top-ranked treatment is placebo / control / the catalogue's "Control intervention" — 501274's 5-FU
  top would have been caught.
- All 27 other contrast-level calls (and the 501216 exclusion) I agree with; my table with the evidence for each is
  `reviewer_checks/iv_readjudication.csv`.

### 3. The arm-level direction adjudication is asserted, not recorded (moderate)

- **Location.** `results/tables/direction.csv` gives every arm-level network the same basis string ("catalogue label
  (checked where labels disagree or the sheet has none)"); deviations D2 says 60 binary/rate and 30 continuous networks
  were checked against outcome text and arm data, but no per-network record exists.
- **My re-adjudication** (`reviewer_checks/sheet_labels.py`, `arm_direction_screen.py`,
  `arm_readjudication.csv`): 116 arm-level networks — all 21 where the sheet's own label contradicts the catalogue (7
  binary, 14 continuous), all 30 continuous networks (reading y's sign and scale), and all 56 further networks with an
  identifiable placebo/control arm (pooled control-arm outcome against the other arms under the call). **All 116 agree
  with the study's calls**, including the 501243 override; the four networks where control looks "better" are safety
  outcomes where actives are expected to have more events. The claim "the catalogue was right in all but one" holds
  on everything I could check.
- **Fix.** Release the per-network adjudication (sheet label, outcome text, control-arm comparison) so the claim is
  checkable; my `arm_readjudication.csv` can serve as a template.

### 4. `withheld_share` is wrong for contrast-level networks in the released network_results.csv (minor, released)

- **Location.** `code/analysis.py`: for contrast-level data `wshare = 1 − len(used)/d.study.nunique()`, but after
  the D3 split `studies_used` holds split *contrast* labels (`study_k`), so the "share" ranges from −0.59 to 0.40
  across the 28 iv networks. The column feeds only the full predictor model, which is fitted on the primary set, so no
  reported number changes. **Fix.** Count distinct original study ids (strip the suffix) or use the job's study list.

### 5. Empty "studies" are counted and withheld (minor)

- **Location.** `code/standardise.py` keeps rows with n = 0 or missing y; `code/nma.R` later drops their contrasts
  (`is.finite(TE)`), so the network loses studies silently. In the primary set: 479585 (Schiff 2009, r = n = 0 — and
  2009 is that network's whole T10 tranche year), 479808 (four 0/0 studies), 482475 (two arms with no mean), 501307
  (a one-arm study). `reviewer_checks/full_fit_coverage.csv`.
- **Fix.** Drop unusable rows at standardisation, count studies after that, and report the number dropped; V2 counts
  and tranche targets are inflated by them.

### 6. Publication years in the sheets are unvalidated and sometimes wrong, so the "newest tranche" can be the wrong studies (moderate, a limitation to state)

- **Evidence.** 479888 (iv): the sheet dates "VonHoff" (MPACT, nab-paclitaxel, published 2013) as 2002 and "Louvet"
  (GemOx, 2005) as 2013; the T10 tranche therefore withholds Louvet, VanCutsem (tipifarnib, dated 2012, published
  2004) and keeps MPACT in the pre-update set. V1 verified parsing against the sheet, not the sheet against reality,
  so it cannot catch this.
- **Fix.** Say so in Limitations; spot-check a sample of study years against Europe PMC (as V3 does for titles) and
  report the error rate; consider a sensitivity analysis dropping networks with an implausible year.

### 7. The V1 note on combined labels is inaccurate (minor)

- `results/tables/v1_parse_validation.csv` (501220): "combined labels take the later year". The D1 rule takes the
  *last* year in the string; in 480666 that is the earlier one ("Agosti 1997/Elkin 1989" → 1989, "Sung 2012/Rush 2011"
  → 2011; four such studies). No tranche changes in 480666, 501220 or 501373. **Fix.** Say "last year in the label" or
  take the maximum, and say which.

### 8. Framing of the negative control is stronger than the estimate (moderate, text)

- "The newest studies are not special" / "barely more disruptive" (report.md, Results and plain terms). The point
  estimate is a 28% relative excess (19.9% vs 15.5%), with an interval (−0.6 to 9.7; −1.0 to 9.8 after issue 1) that
  allows a 60% relative excess. The random holdouts also remove the same *number* of studies but fewer *participants*
  (the temporal tranche is a median 20% of participants against 15% of studies), so part of any difference is "more
  evidence removed", not "newer evidence". **Fix.** "We could not distinguish the newest studies from random studies
  of the same number: the difference is 4 points (−1 to 10)"; mention the participant asymmetry.

### 9. The calibration claims silently exclude new entrants (moderate, text)

- H2 and the plain-language "kept its top spot about 80% of the time" count retention only among treatments already
  in the network, as preregistered. Counting a new entrant that goes straight to the top as a loss: T10 retention is
  71% (P(best) 0.61 still understates, by 10 points), but S3 retention is **46%**, so over the longer horizon the
  stated 0.59 *overstates* by 13 points. "Over the longer horizon, the stated chance was about right" and "the fairer
  forecast test ... the curve sits close to the diagonal" hold only among incumbents. (Also: in 20 of 176 networks the
  P-score top is not the P(best) top; mean maximum P(best) is 0.62 against 0.61 — negligible.)
- **Fix.** Add "among the treatments already compared" wherever retention or calibration is claimed, and report the
  new-entrant-inclusive retention next to it (71% / 46%).

### 10. "Reading it as the chance this is still the top treatment next time is safe, perhaps too safe" (text)

- Overstated for the same reasons: it is conditional on no new entrant, on an update of about 15% of studies, and the
  0.4–0.6 bin is close to calibrated (0.50 against 63%) while the 0.2–0.4 bin's 71% rests on 28 networks (54–86%).
  **Fix.** "For the treatments already compared, over an update of this size, the stated probability was, if
  anything, conservative."

### 11. "A reasonable but fallible snapshot" — acceptable, with the qualifiers above. The comparison with Daly et al. (2019) is accurate (five data sets, studies removed one at a time, lowest quadratic-weighted kappa 40%); "random, not temporal, removal" should read "one-at-a-time, not temporal".

### 12. Unverifiable citation (minor)

- ISPOR "Souring on SUCRAs" (2022) has no OpenAlex record; give a full reference (authors, outlet, URL) or drop it.

### 13. Run-time comment is wrong (trivial)

- report.md "Reproducing it": "42,435 fits, ~20 min on 24 cores". logs/fits.err (00:59:33) to logs/fits.log
  (05:47:58) is 4 h 48 min.

### 14. Deviation D2's confidence labels (minor)

- "22 calls are high confidence" — two are wrong (issue 2); 7 of 7 medium calls are right. The labels did not track
  the actual error rate; say what "high" meant (a landmark-trial match, a sheet note) and recount.

### 15. Is moving the contrast-level networks to a sensitivity set justified?

- Yes, and it is not a hidden degree of freedom: the commit (28b0307, 00:51) precedes every fit (fits_full.jsonl
  00:56, fits.jsonl 05:47), it is logged with a reason, and the results are reported both ways. My finding of two
  inverted calls in 29 *supports* the separation: contrast-level sign conventions in nmadb are genuinely ambiguous and
  the adjudication error rate is not negligible. The report should say, though, that the primary N changed from the
  207 the plan implied to 176 by this decision, and keep the corrected iv numbers visible.

## What I checked and found right

- **Provenance.** Code commits precede their outputs: plan 00:36; standardiser/holdouts/engine 00:41; D1 00:43;
  V1 + D2 00:51 (before fits_full 00:56); D3 00:53; V2/V3 00:56–00:59 (before any holdout fit); analysis.py committed
  01:01 while the main run (started 00:59:33) was in progress and long before fits.jsonl (05:47); results and figures
  05:53. No code file changed between its commit and HEAD. data/ is untracked (file mtimes used).
- **Standardisation** (`reparse_check.py`, 32 networks re-parsed from the raw sheets with my own parser: 22 random
  included networks, 6 label-year, the two natural-scale, the "wide" one and 501220). Studies, arms, treatments, years
  and values agree exactly in 31; the 32nd (480666) is my parser not recognising its `studyID` label column, and its
  standardised years follow the stated D1 rule. The single "wide" sheet (479629) is in fact long layout with a `t`
  column and parses correctly. Natural-scale handling: 479757's seTE from CI (0.82, 0.65–1.03 → 0.1174) and 501200's
  from the text CI ("1.942-7.397" → 0.3412) are right; the malformed "6.04-40-291" gives 0.4823 instead of 0.4842.
  Undated studies: 24 primary networks hold 38, never withheld. Continuous y/sd/n layouts (11 inspected) are right,
  including the four sheets with an `se` column where `sd` was also present.
- **Holdouts** (`holdout_checks.py`): my independent T10 construction matches all 207 networks; S2 is the latest year
  in all; random holdouts are exactly T10-sized and drawn from dated studies only in all 207; median primary tranche
  15.4% of studies (max 50%, none above); 10 networks hand-recomputed in the table. New entrants handled as planned
  (18 of 176; 51 "flip or new entrant").
- **Fitting** (`probe_pscore.R`, `refit.R`, 10 networks: 8 random primary + 479757 and 501308). `small.values =
  "good"/"bad"` is accepted by netmeta 3.6.1 and stored as desirable/undesirable; `pscore()` equals `netrank(method =
  "P-score")` to 1e-16; `TE.random[i, j]` is θ_i − θ_j (checked against the direct log RR of study Martin in 473269:
  −0.3747); the rankogram's rank-1 probability concentrates on the P-score top; my refits reproduce every treatment
  set, every P-score (max |Δ| 5e-16), every top, τ² exactly, and P(best) within Monte-Carlo noise (max |Δ| 0.02); the
  restricted full-data P-scores are the same formula on the sub-matrix and my independent implementation reproduces
  all 35 flips.
- **Verdicts** (`recompute_verdicts.py`): see the table. Decision rules applied as preregistered.
- **Validations.** V2 counts (165/207, 106/168) reproduce. V3: I re-read 16 abstracts and checked the treatment codes
  behind the "?" names (501383 = fingolimod, 501431 = ACE inhibitor + CCB, 501392, 501299); all 16 codings are
  defensible (501392 is conservative: for the rebleeding outcome analysed, TIPS and EBL+EIS are the authors' lowest
  ORs and rank 1–2 here). "9 of 13" and "control at bottom in all 19" reproduce. V1 is adequate for parsing but not
  for the sheets' content (issues 2, 6): it never compared treatment names, which is how the 501220 table miss went
  unnoticed.
- **Numbers.** Every number in report.md, report.html, the figure captions and figures F1–F3 matches primary.json /
  network_results.csv (checked line by line; the only false statement is the run-time comment, issue 13).

## Recomputed numbers

| quantity | report | recomputed from fits.jsonl | with issues 1–2 fixed |
| --- | --- | --- | --- |
| primary networks | 176 | 176 | **177** (501229 restored) |
| H1 flips | 35/176 = 19.9% (14.7–26.4) | 35/176 = 19.89% (14.66–26.40) | 35/177 = 19.8% (14.6–26.3) |
| flip or new-entrant top | 51/176 = 29% | 51/176 (18 new-entrant tops, 2 overlap) | — |
| H2 mean P(best) / retention | 0.61 / 80% | 0.6071 / 0.8011 | 0.6066 / 0.8023 |
| H2 overstatement | −0.19 (−0.25 to −0.13) | −0.1941 (−0.2528 to −0.1317) | −0.196 |
| retention counting new entrants | not reported | 0.710 (T10), 0.456 (S3) | — |
| H3 Nagelkerke R² / AUC | 0.12 (0.04–0.24) / 0.69 | 0.1156 (0.039–0.240) / 0.686 | — |
| flip rate, gap < 0.05 / ≥ 0.2 | 24% / 7% | 24.4% (n = 41) / 7.3% (n = 55) | — |
| random control | 15.5%; diff 4.4 (−0.6 to 9.7) | 15.50%; 4.38 (−1.0 to 10.0) | 15.4%; 4.4 (−1.0 to 9.8); failed holdouts flip 12.4% |
| S1 | 34% (27–41) / 50% | 59/173 = 34.1% / 49.7% | 59/175 = 33.7% |
| S2 | 15% (10–21) / 18% | 26/176 = 14.8% / 18.2% | 26/177 = 14.7% |
| S3 | 34% (27–41) / 54% | 57/169 = 33.7% / 54.4% | 57/174 = 32.8% |
| S3 P(best) vs retention | 0.59 vs 66%, −7 (−14 to −0.3) | 0.590 vs 0.663 | 0.593 vs 0.672 |
| Kendall τ median; top-2 changed | 0.90; 43 (24%) | 0.905; 43 | — |
| common effect; SUCRA | 19.3%; 21.6% | 34/176; 38/176 | — |
| + contrast-level networks | 18.1% (37/204) | 37/204 | **39/206 = 18.9%** |
| + high-confidence calls only | 18.3% (36/197) | 36/197 | **38/199 = 19.1%** |
| median tranche share / participants | 15% / 20% | 0.154 / 0.196 | — |
| calibration bins retention | 71%, 63%, 88%, 31/32 | 0.714 (28), 0.625 (48), 0.875 (64), 0.969 (32) | — |
| inclusion cascade | 278/277/236/208/207/178+29/176+28 | 278/277/236/208 (29 label-year)/207/178+29/176+28 | 177 + 29 |
| fits; failed | 42,435; 887 random | 42,435; 905 (687 + 10 + 2 "same length", 201 arm-variance, 3 subnet) | 5 genuine failures remain |
| refit of 10 networks | — | identical treatments, P-scores (≤ 5e-16), tops, τ²; P(best) within 0.02 | — |
| direction re-adjudication | 1 catalogue error; 22 high / 7 medium iv | 116 arm-level agree; 27 of 29 iv agree | 501220, 501274 inverted |

## Files

- `reviewer_checks/probe_error.R` — reproduces the component-rule bug. `probe_pscore.R` — netmeta conventions.
- `reviewer_checks/refit.R`, `refit_comparison.csv` — independent refit of 10 networks.
- `reviewer_checks/refit_failed.R`, `cache/refit_failed.jsonl`, `cache/refit_corrected_direction.jsonl`,
  `recompute_with_fixes.py`, `recomputed_with_fixes.csv` — the 702 refits and the two corrected networks.
- `reviewer_checks/recompute_verdicts.py`, `recomputed_network_results.csv` — H1/H2/H3, control, secondary, bins.
- `reviewer_checks/holdout_checks.py`, `holdout_recompute.csv` — tranche recomputation for all 207 networks.
- `reviewer_checks/reparse_check.py`, `reparse_check.csv` — standardisation re-check (32 networks).
- `reviewer_checks/sheet_labels.py`, `sheet_labels.csv`, `arm_direction_screen.py`, `arm_direction_screen.csv`,
  `arm_readjudication.csv` (116 rows), `iv_readjudication.csv` (30 rows) — direction re-adjudication.
- `reviewer_checks/full_fit_coverage.py`, `full_fit_coverage.csv` — silently dropped studies.
- `reviewer_checks/cache/iv_dump.txt`, `cache/report_html_text.txt` — working dumps.
