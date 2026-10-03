# Research Lab

An agent-driven system for generating, ranking, and executing in-silico research projects
on this machine (32-core Xeon, 94 GB RAM, A100 80 GB, ~600 GB free disk).

## Components

| Piece | What it is |
|---|---|
| `leads.json` | The lead database: candidate research avenues with hypothesis, literature for/against, open datasets, value/cost scores, feasibility class, and a step-by-step subagent plan. Produced by the `research-lead-scout` workflow (10 domain scouts + completeness critic). Extended on 2026-10-02 by a second round (`research-lead-scout-round2.js`: 8 domain scouts + a calibration critic) with 32 leads in ecology, seismology, formal mathematics, AI evaluation, cheminformatics, computational reproducibility, law and digital humanities, and quantum simulation (80 leads in total). On 2026-10-03 a third round added 12 leads with Auckland / Aotearoa New Zealand local context (domain `auckland-nz`: hazards and climate, urban systems, health and society, environment), each with a `local_relevance` note, any `time_sensitive` deadline and any `needs_engagement` requirement (Te Mana Raraunga); 92 leads in total. |
| Interactive plot (Artifact) | Value (y) vs cost (x) scatter of every lead. Click a marker for full details. Golden quadrant = high value, low cost (top-left). Served from `index.html` on GitHub Pages and mirrored at https://claude.ai/artifact/FL86H7RkNAMkd4CbKserUx; after changing `index.html`, run `python3 build_artifact.py OUT.html` and republish OUT.html to that artifact URL to keep the two in sync. |
| `run-avenue.js` | The executor workflow. Give it one lead from `leads.json` and it runs the entire research workflow via subagents: scope → build → execute → adversarial review → write-up. |
| `runs/<lead-id>/` | Working directory created per executed lead: code, data, results, figures, report. |

## Lifecycle

```
scout (done) ──► leads.json ──► human picks leads from the plot
                                      │
                                      ▼
        Workflow({scriptPath: "research-lab/run-avenue.js", args: <lead object>})
                                      │
        1. SCOPE    preregistration-style analysis plan; verify data access
        2. BUILD    write pipeline code, smoke-test on a sample
        3. EXECUTE  full run, results + figures into runs/<id>/
        4. REVIEW   two adversarial reviewers try to refute the finding
                    (confounds, leakage, multiple comparisons, data errors)
        5. WRITE-UP report.md + figures, honest about what survived review
```

## Scoring rubric used in leads.json

- **cost_score** (x-axis): 1–2 hours-to-a-day CPU-only · 3–4 days with some GPU ·
  5–6 one-two weeks heavy compute · 7–8 near hardware limits, weeks ·
  9–10 exceeds this machine (see `requirements_if_out_of_reach`).
- **value_score** (y-axis): 2–3 minor replication · 4–5 solid incremental ·
  6–7 fills an actively-discussed gap · 8–10 major open question / broad impact.
- **feasibility**: `local` (fits comfortably), `stretch` (fits with care),
  `out_of_reach` (documented for completeness; requirements listed).

## Constraints honored by every lead

- Executable entirely in silico by AI agents (no lab, field, or human-subjects work).
- Prefers open datasets and open-access literature.
- Prior art recorded honestly in `lit_against`.

## Deep dives

