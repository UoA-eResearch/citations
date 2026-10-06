# Independent review: "Did DOT's rules become LLM-written after its Gemini drafting plan?"

Adversarial review of the pre-review draft (commit 4259a92) against the preregistration (plan.md, commit 22616bf),
deviations D1-D8, the code and the results files. Written 7 October 2026 under the brief in `review/prompt.md`.
Everything below was checked by re-running the study's own code path (`./venv/bin/python`, cores 0-3) or by reading the
committed files; the reviewer's scripts are in the session scratchpad
(`/tmp/claude-1001/-mnt-citations/14121cdb-aa2a-421c-926d-b1c71589d0e4/scratchpad/recompute_{A..E}.py` and logs) and
were not added to the run directory.

## Recommendation: **fix first** (text and secondary analyses; the primary estimate and the Inconclusive verdict stand)

The primary estimate, its interval and the verdict reproduce exactly from the committed code; the decision rule was
applied as preregistered; the 2026 issues were verifiably untouched until the validation results and the MDE were
committed; the estimator changes D5 and D6 used 2019-2021 data only and preceded unsealing. None of the issues below
changes the verdict.

The report should nevertheless not be published as written, for four reasons:

1. It states that "every cabinet department's rules became somewhat more AI-like". By the study's own estimator,
   three of the fourteen departments fell (Justice, Education, HUD) and the largest (Commerce, 735 pre-period
   documents) barely moved (0.9% to 1.3%). The per-department monitoring series that plan section 6 promised was not
   produced (issue 1).
2. The validation section misdiagnoses why the pseudo-document construction undercovers (bias, not clustering), and
   the explanation of the wider-than-predicted interval is right in direction but misstated: the documents were
   always heterogeneous (nothing "appeared from 2025"), V2 ignored that by uniform injection, and the estimator's
   lower boundary, never mentioned, collapsed the intervals of every cell that sat at raw α = 0 (issues 2 and 3b).
3. DOT's +4.0 pp change is confounded by a large shift in DOT's own sub-agency mix (FAA from 46% to 30% of documents,
   PHMSA from 13% to 29%), and the sub-agency estimates are wildly heterogeneous (Office of the Secretary 21%, NHTSA
   9%, PHMSA down from 13% to 2%, FAA at the floor). The report does not mention sub-agencies (issue 4).
4. The formal verdict is a coin flip on the bootstrap seed and the report does not say so: under twelve seeds the
   upper bound ranges 4.84-5.11 pp and the preregistered rule returns Refuted in six of them (issue 3). The committed
   seed was fixed before unsealing, so Inconclusive stands, and on the study's realised precision (about 6.7 pp
   detectable) it is also the right verdict on substance; but "by a hair" is the wrong description.
5. Several statements are overclaimed or misdescribed: the Unicode-marker check "rules out" nothing (the corpus shows
   the typesetting normalises non-breaking spaces), the excess-word selection criterion, and the deregulatory regex
   (issues 5-8).

Verdict-relevant numbers are confirmed to every digit; see the table at the end.

## 1. Decision rule, primary estimate and verdict logic (brief item 1)

- `analysis.verdict()` implements plan section 5 exactly: Supported iff DiD >= 0.05 and lo > 0; Refuted iff
  DiD < 0.02 and hi < 0.05 and MDE <= 0.05; otherwise Inconclusive. The placebo downgrade (|DiD| >= 2 pp) is applied
  only to Supported, as the plan says. `verdict()` was already in this form at commit 5a0011f (D2), before any
  validation run. The DEREG regex, the splits and the event study were also committed then.
- **Reproduction.** Rebuilding the estimator (`validate.build_estimator`), the dedup (277 near-duplicates dropped,
  as reported) and the per-document log-likelihood ratios, then calling `analysis.did()` with the module seed
  (20261007) and B = 2000 gives DiD = 0.005639834638119283, lo = −0.042574139589165325, hi = 0.05101331449288119:
  identical to `primary.csv` to every digit. Point estimates for all four group-periods match likewise (DOT −0.38% /
  +3.61%, others +1.56% / +4.98%, n = 697 / 265 / 3,190 / 1,126).
- MDE: power at injected DiD = 3 pp is 33/40 = 0.825, at 2 pp 0.70, at 5 pp 1.00; `MDE_80 = 0.03` follows from the
  grid. With 40 replicates the 95% binomial interval on power at 3 pp is roughly 0.67-0.93, so "MDE = 3 pp" could
  equally be 2 or 5 pp; this does not matter for the rule, because the rule needs MDE <= 5 pp and power at 5 pp is 1.00.
- Placebos: P1 −0.02 pp (−0.72, +0.84), P2 +0.23 pp (−1.45, +1.79); both below 2 pp. Note that P2 is degenerate for
  DOT: both DOT values sit at the estimator's lower boundary (raw α = 0, calibrated −0.70%), so P2 has no power to
  detect a DOT-specific change and its interval is driven entirely by the comparison group (issue 11).

