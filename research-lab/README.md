# Research Lab

An agent-driven system for generating, ranking, and executing in-silico research projects
on this machine (32-core Xeon, 94 GB RAM, A100 80 GB, ~600 GB free disk).

## Components

| Piece | What it is |
|---|---|
| `leads.json` | The lead database: candidate research avenues with hypothesis, literature for/against, open datasets, value/cost scores, feasibility class, and a step-by-step subagent plan. Produced by the `research-lead-scout` workflow (10 domain scouts + completeness critic). |
| Interactive plot (Artifact) | Value (y) vs cost (x) scatter of every lead. Click a marker for full details. Golden quadrant = high value, low cost (top-left). |
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