| Lead | Status | Report |
|---|---|---|
| `astronomy-gwtc4-q-chieff-copula-stress-test` — is the q–χ_eff anticorrelation in GWTC-4.0 real? | Revised after three independent reviews and recalibrated against detection-consistent mocks. Preregistered verdict: **indeterminate**; every calibratable statistic is consistent with no dependence (low power). | [report.html](runs/astronomy-gwtc4-q-chieff-copula-stress-test/report.html) · [deviations log](runs/astronomy-gwtc4-q-chieff-copula-stress-test/deviations.md) |
| `bioinformatics-vep-acmg-calibration-drift` — do the ClinGen PP3/BP4 predictor thresholds still hold on variants classified since? | Revised after independent review. Thresholds hold on ClinVar as a whole; weakest in expert-curated disease genes (BayesDel Supporting/Moderate fall short on expert-panel labels); post-2022 ClinVar trends are composition. | [report.html](runs/bioinformatics-vep-acmg-calibration-drift/report.html) · [deviations log](runs/bioinformatics-vep-acmg-calibration-drift/deviations.md) |
| `climate-earth-record-margin-obs` — are heat records being broken by growing margins in station data? | Revised after independent review. Record-shattering (2003–2025) is **not yet visible** beyond mean warming: not distinguishable from a no-warming climate network-wide, new 30-year records ~20% below a steady-warming null (not established); outside the US new records are ~1.8× the no-warming rate. | [report.html](runs/climate-earth-record-margin-obs/report.html) · [deviations log](runs/climate-earth-record-margin-obs/deviations.md) |
| `health-econ-wastewater-flusight-value` — does influenza wastewater improve state flu-hospitalisation forecasts? | Revised after independent review. **No detectable gain** at an assumed 10-day reporting delay (relative WIS 0.995 [0.946, 1.045], 16 best-covered states; nothing added to the FluSight ensemble); exploratory: the signal is not ahead of admissions, and value appears only with reporting within days. | [report.html](runs/health-econ-wastewater-flusight-value/report.html) · [deviations log](runs/health-econ-wastewater-flusight-value/deviations.md) |
| `metascience-citation-context-replication` — does citing language before a replication predict its outcome? | Revised after independent review (fix-first). Preregistered classifiers failed validation and the positive control, so H1–H3 are **uninformative**; exploratory replication-failure keywords pass the control but predict only faintly before replication (AUC 0.53). | [report.html](runs/metascience-citation-context-replication/report.html) · [deviations log](runs/metascience-citation-context-replication/deviations.md) |
| `climate-earth-ai-humid-heat-attribution` — does the counterfactual moisture treatment change AI-forecast attribution of humid heat? | Revised after independent review (fix-first) and a sign-flip control. AIFS responds linearly; ~1–1.5 °C of peak wet-bulb temperature attributable; moisture treatment R = 1.21 pooled (≥1.5 **contradicted**; larger at 4–6 days and for area means) vs 4.4 statically; the response does not track the local surface signal. | [report.html](runs/climate-earth-ai-humid-heat-attribution/report.html) · [deviations log](runs/climate-earth-ai-humid-heat-attribution/deviations.md) |
| `comp-social-science-temp-accounts-vandalism` — did Wikipedia's switch from public IP addresses to temporary accounts increase vandalism? | Revised after independent review (fix-first) with an in-time placebo. **No detectable change**: the logged-out 48-hour revert rate moved +2.0 points [−2.9, +5.3] (H1 ≥ +10% inconclusive), no more than the design's seasonal bias (+2.7 points with dates shifted back a year); seasonally adjusted +0.1% [−17.8%, +11.0%]. | [report.html](runs/comp-social-science-temp-accounts-vandalism/report.html) · [deviations log](runs/comp-social-science-temp-accounts-vandalism/deviations.md) |
| `extra-open-neuroimaging-reanalysis-metaanalytic-prior-shrinkage` — is shrinking a small fMRI study's map toward a NeuroQuery prediction worth extra subjects? | Revised after independent review. **Refuted**: empirical-Bayes shrinkage of 15-subject maps lowered spatial accuracy in all six AOMIC domains (gain < 0.67× in four, 0.76–0.81× in two; ≥ 2× predicted); an oracle-tuned blend gains at most 1.39×. Strong effects vary most between people, so voxelwise shrinkage flattens peaks; it does cut effect-size error ~70% in weak-signal tasks. | [report.html](runs/extra-open-neuroimaging-reanalysis-metaanalytic-prior-shrinkage/report.html) · [deviations log](runs/extra-open-neuroimaging-reanalysis-metaanalytic-prior-shrinkage/deviations.md) |
| `llm-ml-science-mcf-emergence` — does answer-letter probability predict when a model learns multiple-choice format? | Revised after independent review. **Unsupported**: across 412 checkpoints of 28 runs, letter mass passes 0.5 within a few billion tokens almost everywhere, but only the two OLMo 7B runs ever leave chance (about 300B and 490B tokens, several tasks at once); H1 supported but uninformative, H2 not testable. Found stale duplicate weights in 11 pythia-2.8b Hugging Face branches. | [report.html](runs/llm-ml-science-mcf-emergence/report.html) · [deviations log](runs/llm-ml-science-mcf-emergence/deviations.md) |
| `cheminformatics-drug-discovery-cliff-noise-ceiling` — are benchmark activity cliffs real, or partly measurement noise? | Revised after independent review (fix-first, then confirmation pass). **Supported**: ~75% of MoleculeACE's 28,569 cliffs are not confidently real given ChEMBL 37 replicate noise (sigma 0.50 log, after removing the ~2/3 of 'replicates' that are re-reported copies); noise-only worlds reproduce 96–171% of the cliff error gap for all four models. The gap on 'high-confidence' cliffs is larger, but equally so in noise-only worlds: a selection effect. | [report.html](runs/cheminformatics-drug-discovery-cliff-noise-ceiling/report.html) · [deviations log](runs/cheminformatics-drug-discovery-cliff-noise-ceiling/deviations.md) |
| `auckland-nz-crl-structural-uplift-prereg` — is the City Rail Link's ridership jump structural or a novelty effect? | Preregistered (plan frozen 3 Oct 2026, before outcome data exist); calibration revised after independent review (fix-first). **Pending**: the 16 Feb–25 Mar 2027 train/bus ratio decides it, Supported at 0.266 or more and Contradicted below 0.253 (pre-opening baseline 0.222; opening week +36.5%). Confirmatory test ~April 2027. | [interim status](runs/auckland-nz-crl-structural-uplift-prereg/report.html) · [deviations log](runs/auckland-nz-crl-structural-uplift-prereg/deviations.md) |
| `auckland-nz-speed-limit-reversal-crashes` — did raising New Zealand speed limits back up in 2025 increase crashes? | Stage 1, revised after independent review (publish with edits). **Inconclusive**: injury crashes on 828 km of raised roads RR 1.03 (0.84–1.27) vs matched roads, 252 post crashes; MDE RR 1.33. All-crash 1.13 (1.02–1.26) is window-sensitive and exploratory. Daily NSLR snapshots running for the Stage-2 re-run (~Oct 2027). | [report.html](runs/auckland-nz-speed-limit-reversal-crashes/report.html) · [deviations log](runs/auckland-nz-speed-limit-reversal-crashes/deviations.md) |
| `auckland-nz-wastewater-testing-gap-deprivation` — are COVID-19 cases under-reported more in deprived towns, measured against wastewater? | Revised after independent review (publish with edits). **Inconclusive**: ratio 0.86 per SD NZDep2023 (CR1 0.68–1.09; CR2 0.64–1.17) across 57 towns; 27% power for the preregistered 15% gap; sensitive to integer-rounded zero-case weeks (0.83–1.00). H2 inconclusive (26 sites). | [report.html](runs/auckland-nz-wastewater-testing-gap-deprivation/report.html) · [deviations log](runs/auckland-nz-wastewater-testing-gap-deprivation/deviations.md) |
| `auckland-nz-equity-adjustor-waitlist-did` — did ending Auckland's ethnicity-inclusive waitlist score change who waits longest? | Revised after independent review (fix-first, then confirmation pass). **Inconclusive**: preregistered +7.2 pp (rank 1/16) but the Asian negative control widened +5.5 pp; post hoc, half is Auckland's regional dental list and the within-specialty change is ~3 pp (rank 2–3/16). Run without prior Māori/Pacific framing input at the lab owner's direction. Jul–Dec 2026 hold-out pending. | [report.html](runs/auckland-nz-equity-adjustor-waitlist-did/report.html) · [deviations log](runs/auckland-nz-equity-adjustor-waitlist-did/deviations.md) |