**Issue 3 (must fix): the verdict boundary is within bootstrap Monte Carlo error, and "by a hair" is the wrong
frame.** The upper bound that decides Refuted versus Inconclusive is a 97.5th percentile of 2,000 draws of a quantity
with standard deviation about 2.4 pp; the Monte Carlo standard error of that percentile is about 0.14 pp, larger than
the 0.10 pp margin. Re-running `analysis.did()` with B = 2000 under twelve seeds (the preregistered 20261007 and
1-11), on the same per-document ratios and calibration draws: the point DiD is +0.56 pp in every run; the lower bound
ranges −4.44 to −4.06 pp; the upper bound ranges 4.84 to 5.11 pp (mean 4.97, sd 0.11), and **falls below 5.00 pp in
6 of the 12 seeds**, under which the preregistered rule returns Refuted (seeds 1, 2, 3, 6, 9, 11 give 4.87, 4.94,
4.85, 4.90, 4.86, 4.84; seeds 4, 5, 7, 8, 10 give 5.05, 5.09, 5.11, 5.06, 5.00). The committed seed's 5.10 is the
second-highest of the twelve. The preregistered seed was fixed in code before unsealing, so the committed verdict is
the legitimate one, but the report must disclose that the formal verdict is a coin flip on the bootstrap seed, and
should stop describing the outcome as decided "by a hair" in favour of Inconclusive. The
realised interval (9.4 pp wide) implies a realised minimum detectable DiD of about 6.7 pp (2.8 × 9.36/3.92), above
the 5 pp that the rule's own Inconclusive clause treats as the floor of adequate power. On the study's substance,
Inconclusive is the right verdict whichever side of 5.0 the upper bound fell; the report should say so instead of
presenting the verdict as a near miss of Refuted.

## 2. Sealing and timing (brief item 2)

Verified:

- `sha256sum -c` on the 188 sealed issues: 188/188 OK; `SEALED_MANIFEST.sha256` is byte-identical to the copy in
  22616bf; the manifest was written at 14:52:02, the plan committed at 14:52:44 (all times NZDT, +13:00).
- `paragraphs_sealed.parquet` was written at 03:50:53 on 7 October; `validation_v2.csv` at 03:49:06; the D7 commit
  (validation results and MDE) at 03:50:16. The parse of 188 issues takes roughly a minute, so `parse.py sealed`
  began within seconds of, and possibly before, the D7 commit landing. Parsing produces no estimate, and the
  validation files were on disk 70 s earlier, so this is a procedural technicality, but D8's "parse.py sealed (03:50
  NZDT)" should state the overlap honestly (issue 14a).
- `mle.py` (00:37) and `validate.py` (00:57) were not modified after D6 (00:57:58) and are identical in commits
  ac766f3, 7893932, 938da56 and 4259a92. `analysis.py` changed between D7 and D8 only in `dedup()` (the `q`
  Series fix and `update_batch`) and in the empty-group guard, exactly as D8 says. After D8 only `figures.py` (a
  legend and the capped-V2 curve), `explore_words.py` (labelled exploratory) and `build_report_html.py` changed.
- `plan.md` has one commit. The decision rule never changed. Deviation timestamps are consistent with commit times
  (D1 14:55, D2 22:27/22:30, D3 23:32, D4 23:57, D5 00:43, D6 00:57, D7 03:50, D8 04:28).

Not verifiable, and the report should say so (**issue 14b, should fix**): only the 2026 issues were sealed. The
2022-2025 text, including the whole pre-period and both placebo windows, was parsed on 6 October at 14:55 and sat
unsealed on disk while D2-D6 were decided. The plan's assertion that no LLM-fraction estimate was computed on any
2022+ text before D7 cannot be checked from artefacts (the D5 "quick checks" are described as scratchpad runs, not
committed). I found nothing that contradicts it, but the report currently reads as if the sealing protected the whole
design; it protected the post period only. Say that in the Sealing paragraph and in the caveats.

## 3. The estimator (brief item 3)

What is implemented matches what is described:

- Paired reference (D5): `p_A(w) = clip(p_H(w) × p_r(w)/p_s(w), 1e-6, 0.999)` with add-0.5 smoothing in all three
  rates; `p_s` from the source paragraphs of the 80% reference keys only; weights `w = logit p_A − logit p_H`
  range from −1.40 to +4.43, none clipped.
- Calibration (D5/D6): a = 0.5366% (raw α on the generation pool's human documents), b = 0.7695 (raw α on the
  C half, 77.49%, minus a); 2,000 calibration draws by resampling generation-pool documents and C-half paragraph keys;
  `cal_draws` applies draw i to bootstrap draw i; in `did()` the same i is used for all four groups, so a cancels and
  b_i rescales the whole DiD. Correct.
- Bootstrap: documents resampled with replacement within each group-period (`alpha_boot`), B = 2000 for the primary,
  1000 for placebos and splits, 300 for the event study and LOGO. As described.
- Sets: human pool (60%), generation pool (20%; sources, a-calibration, V2 background), validation pool (20%; V1, V2
  background); generated paragraphs split 80% reference / 20% held-out, held-out split C/V by md5 parity. The vocabulary
  uses only human-pool and reference sentences. No leakage into V1 or into the outcome estimates. Two mild
  circularities to disclose: (i) a is fitted on the same source documents that define r(w); (ii) P1's 2019-2021
  baseline is the generation + validation pools, i.e. it includes the a-calibration documents, whose calibrated α is
  about 0 by construction (P1 is ~0 anyway).

Problems:

