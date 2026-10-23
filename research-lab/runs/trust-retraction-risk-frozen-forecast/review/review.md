# Review: trust-retraction-risk-frozen-forecast

Independent adversarial review of the draft at b314e0f, 2026-10-23. Scripts and outputs: `review/reviewer_checks/`
(c0 lookup sanity, c2 label dates, c3 evaluation and refits, c4 cohort scan and one-year-buffer test, c5 OpenAlex
agreement and re-typing, c6 PMC-host features). Nothing outside `review/` was modified; the sealed score file was not
opened; no per-paper score appears here or in any output file.

## Verdict: fix first

The preregistered verdicts survive (H1 Inconclusive by the rule; H2 Supported under every bootstrap, seed, buffer and
leave-Hindawi-out variant I tried, lower bounds 4.9–6.0 against a bar of 3). The report's explanation of them does
not. The frozen primary model is a degenerate fit whose log-loss is worse than predicting the base rate, 59% of its top
1% is PubMed-Central-hosted articles with 13 retractions among 36,987, and the title, plain-terms section and
"why the venue block can mislead" paragraph draw a conclusion about journal signals that the study's own ablations
contradict. H2's headline number is at the favourable end of its seed range and the "survives removing the dominant
publisher" claim was never tested (it holds, at about 7×, not 11×). One real leakage channel exists in the label dates
(Crossref self-updates), bounded here as small. H3's sealed rule is under-specified and the sealed model very likely
shares the degenerate fit. All of this is fixable without refitting anything that was frozen.

Provenance checks all pass: plan 2747646 (19:17:23) precedes the first label and pass-1 outputs (19:23:58, 19:25);
D1 df9aa9f (20:41:36) precedes the first model file (20:48); model_hashes.json committed in 660d682 at 20:51:12,
score.log created 20:51:14 (logs/ mtime), h1_h2.json written 21:06:05; the six model hashes and both forecast hashes
match the disk files; model_hashes.json is unchanged since 660d682; D2 (21:12) post-dates the results and says so.
Every number in the report matches the tables (recomputed independently in c3: E@k for all six models agree to three
decimals, the Poisson interval reproduces exactly), the figures match the tables, and the "Born Flawed?" numbers
(0.485 to 0.661, +0.176 [0.099, 0.252], 219/184, Zhang, posted 20 July 2026) are correct.

## Findings

### 1. Major. The frozen primary model is a degenerate fit; H1's 3.7× measures a failed fit, not venue information.

Evidence (c3_eval.json `frozen.hgb_full.pkl`):
- `validation_score_`: −0.00323 at iteration 0 (constant base-rate predictor), −0.00505 after the first tree,
  −0.03274 at iteration 5, −0.00585 at iteration 10 where it stopped. `train_score_` ends at −0.00557. Both are
  *worse than the constant model*. Early stopping fired because scikit-learn stops when none of the last 10
  iterations beats the iteration-0 reference (code/model.py:55-56 uses the defaults: `n_iter_no_change=10`,
  `l2_regularization=0`, `learning_rate=0.1`, `min_samples_leaf=20` counted in samples, not weight).
- Mechanism: with negatives weighted 20 and positives 1, the weighted base rate is ~3.6e-4; a near-pure positive leaf
  (20 positives, which the rate features `src_rate`, `host_rate`, `inst_max_rate` make easy to isolate) gets a raw
  value of order 1/p and saturates every validation negative that falls in it. `hgb_A_only` and `hgb_B_only` show the
  same first-iteration collapse and then recover (64 and 27 iterations); `hgb_no_A` improves monotonically from the
  first tree (32 iterations). So the one model that *lacks* venue rates is the one the recipe fitted properly.
- Same recipe, other seeds (c3 `refits`): E@1% = 3.9×, 6.9×, 2.9×, all stopping at 10. The H1 point estimate is
  a seed draw.
- Fixed iteration counts, no early stopping: 32 → 8.8×; 100 → 9.7× (4.6–12.3); 300 → 9.5× (4.4–11.7). Full model
  without `src_rate`/`host_rate` but with the rest of block A, early stopping: 8.9× (5.8–11.7).
- The frozen venue-only model reaches 8.0× (report table), i.e. venue features *alone* beat the full model by 2×.

Consequence: "venue signals do not hold up" (title), "Journal signals did not. Adding signals about the journal made
the ranking worse" (plain terms), and the whole "Why the venue block can mislead" paragraph (report.md:131-133) are
not what the data show. What is shown is that the preregistered fitting recipe is unstable on skewed rate features at
a 20:1 weight ratio.