Skipped after a novelty check: `software-security-attestation-phantom-code`. Solarin et al. (2026,
arXiv:2608.18180) already compare 4,500 attested with 4,500 non-attested releases on PyPI and npm and recover source
commits from the attestations, which leaves only one metric (phantom-file rates by attestation status) for a new study.

Lessons from the first deep dive, to carry into the next ones (details in its deviations log, D19–D29 and D27c):

- **Get independent review before stating a verdict.** Both reviewers found real problems the main analysis had missed:
  a defective mock generator, a nuisance-sensitive statistic and a post-hoc decision rule.
- **Validate simulated data against the real data before quoting any false-positive rate.** Check Monte Carlo
  variance, measurement widths and boundary pile-up.
- **For gravitational-wave populations, use physical mock parameter estimation** (Gaussian in chirp mass, symmetric mass
  ratio, spin and distance, resampled to the PE prior). Translated likelihood shapes are not valid for the mass ratio.
- **Never run unpenalised MAP optimisation on a Monte Carlo selection-corrected likelihood.** It exploits injection
  sparsity.
- **Compare point estimates only under the same measure.** The PE prior alone can create the effect under study.
- **Check benchmark composition before reading a trend.** In the ClinVar study a threefold rise in apparent predictor
  performance came from one laboratory's bulk submission in previously unlabelled genes; standardise to a fixed gene mix
  and look at submitters before attributing a change to behaviour (circularity) or to the tools.
- **Make simulated catalogs detection-consistent.** Drawing events from found injections and adding independent noise biased a dependence
  estimate by −0.14 (half the null spread) until each mock event's likelihood included P_det(θ) (Essick & Fishbach, arXiv:2310.02017).
  Check a simulator by running the statistic at the true parameters with and without noise.