**Issue 2 (must fix): the V1 pseudo-document result is misdiagnosed, in D5, D6 and the report.** The report says the
pseudo-document construction "undercovers badly (58-66% at 5-10%), because it hides document-level variation", and
D5 says "its bootstrap CI ignores between-document variation". In that construction there is no between-document
variation to ignore: sentences are an i.i.d. draw from the pooled validation sentences, randomly partitioned into 290
chunks, so the chunk bootstrap is a valid sentence bootstrap for that design. The intervals miss because the
estimator is biased by +0.6 to +1.0 pp at α >= 2% (the ~4% slope error between halves C and V), and the pseudo-document
intervals are only 1.7-2.3 pp wide, so bias ≈ half-width. Coverage is worst exactly where bias/width peaks (5-10%) and
recovers at 0% (bias 0.3 pp) and at 25% (width 3.7 pp). The "documents" construction covers 88-100% only because real
document heterogeneity doubles its width (3.6-4.8 pp) and swallows the same bias. The correct statement is: the
estimator carries a systematic relative bias of about +4%, and single-group intervals cover only when document
heterogeneity makes them wide enough to absorb it. For the DiD this bias is multiplicative and nearly cancels, which
is worth saying explicitly.

**Issue 3b (should fix, with issue 3): the explanation of the wider-than-predicted interval is right in direction
but misstated, and it omits the boundary.** The report attributes the 9.4 pp realised width (versus ~4 pp in V2) to
AI-like text "that appeared from 2025" being "concentrated in some documents rather than spread evenly", whereas V2
"injected it evenly". Decomposing the real DiD's bootstrap variance by cell (seed 20261007, B = 2000, raw scale):
DOT-post sd 1.58 pp (74% of the DiD variance), others-post 0.81 pp (20%), others-pre 0.35 pp (4%), DOT-pre 0.31 pp
(3%); the total reproduces the interval (2.39 pp calibrated). V2's DiD sd was 1.0-1.2 pp at every injected level,
including 5-7.5% where the synthetic DOT-post sits at the real one's level with similar n (290 versus 265). So the
real DOT-post is about 1.8 times more variable than a uniformly injected synthetic group: heterogeneity of α across
real documents is indeed what V2 missed. Two corrections are needed, though. (i) Nothing "appeared from 2025": by
every measure I computed the per-document distribution is as heavy-tailed in 2024-25 as in 2026 (share of documents
with per-document raw α > 0.25: 12.8% / 14.0% for DOT pre/post, 11.3% / 11.7% for others; share of AI-like sentence
mass in the top 10% of documents 0.82-0.85 in all four cells). Documents were always heterogeneous; V2 ignored that by
design, and the floor hid it wherever a cell sat at raw α = 0. (ii) The lower boundary is a second mechanism the
report never mentions: the MLE is constrained to [0, 1], so a cell at or near raw α = 0 has bootstrap draws piled at 0
and a collapsed interval. In the real DOT-pre cell 21.5% of the 2,000 draws are exactly 0; in V2 the three uninjected
groups (2019-2021 text at raw α ≈ 0.5-0.8%) were all in that regime, which is why V2's DiD interval was essentially the
DOT-post interval alone. The same mechanism makes the quarterly DOT intervals 2-3 pp wide while DOT sat at the floor
(16 of 31 quarters at raw 0) and 7 pp once it lifted, so the report's "yearly average width" argument partly measures
the boundary, not heterogeneity. Fix: drop "appeared from 2025"; state that V2's uniform injection understated
between-document variance and that its floor-level baseline groups contributed almost none; recommend a V2 that
injects document-level heterogeneous shares into all four groups.

**Issue 11 (should fix): boundary censoring is pervasive and unreported.** 16 of DOT's 31 quarters, both DOT P2
windows, and DOT's 2024-2025H1 window sit at raw α = 0. The estimator cannot represent "less LLM-like than the pooled
human reference", so DOT's baseline is left-censored, and a change measured from a censored baseline is understated
whenever DOT's latent value lies below the floor. Report the score of the log-likelihood at α = 0 (sign and size) for
the censored cells, or run a sensitivity that allows α slightly below 0 where the likelihood is finite.

**Issue 13 (should fix): a prompt-leak token in the vocabulary.** "supplementary" has the largest weight in the
vocabulary (w = 4.43; e^4.43 ≈ 84× likelihood ratio) because the DRAFT prompt says "Write one paragraph of the
SUPPLEMENTARY INFORMATION section" and some generators echo it ("In the supplementary information, it is noted
that…", Nemotron sample). It is the 10th-largest contributor to the comparison group's 2026 rise. The effect is
small, but prompt-induced tokens (here also "preamble", "point" if they qualified) should be excluded from the
vocabulary by rule, and the report should say the vocabulary was screened for them. Also disclose that 113 of OLMo's
4,000 polish outputs begin "Here is the revised…" and 98 gpt-oss polish outputs contain Markdown bold.

Calibration scope (expert point, section 8): b = 0.77 means the paired reference under-fits even its own generators'
held-out text by 23%. The slope for text produced by DOT's actual Gemini deployment is unknown and could differ in
either direction; "calibrated share of LLM-assisted sentences" is therefore a scale anchored to these five
generators, not a measured fraction. The report's caveat on references should say this in those terms.

## 4. Validation (brief item 4)

- V1 and V2 are implemented as D5-D7 describe (50 replicates per level, two constructions; V2 at the real counts
  732/290/3,295/1,178 drawn with replacement from 2,566 generation + validation documents, injection into DOT-post
  only, 40 replicates per δ, B = 300). The capped sensitivity matches (MDE 5 pp).
- The report is honest about the coverage shortfall (88% at 5%) and the 12% false-positive rate, and about the
  3 pp planned versus ~7 pp realised. Three precision points to add: (i) 12% is 5/40 = 12.5%, with a 95% binomial
  interval of roughly 4-27%; (ii) with 50 replicates, 88% versus the 90% criterion is within one standard error
  (4.5 pp), so "narrowly missed" is fair but "indistinguishable from the criterion at this replicate count" is more
  accurate; (iii) V2 intervals used B = 300, the analysis B = 2000, so the 12% is for a slightly different procedure.