Fix: keep H1 Inconclusive (the rule was preregistered and the frozen model is the frozen model), but (a) print the
validation curve and state the diagnosis in Results; (b) report the fixed-iteration refits as a labelled post-hoc
(D3), with the caveat that they are not frozen; (c) retitle, rewrite the plain-terms bullet and delete or invert the
"venue history misleads" explanation; (d) in "What this does and does not show", replace "Venue history alone is not a
reliable forecaster" with the honest statement that the primary recipe failed to fit.

### 2. Major. 59% of the full model's top 1% is PubMed-Central-hosted articles (13 retractions in 36,987); the report omits the publisher audit that shows it.

Evidence:
- results/tables/h1_h2.json `bias_audit.host."1299303238"`: cohort share 0.93%, top-1% share 59.0%. The report
  never mentions a host audit, although plan §5 lists "each of the 20 largest publishers in the top 1%" as a
  secondary and the number sits in the study's own table.
- The id is I1299303238, National Institutes of Health, the OpenAlex host organisation of PubMed Central
  (sources S4306525036 and S2764455111; c6: all 36,987 are `stype` = repository). c3 `top1_host_composition`:
  retraction rate inside the host 0.04% (a fifth of the base rate), 63% of *all* its test articles are in the full
  model's top 1%; the venue-only model does the same (61%). Within-host E@1% is 0.
- Why: `host_rate` for this host is 0.00126 (2021) and 0.00152 (2022) against 0.00003–0.00005 in every training
  year (data/lookup/rates.parquet rows for H 1299303238; c6) and 0.00028 for the rest of the cohort. The
  2018–2020 window picked up ~160–180 retracted COVID-era works whose primary location is PMC. The model learned
  "host_rate ≈ 1e-3 means risky" from genuine publishers and at test time fired on a repository whose rate had shifted
  30-fold. A repository is not a venue; 122,371 test articles (3.1%) have a repository primary location, with 14
  retractions.
- Excluding this host from the frozen full model's scoring: E@1% = 6.6× (4.1–11.5); excluding it and Hindawi:
  7.4× (4.3–12.6). The H2 model puts 0.1% of its top 1% there.

Fix: add the host table for both models, with names (full: NIH/PMC 59%, Elsevier 7.6%, Frontiers 5.7%, Springer
3.8%, Wiley 1.9%; H2: Elsevier 21%, Frontiers 8.7%, MDPI 7.8%, no host 6.9%, Wiley 5.9%, Springer 5.5%, Hindawi
4.7%). Report the PMC concentration in the H1 interpretation and in the ethics section. Decide, as a labelled post
hoc, whether repository primary locations belong in a venue model (exclude them or add a repository indicator) and
show the sensitivity; carry the decision into any future forecast.

### 3. Major (bounded). Crossref self-update dates are often the paper's own publication date, a channel by which later retractions enter the "as-of" features and the training labels.

Evidence (c2_label_dates.json, c4_scan_cohort_and_buffer.json):
- 27,548 of 77,002 Crossref targets are self-updates (notice DOI = article DOI). Where Retraction Watch also dates
  them (n ≈ 18,000): Crossref's year equals RW's in 70% and is *earlier* in 29%, by 1–10 years; Crossref's year
  equals the paper's publication year in 82%, against 27% same-year for RW retractions overall. Non-self notices
  agree with RW in 96%.
- labels.py:60 prefers the RW date, so the exposure is the 9,246 Crossref-only self-updates (11.7% of labels). For
  these the "updated" year equals the Crossref record's own creation year in 91% (8,447/9,232): the retraction is
  dated to the deposit of the article itself.
- In the cohort: 256 of the 2,813 training positives (9.1%) are Crossref-only self-updates, 184 of them dated to
  their publication year; i.e. up to 9% of training positives may be post-2020 retractions wearing a pre-2021 date.
  Test labels need no date (195 such test positives, harmless). The 335,818 author-retraction pairs and the
  reference and entity rates inherit the same dates.