- **Write "pre-committed" rules only before any related result is known,** and record their timestamps.
- **Resample record statistics without replacement.** Bootstrapping residuals with replacement duplicates extreme values,
  which can then never be strictly beaten, so surrogate climates under-produce records (10–25% bias in the heat-record
  study). Use block permutation, and validate every null on synthetic data with a known answer.
- **When units share events, resample the events too.** Heatwaves set records at hundreds of stations in the same year;
  a bootstrap over places alone gave intervals 1.6–3.6× too narrow. Resample places and years (two-way), and check the
  interval's coverage on synthetic worlds whose dependence is measured from the data.
- **Verify real-time data rules against the hub's own forecasts.** The FluSight hub README's description of `as_of`
  would have leaked a week of future admissions; matching the hub baseline's median to candidate vintages settled it.
- **For "does source X add forecast value", run a positive and a negative control first, and scan the reporting lag.**
  Flu wastewater went from no value at a 10-day delay to a 6% gain at an (unreachable) 0-day delay.
- **Validate text classifiers on the target literature before trusting them.** A SciBERT model with F1 0.91 on its
  own (ML-paper) benchmark flagged 44% of psychology citation contexts as "negative"; true doubt was ~3%.
- **Compute a positive control on the same sample as the hypothesis,** and let a failed control make the null
  uninformative rather than "contradicted".
- **For perturbation experiments with AI models, run a sign-flip / scaling control.** A response that does not track
  the imposed signal member by member may still be real (AIFS responded linearly to scaled CMIP6 warming), or may be an
  off-manifold penalty; only the control distinguishes them. Report how unphysical the counterfactual starting state is
  (a temperature-only cooling left 17% of 925 hPa points saturated).
- **Run an in-time placebo for staggered rollouts.** Moving each wave's date back a year, on data from before
  anyone switched, produced a +2.7-point "effect" from school-holiday seasonality, larger than the real estimate.
- **Check a pre-trend test's size before reading it.** The joint 11-lead Wald test rejected 96% of the time on
  no-treatment data with random dates. A 5-lead test rejected 13% of the time, closer to its nominal 5%.
- **Read the dump's flags before trusting group labels.** Wikimedia's `mediawiki_history` marks cross-wiki imported
  revisions as anonymous; they were about 20% of German Wikipedia's "logged-out" edits until they were excluded.
- **Report how much weight rests on a single control unit.** After the last big wave, one not-yet-treated wiki
  carried 47% of the post-switch weight, and a wiki-level bootstrap does not capture that dependence.
- **Give synthetic validation data the real data's variance structure.** A shrinkage estimator passed a check with
  equal noise everywhere, then failed on fMRI maps, where between-subject variance grows with effect size (r 0.39–0.70).
- **Separate the machinery from the content.** A flat-prior arm showed that the false-positive inflation and most of
  the accuracy loss came from shrinkage itself, not from the meta-analytic or mismatched maps.
- **Report a magnitude metric alongside a pattern metric.** Spatial correlation and Dice ignore rescaling; mean
  squared error reversed the conclusion in the two weak-signal tasks.
- **Bound what any method could gain.** An oracle-tuned blend (≤ 1.39×) showed the prior itself was too weak, whatever
  the estimator.
- **Audit model checkpoints before trusting a trajectory.** Eleven pythia-2.8b Hugging Face branches carry a stale
  duplicate `model.safetensors` beside the real weights; identical results at different checkpoints are a red flag.
- **Bound every prefetch queue by disk, not just by concurrency.** Faster authenticated downloads let a thread pool
  fill 524 GB of disk ahead of the GPU.
- **Check what a model wants to say before calling it at chance.** OLMo-1B-0724 put its probability on a newline after
  "Answer:"; read after the newline, it answered well above chance.
- **Test the sensitivity of "first crossing" rules.** A two-in-a-row crossing can be followed by long reversals; a
  must-hold-to-the-end variant changed one run's lead time from about 100× to under 4×.
- **Check public 'replicates' for copies.** About two-thirds of inter-document replicate pairs in ChEMBL carry identical
  values re-reported in later papers; treating them as independent drove a MAD-based noise estimate to zero.
- **Apply any selection rule to the null world too.** Restricting to 'high-confidence' cliffs enlarged the error gap in the
  real data and equally in noise-only simulations; without the null it would have been read as 'real cliffs are hard'.
- **Check a noise model against the data it is applied to,** not only the data it was fitted on: a heavy-tailed model that
  fitted replicate differences predicted more extreme benchmark differences than exist.