- The bias criterion is reported as "met" with a worst case of +0.98 pp at 10%. Say "met with 0.02 pp to spare, and
  exceeded (+1.02 pp) at 25%".

## 5. Group assignment and filters (brief item 5)

Spot checks of `fr_groups.parquet` (38,833 documents):

- Independent agencies are excluded as intended: EPA (4,717 non-templated documents), FCC, NRC, SEC, CFPB, Federal
  Reserve, FTC, CFTC, FDIC, SBA, OPM, Postal Service, Surface Transportation Board (85; correctly excluded although it
  sits inside DOT organisationally), NTSB. VA is correctly in the cabinet group.
- Edge cases to disclose (**issue 17, minor**): `dept_of()` takes the first listed agency that resolves to a
  department, so joint rules led by OMB (27), OPM (9), SBA (5), FHFA (2) land in the cabinet group, and three
  EPA-first joint rules (EPA/NHTSA fuel-economy actions) land in DOT. FERC, an independent regulatory commission that
  the FR API nests under Energy, contributes 66 documents (52 pre, 14 post) to the cabinet group; removing it changes
  the comparison group from 1.56→4.95% to 1.18→5.00%. Commodity Credit Corporation and FCIC (USDA-owned) are fine.
- **The `subagency` column is uninformative.** `groups.py` takes `agencies[0].name`, but the FR API lists the parent
  department first, so every DOT document has subagency "Transportation Department". The diagnostic printed by
  `groups.py` ("DOT sub-agencies") therefore showed nothing. Use `agencies[1]` (see issue 4).
- Templated classes: the regex removes 74.3% of DOT documents (airworthiness directives, airspace), 18.4% of the
  cabinet group's (Coast Guard zones), and nothing substantive that I could find (no non-templated title contains
  "Anchorage"; the non-EPA/USCG/FAA matches are all genuine ADs or airspace actions).
- **Issue 9 (should fix): DOT's "non-templated" set is still dominated by FAA routine families.** Titles matching
  special conditions, route/airway/RNAV/VOR amendments, petitions, corrections and similar are 57% of DOT's 2019-2021
  documents, 43% of the pre period (312 of 732) and 29% of the post period (84 of 290). MinHash at Jaccard >= 0.8
  does not catch them (they share structure, not text). They sit at the floor and are the documents least likely to
  be drafted with Gemini, so they dilute any DOT signal. Excluding them moves the point DiD from +0.56 to +1.26 pp
  (DOT −0.05 → +4.64 on 390/184 documents). The report should disclose the composition and this sensitivity.
- Near-duplicates: the "family" is each document's own LSH neighbour set, not a transitive closure, so the rule is
  conservative (keeps more than "one per family per quarter" when similarity is not transitive). State it (minor,
  issue 19).
- **Issue 10 (should fix): the procedural filter is leaky, and the leak grows over time.** The preregistered regex
  misses "Regulatory Impact Analysis" (no "regulatory analys" substring), "Regulatory Planning and Review",
  "Severability", "Administrative Procedure Act"/good-cause sections, "Environmental Review", "Promoting International
  Regulatory Cooperation" and similar. Those paragraphs read as 6-14% AI-like. The flagged procedural share of DOT
  paragraphs rose from 8% (2019-2024) to 21% (2025-2026) as DOT's documents got shorter (5,748 → 4,369 words) and
  more boilerplate-heavy, so period-dependent leakage was a live risk. I recomputed with a broadened regex
  (preregistered + the headings above): DOT −0.44 → +3.52, others +1.48 → +4.78, DiD +0.67 pp (versus +0.58). The
  primary is robust; the report should state the leak and this check rather than leave "procedural paragraphs are
  excluded" unqualified. For contrast, restricting to "background/discussion/comments/summary" headings only gives
  DOT −0.32 → +6.93, others +3.81 → +5.31, DiD +5.8 pp (point estimate, no interval, reviewer-defined subset): the
  point DiD is sensitive to which paragraphs count, which is another reason not to over-read +0.6.
- **Issue 8 (should fix):** `DEREG = rescind|rescission|remov|withdraw|deregulat|eliminat`. The plan and the report
  list "rescind, remove, withdraw or deregulat". "rescission" is harmless; "eliminat" is an undocumented addition
  (fixed before unsealing, at D2). Make the report match the code.

## 6. Numbers in report.md against the results files (brief item 6)

Every number I checked matches (table at the end). Residual nits (**issue 20, minor**): "2-4 pp from 2019 to 2024"
should be "2-4.3 pp" (comparison group 2021 = 4.3 pp); "12%" is 12.5%; "11-19%" is 10.7-18.8%; "+1.0 pp" for
"without nemotron" is +0.95 pp. **Issue 7 (should fix):** the excess-word lists are selected by frequency ratio
("deregulatory" 2.9×, "unleashing" 2.9×, "deregulation" 3.0×) but introduced as "the largest rises". By absolute
excess the comparison group's largest rises are "general", "establish", "part", "order", "after", "burdens", "thus",
"via" — generic connectives, several of them ("thus", "via", "after") also LLM-leaning. State the criterion (ratio
among words with excess above some floor) and show both lists, or the paragraph's conclusion ("policy words, not
classic AI marker words") is not what the table says.

## 7. Interpretation and overclaiming (brief item 7)

**Issue 1 (must fix): "every cabinet department" is false and the promised monitoring series is missing.** Plan
section 6 lists "α by agency and quarter for every cabinet department: the monitoring series" as a secondary analysis.
No such table exists in `results/tables/`. Computing department-level calibrated α (non-procedural, pre versus post,
point estimates):

