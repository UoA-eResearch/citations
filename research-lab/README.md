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
| `astronomy-gwtc4-q-chieff-copula-stress-test` — is the q–χ_eff anticorrelation in GWTC-4.0 real? | Draft, revised after two independent adversarial reviews. Preregistered verdict: **indeterminate**. | [report.html](runs/astronomy-gwtc4-q-chieff-copula-stress-test/report.html) · [deviations log](runs/astronomy-gwtc4-q-chieff-copula-stress-test/deviations.md) |

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
- **Make simulated catalogs detection-consistent.** Drawing events from found injections and adding independent noise biased a dependence
  estimate by −0.14 (half the null spread) until each mock event's likelihood included P_det(θ) (Essick & Fishbach, arXiv:2310.02017).
  Check a simulator by running the statistic at the true parameters with and without noise.
- **Write "pre-committed" rules only before any related result is known,** and record their timestamps.
