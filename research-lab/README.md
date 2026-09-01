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