| Department | n pre / post | 2024-25 | Feb-Sep 2026 | Change |
|---|---|---|---|---|
| Commerce | 735 / 245 | 0.9% | 1.3% | +0.4 |
| Treasury | 388 / 158 | 3.4% | 8.3% | +4.9 |
| HHS | 384 / 189 | 0.4% | 6.3% | +5.9 |
| Interior | 347 / 95 | 5.4% | 7.5% | +2.2 |
| USDA | 279 / 108 | 0.1% | 1.4% | +1.4 |
| Energy (incl. FERC) | 238 / 52 | 3.1% | 4.7% | +1.5 |
| Defense | 190 / 24 | 2.5% | 14.0% | +11.5 |
| DHS | 161 / 53 | 0.3% | 2.3% | +2.1 |
| Labor | 160 / 54 | 1.2% | 7.0% | +5.9 |
| Justice | 104 / 94 | −0.3% | −0.7% | −0.4 |
| Education | 79 / 28 | 4.6% | 3.2% | −1.3 |
| VA | 77 / 13 | −0.7% | 8.7% | +9.4 |
| HUD | 58 / 18 | 0.8% | −0.7% | −1.5 |
| State | 42 / 22 | 1.9% | 16.2% | +14.2 |

Eleven of fourteen rose, three fell, and the rise is driven by HHS, Treasury, Labor and several small departments,
while Commerce, USDA, Justice, HUD and Education stay at or near the floor. "Government-wide" should become "in most
departments, unevenly", the sentence "every cabinet department's rules became somewhat more AI-like" (In plain terms)
and the tile text "the same rise" should go, and the monitoring series (department × quarter) should be produced as
preregistered, with the caveat that department-level intervals are wide. Department composition of the comparison
group also shifted (HHS 12% → 16% of documents, Justice 3% → 8%, Defense 6% → 2%, Energy 7.5% → 4.4%); reweighting
the 2026 department estimates to the 2024-25 document shares gives 5.06% against 4.95% actual, so composition is not
what moves the comparison group, but say so.

**Issue 4 (must fix): DOT's own composition shifted, and its sub-agencies disagree.** Using `agencies[1]`:

| DOT sub-agency | n pre / post | share pre → post | 2024-25 | Feb-Sep 2026 |
|---|---|---|---|---|
| FAA | 335 / 88 | 46% → 30% | 0.4% | −0.6% (floor) |
| PHMSA | 80 / 69 | 13% → 29% | 13.5% | 2.3% |
| FRA | 74 / 29 | 10% → 10% | −0.7% (floor) | 1.6% |
| NHTSA | 64 / 30 | 9% → 11% | −0.7% (floor) | 9.1% |
| FMCSA | 47 / 24 | 7% → 8% | −0.7% (floor) | 3.4% |
| FHWA | 46 / 4 | 6% → 1% | −0.6% | (n < 5) |
| Office of the Secretary (department only) | 40 / 12 | 5% → 4% | −0.7% (floor) | 21.3% |
| FTA | 19 / 7 | | floor | floor |

Pooled DOT moved −0.36% → +3.62%. Reweighting the 2026 sub-agency estimates to the 2024-25 shares gives 2.56%;
reweighting the 2024-25 estimates to the 2026 shares gives 3.37%. So between 1.1 and 3.7 of DOT's 4.0 pp change is
attributable to the FAA → PHMSA shift in what DOT published, and the within-sub-agency change is between +0.3 and
+2.9 pp. These are point estimates on censored sub-agency values and should be treated as rough, but two things in
the table are too large to omit from a report about DOT's drafting: the Office of the Secretary's twelve 2026 rules
read 21% (the Secretary's office is where ProPublica placed the Gemini initiative), and PHMSA's 80 pre-period rules
read 13.5%, far above every other DOT sub-agency before the announcement. The latter coincides with DOT's 2025Q3 spike
(143 documents, 3.3%), the quarter of the PHMSA/FAA deregulatory batch. If any of that batch was AI-assisted, the
pre-period is contaminated by treatment and the DiD is biased toward zero. The clean-baseline sensitivity (pre =
2024-01 to 2025-06, where DOT is at the floor) gives DiD +0.30 pp, so the pooled conclusion does not change, but the
report must show the sub-agency table, discuss the PHMSA pre-period level, and present OST and NHTSA 2026 as the
cells to watch.

**Issue 12 (should fix): no discussion of drafting-to-publication lag or treatment intensity.** Rules published in
February-April 2026 were drafted in 2025; final rules reflect NPRMs drafted earlier still; OIRA review adds months.
ProPublica reported a December 2025 demonstration and a plan, not an adoption date, and the first known Gemini-drafted
FAA rule was then unpublished. The post window therefore mixes untreated and treated documents in unknown proportion,
and the estimand is an intention-to-treat effect on published text. The report's only related caveat ("Published text
only") is about editing, not timing. Add a lag caveat and note that 2026Q3 (DOT 5.7%, its highest) is the first
quarter likely to contain mostly post-announcement drafting.

**Issue 5 (must fix): the Unicode-marker claim.** "This rules out text pasted unmodified from those tools, unless
the Federal Register's typesetting normalises the characters." The corpus answers the "unless": across 2.77 million
paragraphs from 2019-2026 there is not one ordinary non-breaking space (U+00A0) either, a character that is routine in
Word-drafted legal text ("§ 1.1", "5 U.S.C. 553"), while curly quotes (539,000 paragraphs) and em dashes (103,000)
survive. GPO's composition pipeline evidently normalises spaces and (plausibly) hyphens. The check is uninformative,
as D4 itself half-says ("A zero share is not evidence against LLM use"). Delete "rules out" and report the check as
a null that cannot discriminate.

**Issue 6 (should fix): "Deregulatory documents are not the cause."** Removing deregulatory-*titled* documents tests
a title, not the hypothesis. The administration's vocabulary (EO 14192 cost discussion, "unnecessary", "outdated",
"regulatory", "statutory") pervades all 2025-26 rules; "regulatory" (w = +0.65) is the single largest contributor to
the 2026 rise in both groups. The paragraph's conclusion ("cannot separate AI drafting from a change in what rules
are about") is right; the bold heading contradicts it. Reword to "Removing deregulatory-titled documents does not
remove the rise; the policy vocabulary is spread across all documents".