- Bound: recomputing `auth_prior_ret_n/max` and `ref_retracted_share` for every test article with a one-year buffer
  (retraction year ≤ Y−2) and rescoring the frozen models: H2 11.36× → 11.21×, B-only 5.84× → 5.71×, C-only
  6.04× → 5.42×, full 3.73× → 3.43×. The share of test authors with a prior retraction falls from 10.1% to 8.7%.
  (The recomputation with the original Y−1 rule reproduces the stored features exactly, which also validates
  features.py's as-of logic, `ar_key` arithmetic included.) Multi-year mis-dating is not covered by the buffer, and
  `inst_max_rate` could not be buffered without the unsaved entity tables.

Fix: treat Crossref-only self-update dates as unknown: exclude those records from training labels and from the
as-of feature construction (keep them as undated test labels), or date them from PubMed/notice records; log it as a
deviation and report the sensitivity. Note in the Born Flawed comparison that Zhang excluded reference-retraction
share as inadmissible ("leaky contrast", +0.308 vs +0.176) precisely because OpenAlex carries current status; this
study's inclusion of it rests on registry dating, i.e. on this point.

### 4. Major (report). H2's narrative overstates robustness and under-describes the signal.

Evidence (c3):
- report.md:168-171 says the 11-fold concentration "survives removing the dominant publisher's influence". No
  leave-one-publisher-out was run for the H2 model (model.py:186 refits `SETS["full"]` only). Frozen H2 scored
  without Hindawi: 7.4× (5.4–9.3); H2 refitted without Hindawi in training and test: 6.7× (5.1–8.4); H2 ranking
  *within* Hindawi: 2.8×. Hindawi is 4.7% of H2's top 1% (about 1,870 articles) but roughly 70% of the retractions
  it catches (870 retracted in the top 1% overall against about 240 in the top 1% of the non-Hindawi set).
- Same recipe, seeds 1–3: 8.1×, 9.4×, 9.9×; fixed 10/32/100 iterations: 11.2×, 8.6×, 8.8×. The frozen 11.4× is
  the top of the range. All lower bounds stay ≥ 3 (4.9–6.0), under Poisson-host (6.0–14.1), multinomial-host
  (6.0–14.3), source-clustered (9.2–13.0) and iid-article (10.7–12.0) bootstraps, so Supported is safe; the
  headline should be "about 7–11×, 7× outside Hindawi".
- What the signal is: 90% of H2's top 1% has `inst_max_rate` > 0 (cohort 57%), 40% has an author with a prior
  retraction (cohort 10%), 8.6% cites already-retracted work (cohort 0.8%). 73% of retracted test articles have
  neither an author-prior nor a reference-retraction signal, and among such articles H2 still reaches 12.7×: the
  ranking leans on institutions' prior retraction rates, newcomer share and reference-list shape. "Paper triage,
  not only publisher triage" is literally true (no venue features) but a large part is *institution* triage, an
  entity-level proxy the ethics section should name alongside country.
- By year: 9.6× (2021), 12.4× (2022).

Fix: report the ex-Hindawi figures as the robustness result; give the seed range; describe the institution
component and add institutions to the bias audit (aggregate: share of top 1% from the ten institutions with the
highest `inst_max_rate`, say); soften the "11-fold" framing in title and plain terms.

### 5. Moderate. Retraction notices sit in the cohort as "articles"; the plan's OpenAlex `is_retracted` check is missing and would have shown it.

Evidence (c4, c5):
- 2,252 cohort "articles" are retraction-notice DOIs (Crossref notice DOIs with a different target, or RW
  RetractionDOI ≠ original): 935 train, 956 test, 361 forward. Test-window hosts: Dove Medical Press 228,
  Spandidos 188, Hindawi 170, Elsevier 115.
- OpenAlex marks 8,789 test articles `is_retracted`; 7,617 overlap the labels, 43 labelled articles are not flagged,
  and 1,172 flagged articles are *not* labelled. Their hosts (Dove 246, Spandidos 200, Hindawi 170, Elsevier 139)
  match the notice hosts, so most are notices OpenAlex flags as retracted, not missed retractions. Over all labels,
  77,845 of 78,857 carry the OpenAlex flag.
- plan §2 promised the agreement check "as a check"; neither the report nor any table has it. plan §1 promised
  exclusion counts; pass2.log has totals only.

Fix: drop notice DOIs from the cohort (negligible for E@k, 0.02% of the test set, but they are false negatives by
construction and some will rank high because they cite retracted work); report the OpenAlex agreement and the
exclusion counts as the plan said.

### 6. Moderate. H3's sealed rule is under-specified, and the sealed model very likely shares finding 1.

Evidence: forecast_seal.json `rule`; plan §5 H3; forecast.py:40 writes `wid, year, score` only.
- No decision rule: H1/H2 use the lower bound; H3 says "E@1% ≥ 3" without saying point or bound.
- No statement of which registry layers and which dating rule apply in 2028, nor that the cohort is fixed to the
  4,375,482 works of the 2026-09-22 snapshot (articles indexed later, including Oct–Dec 2026, are out; fine, but
  say so).
- The score file carries OpenAlex work ids only. Ids merge and are deleted; the wid→DOI map lives in unsealed
  `data/cohort_raw/`. Nothing committed pins it.
- 822 forward articles were already retracted at sealing (460 dated to their publication year); the rule does not
  say whether they count.
- The forward model used the same recipe and also stopped at 10 iterations (forecast_seal.json `iterations`), so
  it almost certainly has the same degenerate fit and the same PMC-host behaviour (`host_rate` for the NIH host is
  0.0002–0.0003 in 2025–2026, so the pattern may differ, but the fit will not). I did not open the model file.

Fix: commit a dated H3 addendum now, before any 2028 label exists: decision rule (lower bound ≥ 3, as H2), registry
layers and dating, cohort fixed to the sealed wids with a committed SHA-256 of a `wid, doi` file, exclusion of
articles retracted before the seal date. Consider sealing a second, clearly labelled, fixed-iteration forecast
alongside; never replace the first.

### 7. Minor. Leave-one-publisher-out is partial, and inherits the fragile fit.

model.py:186-189 drops the publisher's articles from training and test but the feature tables (`rates.parquet`,
`ar_*`, reference retraction shares) still carry its retraction history. Plan §5 wording allows this; say it. The
LOPO refits also early-stop at 10 iterations; my replicate with a different negative sample gives 4.69× against the
study's 5.05×, so the second H1 condition is as seed-dependent as the first.