Other interpretation points:

- "In plain terms" opens with "The answer is no detectable DOT-specific change". Readers will take that as "no
  change". Say "We found no DOT-specific change, but the test was too imprecise to rule out a DOT-specific rise of up
  to about 5 points" (**issue 21, should fix**).
- Pre-LLM quarters already reach 4.1% (DOT 2020Q3, n = 23) and 4.0% (comparison 2021Q1). Those are the estimator's
  false-positive range on this genre; 2025-26 levels of 4-6% sustained over five quarters are different in kind
  from a one-quarter spike, but the report should state the historical noise range when it interprets 3-6% readings
  (**issue 16, should fix**).
- The exploratory analysis is correctly labelled "exploratory, after unsealing" and the splits "secondary". Good.
- "To our knowledge this is the first agency-level, preregistered test on the Federal Register" is adequately hedged.
  Atkinson & O'Bryan (arXiv 2607.04543, ICML 2026 TAIGR workshop) exists and is described accurately.

## 8. What a computational social scientist or an LLM-detection methodologist would object to (brief item 8)

1. **Treatment is intention, timing and intensity are unknown** (issue 12). A DiD on publication dates with a
   December-2025 demonstration and multi-month drafting lags is an ITT design with heavy attenuation. The report should
   adopt that language and recommend re-estimation with a longer post window.
2. **Composition, not parallel trends, is the main threat** (issues 1, 4, 9, 17). The study pools fourteen
   departments and ten DOT sub-agencies without fixed effects or reweighting; both mixes moved. A department/sub-agency
   fixed-effects DiD (or a reweighted comparison) is the standard remedy and is cheap here; at minimum report the
   decomposition above.
3. **The estimator measures distance from a 2019-2021 cabinet-wide style, not AI use.** Procedural boilerplate reads
   11-19% in every period; leaked boilerplate 6-14%; PHMSA's 2024-25 rules 13.5%; pre-LLM quarters up to 4%. Liang et
   al. validate their estimator against distribution shift in prompt and model, but not against a simultaneous
   genre/policy shift in the human corpus, which is exactly what 2025-26 brings. Human adoption of LLM vocabulary
   (Yakura et al. 2024, Kobak et al. 2025) further blurs the construct. The report's caveats cover this fairly; the
   sub-agency table makes it concrete.
4. **Calibration transfer.** b = 0.77 on the generators' own held-out text; the slope for real Gemini-in-DOT text is
   unknowable from this design. LOGO and Gemma-only ranges (−0.0 to +1.0 pp) are the right robustness checks and are
   reassuring about direction, not about scale.
5. **Lower boundary and censoring** (issue 11). Liang et al.'s MLE is also bounded, but their corpora sit well
   above 0; here half of DOT's history is at the floor. A two-sided or offset-baseline formulation would be more
   informative for a "did it rise" question.
6. **Sentence weighting.** α is sentence-weighted; the top 10% of documents carry 82-85% of the AI-like sentence
   mass in every period. A document-weighted or length-trimmed estimate would be a useful secondary, and the report
   should say which weighting the plain-language numbers refer to.
7. **Monte Carlo and replicate counts** (issues 3, 15). B = 2000 for a decision threshold 0.1 pp from the estimate;
   40 replicates for a 5% false-positive rate; 50 for a 90% coverage criterion. All are too few for the precision the
   decision rule assumes. Recommend B >= 10,000 for the primary (one-off cost) and reporting Monte Carlo error.

## Numbered issues with locations and fixes