### 8. Minor. Bootstrap choice decides H1's label; show the contrast.

Poisson(1) cluster weights with a fixed top-k set are a reasonable approximation (c3: multinomial cluster resample
gives 1.57–13.08 vs 1.38–13.26 for the full model, 6.04–14.31 vs 5.98–14.13 for H2). With 57% of positives in one
cluster the host-clustered interval is essentially a Hindawi in/out indicator, as the report says. Under iid-article
resampling H1 would read 3.3–4.2 and be *Refuted*; under source clustering 1.6–11.0. The preregistered choice stands,
but print the iid interval for contrast. Ties at the 1% boundary are immaterial (2,330 tied, 3 retracted; E@1%
between 3.73 and 3.77 under any tie-break).

### 9. Minor. Metadata completeness differs within publishers, but there is no sign of post-retraction edits.

Within Elsevier, retracted test articles lack references 3.6% of the time against 23.7% for the rest; Springer 0.2%
vs 7.7%; Hindawi 0.4% vs 0.5%. D2's restriction is the right response, and the within-publisher gap is most likely
item type (non-research items typed "article") rather than metadata altered after retraction. Re-typing is not
happening: retracted works are typed "article" 93–94% of the time for retraction years 2023–2026 against 65–83% for
2015–2022 (c5). The own-retraction leak (an article whose own retraction year ≤ Y−1 counting as its authors' prior)
affects 4 test articles, none in any top 1%.

### 10. Minor. Small departures from the plan to log.

- `newcomer_share` counts a first year equal to Y as a newcomer (features.py:78); plan §3 says "the two previous
  years". Harmless, log it.
- "Top 20 fields" is 10 codes because the two domains contain 10 fields. Say so.
- P4310319900 is Springer Science+Business Media, not Springer Nature; the label "Springer" is fine but the report
  should give the OpenAlex ids once.
- The report says the test label is "as of the registry fetch (2026-10-21)"; the raw files are dated 2026-10-22
  local time; fine, but the fetch log says 2026-10-21T21:16Z.
- Hindawi: 3,557 of its 4,374 test retractions are dated 2023 (81%), so "largely from its 2023 mass retraction" is
  right; 55% of all test retractions are dated 2023.

### 11. Ethics and exposure.

No per-paper information is in results/, logs/ or the figures; `top_1pct_threshold` in forecast_seal.json is a
score value, not a paper. `data/` is untracked by git. The misconduct and country statements are adequate as far as
they go; add (a) the institution dimension (finding 4), (b) the PMC-host concentration (finding 2), and (c) a line
that the country concentration is partly a Hindawi-era artefact to be re-measured in 2028.

## What I did not do

No GPU, no pip, no change outside review/. I did not refit the frozen models in place, open the sealed score file,
or scan the raw snapshot (the cohort and pass-1 arrays sufficed). Features were loaded by year; peak resident memory
was a few GB; CPU was capped at 4 threads, niced.