| # | Severity | Location | Problem | Fix |
|---|---|---|---|---|
| 1 | must fix | report.md In plain terms ("every cabinet department"), tiles.json ("the same rise"), plan §6 | Claim contradicted by department-level estimates (3 of 14 fell; Commerce flat); preregistered monitoring series not produced | Produce `results/tables/monitoring_by_department.csv` (α by department × quarter, with intervals); replace "every"/"government-wide" with "most departments, unevenly, led by HHS, Treasury, Labor, Defense, State, VA"; add the department table |
| 2 | must fix | report.md Validation bullet 3; deviations D5 §3, D6 "Cause" | Pseudo-document undercoverage attributed to ignored clustering; actual cause is +0.6-1.0 pp bias against 1.7-2.3 pp widths | Rewrite: estimator has ~+4% relative bias; single-group intervals cover only when wide; bias nearly cancels in a DiD |
| 3 | must fix | report.md Caveats bullet 1, In plain terms "by a hair", Results "Verdict" | Verdict boundary within bootstrap MC error (SE of the upper bound ≈ 0.14 pp against a 0.10 pp margin); realised MDE ~6.7 pp > 5 pp | Report seed sensitivity and MC error; state that Inconclusive holds on substance regardless of the 5.0/5.1 margin; drop "by a hair" |
| 3b | should fix | report.md Results "The interval is wider than validation predicted" | Heterogeneity explanation right in direction (real DOT-post bootstrap sd 2.05 pp vs V2 DiD sd 1.0-1.2 pp) but "appeared from 2025" is false (per-document distribution equally heavy-tailed in 2024-25); boundary mechanism (21.5% of DOT-pre draws at raw 0; V2's three uninjected groups at the floor) not mentioned | Reword; add the variance decomposition (DOT-post 74%, others-post 20%, pre cells 6%); note V2's design limits |
| 4 | must fix | report.md (no sub-agency content), groups.py `subagency` | DOT composition shift (FAA 46→30%, PHMSA 13→29%); sub-agency α from −0.7% to 21%; PHMSA 13.5% pre; 1.1-3.7 of DOT's 4.0 pp is composition | Fix `subagency = agencies[1]`; add the sub-agency table and decomposition as a secondary; discuss PHMSA pre-period and OST/NHTSA 2026; add clean-baseline sensitivity (+0.30 pp) |
| 5 | must fix | report.md Model-free checks bullet 1 | "rules out text pasted unmodified" — the corpus has zero U+00A0 in 2.77M paragraphs, so the typesetting normalises | Report as non-discriminating; cite the U+00A0 evidence |
| 6 | should fix | report.md "Deregulatory documents are not the cause" | Title-based removal cannot test the vocabulary hypothesis; "regulatory" is the top contributor in both groups | Reword heading and body as above |
| 7 | should fix | report.md Word-frequency changes | Lists are top-by-ratio, introduced as "largest rises"; top-by-excess are generic connectives | State criterion; show both |
| 8 | should fix | report.md Robustness "Deregulatory titles", plan §6 | Code regex adds "rescission" and "eliminat" | Match text to code; log as a deviation line |
| 9 | should fix | report.md What was done (filters) | 43%/29% of DOT's non-templated documents are FAA routine families | Disclose; add the exclusion sensitivity (+1.26 pp) |
| 10 | should fix | parse.py PROC, report.md Text paragraph | Procedural regex misses RIA/APA/severability etc.; DOT flagged share 8→21% | Disclose the leak and the broad-filter check (+0.67 pp); list missed headings |
| 11 | should fix | report.md Event study, Placebos | 16/31 DOT quarters and both DOT P2 cells at the floor; P2 has no power for DOT | Say so; report score at α = 0 or allow α < 0 as a sensitivity |
| 12 | should fix | report.md Caveats | No drafting-lag / ITT caveat | Add; flag 2026Q3 as first mostly-treated quarter |
| 13 | should fix | mle.py vocabulary, report.md Estimator | Prompt-leak token "supplementary" (w = 4.43); OLMo "Here is the revised…" preambles | Exclude prompt-induced tokens; strip chat preambles; disclose |
| 14 | should fix | report.md Sealing; deviations D8 | (a) parse began within seconds of the D7 commit; (b) 2022-25 text never sealed, "no estimate before" unverifiable | State both plainly |
| 15 | minor | report.md Validation | 12% = 5/40 (CI 4-27%); 88% vs 90% within 1 SE; V2 at B = 300 | Add the uncertainty |
| 16 | minor | report.md Event study | Pre-LLM quarters already reach 4% | State the historical noise range |
| 17 | minor | groups.py, report.md | FERC (66 docs), OMB/OPM/SBA-led joint rules in cabinet group; 3 EPA-first rules in DOT | Disclose; optional FERC exclusion (no material change) |
| 18 | minor | generator_revisions.json | Nemotron revision not recorded (plan: "recorded at download") | Record it |
| 19 | minor | analysis.py dedup docstring | "family" is the LSH neighbour set, not a closure | Say "conservative" |
| 20 | minor | report.md | "2-4 pp" (4.3), "12%" (12.5), "11-19%" (10.7-18.8), "+1.0" (+0.95) | Correct |
| 21 | should fix | report.md In plain terms | "no detectable DOT-specific change" reads as "no change" | "could not detect; consistent with up to ~5 pp" |

## Recomputed numbers

All recomputations use the study's code (`mle.py`, `validate.build_estimator`, `analysis.dedup/did`) and data;
"point" means a point estimate without an interval.

| Quantity | report.md | results file | Recomputed | Status |
|---|---|---|---|---|
| Primary DiD | +0.6 pp | 0.005640 | 0.005639834638119283 (seed 20261007, B = 2000) | match (all digits) |
| 95% CI | −4.3, +5.1 | −0.04257, 0.05101 | −0.042574139589165325, 0.05101331449288119 | match (all digits) |
| DOT 2024-25 / 2026 | −0.4% / 3.6% | −0.00384 / 0.03608 | −0.38% / +3.61% | match |
| Others 2024-25 / 2026 | 1.6% / 5.0% | 0.01557 / 0.04985 | +1.56% / +4.98% | match |
| Documents | 697 / 265 / 3,190 / 1,126 | same | same (meta 732/290/3,295/1,178 → in XML 716/273/3,242/1,153 → after dedup) | match |
| Near-duplicates dropped | 277 | 277 | 277 | match |
| Verdict | Inconclusive | Inconclusive | Inconclusive (hi 0.0510 ≥ 0.05) | match |
| Seed sensitivity of upper bound | not reported | — | 12 seeds: hi 4.84-5.11 pp (mean 4.97, sd 0.11); hi < 5.00 in 6 of 12 → formal rule gives Refuted in 6 of 12; lo −4.44 to −4.06 | new; verdict is seed-dependent |
| MDE (80% power) | 3 pp | 0.03 | 3 pp (power 0.70 / 0.825 / 1.00 at 2 / 3 / 5 pp) | match |
| False-positive rate at δ = 0 | 12% | 0.125 | 12.5% (5/40; 95% CI ≈ 4-27%) | nit |
| V1 documents: estimate / coverage | 0.3, 2.8, 5.8, 11.0, 26.0 / 100, 100, 88, 90, 96 | same | same | match |
| V1 pseudo-doc coverage | 58-66% at 5-10% | 0.58, 0.66 | same; widths 1.9-2.3 pp vs bias +0.9-1.0 pp | match; explanation wrong |
| Calibration a, b | 0.5% raw, 77.5% raw | 0.005366, 0.7695 (C half 0.7749) | same | match |
| Vocabulary | 859 | 859 | 859; weights −1.40 to +4.43 ("supplementary" max) | match |
| P1 / P2 | −0.0 (−0.7, +0.8) / +0.2 (−1.5, +1.8) | −0.00017 (−0.0072, 0.0084) / 0.0023 (−0.0145, 0.0179) | from file | match |
| Event study 2025Q3-2026Q3 | others 3.8/5.3/5.7/3.9/5.0; DOT 3.3/2.0/0.0/1.5/5.7 | same | same | match |
| DOT 2026Q3 CI | −0.8 to +9.7 | −0.0077, 0.0974 | from file | match |
| DOT quarters at floor | "most ... through 2025Q2" | — | 16 of 31 (all before 2025Q3) | match |
| Quarterly CI widths by year | 2-4 pp 2019-24 (DOT 2020 6); 6-7.5 pp 2025-26 | — | DOT 2.1/6.0/2.9/2.2/2.6/2.3/7.1/7.5; others 3.1/3.6/4.3/2.4/2.6/3.5/6.3/6.6 | nit (4.3) |
| Realised interval width / implied MDE | 9.4 pp / "about 7 pp" | — | 9.36 pp / 6.7 pp | match |
| LOGO range | −0.0 to +1.0 pp | −0.0002 to +0.0095 | from file | match (0.95) |
| Gemma 4 only | +1.0 (−5.3, +6.0) | 0.00996 (−0.0528, 0.0597) | from file | match |
| Final / proposed rules | +4.5 (−2.1, +8.9) / −3.9 (−7.8, −0.1) | 0.0448 / −0.0392 | final rules point +4.48 | match |
| Deregulatory titles | −11.3 (−19.2, +0.6); 4.2→15.7%; 18 DOT docs | same | from file | match |
| Procedural paragraphs | 11-19%; DiD +4.8 (−1.9, +10.8) | 10.7-18.8%; 0.0478 | point: DOT 15.2→18.5, others 12.1→10.7 | nit (10.7) |
| Em dashes per 1,000 words | 0.53/0.64/0.83; 0.62/0.63/0.74 | same | from file | match |
| U+2011 / U+202F share | 0 everywhere | 0.0 | 0 in 2.77M paragraphs; also 0 U+00A0 | match; interpretation wrong |
| No-dereg exploratory | 3.6→3.7; 5.0→4.7; 6.6-8.4% | same | from file | match |
| Top-20 word share | "under half" | — | 44.5% (DOT), 48.6% (others) | match |
| Excess words, others | "deregulatory, unleashing, burdens, deregulation" | top by excess: general, establish, part, order… | ratio-ranked | criterion unstated |
| Manifest | b8a470f9…, 188 issues | — | 188/188 OK; unchanged since 22616bf | match |
| Broad boilerplate filter | not reported | — | DiD +0.67 pp (point) | new |
| Clean baseline 2024-01..2025-06 | not reported | — | DiD +0.30 pp (point) | new |
| FAA routine titles excluded | not reported | — | DiD +1.26 pp (point) | new |
| Department-level change | "every department rose" | — | 11 of 14 rose; Justice, Education, HUD fell | contradicts |
| DOT sub-agency 2026 | not reported | — | OST 21.3% (n = 12), NHTSA 9.1%, FMCSA 3.4%, PHMSA 2.3% (13.5% pre), FAA −0.6% | new |
| Composition share of DOT's +4.0 pp | not reported | — | 1.1-3.7 pp | new |
| Concentration (top-10% docs' share of AI-like mass) | "concentrated ... appeared from 2025" | — | 0.84 / 0.82 / 0.85 / 0.85 (DOT pre/post, others pre/post); per-doc raw α > 0.25: 12.8% / 14.0% / 11.3% / 11.7% | "from 2025" not supported |
| Bootstrap sd by cell (raw, pp) | not reported | — | DOT-pre 0.31 (21.5% of draws at 0), DOT-post 1.58, others-pre 0.35, others-post 0.81; DiD sd 2.39 pp calibrated | new |
| V2-implied DiD sd | "about 4 pp" width | widths 3.96-4.66 pp | sd 1.0-1.2 pp at every δ | match |

## Closing

The study's procedural discipline is good: the preregistration is specific, the sealing is verifiable, every change
is timestamped and matches the commit history, and the verdict follows the rule. The weaknesses are in what the
report says about its own validation and about the government-wide pattern, and in the two confounders it never
looks at: DOT's shifting sub-agency mix and the drafting lag. Fix those, produce the preregistered monitoring series,
and the Inconclusive verdict can be published with the caveats it deserves.
