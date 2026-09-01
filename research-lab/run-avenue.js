export const meta = {
  name: 'run-avenue',
  description: 'Execute one research lead end-to-end: scope, build, run, adversarially review, write up',
  phases: [
    { title: 'Scope', detail: 'preregistration-style analysis plan + data access check' },
    { title: 'Build', detail: 'implement pipeline, smoke-test on sample' },
    { title: 'Execute', detail: 'full run, results and figures' },
    { title: 'Review', detail: 'two adversarial reviewers try to refute' },
    { title: 'Write-up', detail: 'report.md incorporating review verdicts' },
  ],
}

// Invoke with: Workflow({ scriptPath: 'research-lab/run-avenue.js', args: <one lead object from leads.json> })
const lead = args
if (!lead || !lead.id || !lead.hypothesis) throw new Error('args must be a single lead object from leads.json (id, hypothesis, plan, datasets...)')

const RUN_DIR = `/mnt/citations/research-lab/runs/${lead.id}`
const HW = 'Hardware: 32-core Xeon, 94GB RAM, one A100 80GB GPU, ~600GB free on /mnt. Python available; create a venv inside the run dir. Be a good citizen: leave at least 100GB disk free, and clean up raw downloads you no longer need.'

const leadBrief = `RESEARCH LEAD ${lead.id}: "${lead.title}" (${lead.domain})
HYPOTHESIS: ${lead.hypothesis}
GAP: ${lead.gap}
METHOD SKETCH: ${lead.method}
DATASETS: ${JSON.stringify(lead.datasets)}
SUGGESTED PLAN: ${(lead.plan || []).join(' | ')}
KNOWN PRIOR ART / CHALLENGES: ${(lead.lit_against || []).join(' ; ')}
RISKS: ${lead.risks}`

phase('Scope')
const SCOPE_SCHEMA = {
  type: 'object', required: ['viable','analysis_plan','data_verified','success_criteria','notes'],
  properties: {
    viable: { type: 'boolean' },
    analysis_plan: { type: 'string', description: 'preregistration-style: endpoints, tests, controls, exclusions' },
    data_verified: { type: 'string', description: 'what was actually checked: URLs hit, sizes, schemas' },
    success_criteria: { type: 'string', description: 'what result confirms vs refutes the hypothesis' },
    notes: { type: 'string' },
  },
}
const scope = await agent(`You are scoping a research project before any real work begins.
${leadBrief}
${HW}
Tasks:
1. mkdir -p ${RUN_DIR} and write your outputs there as you go (plan.md).
2. VERIFY data access for real: hit the APIs/download a small sample of each dataset into ${RUN_DIR}/data/sample/. If a dataset is unavailable, find a substitute or set viable=false.
3. Write a preregistration-style analysis plan: primary endpoint, statistical tests, controls/confounds to handle, exclusion rules, and explicit success/refutation criteria for the hypothesis. Do a quick literature check (load WebSearch via ToolSearch, max 4 searches) to make sure the exact study hasn't been published in the last 2 years; note close prior art and how this differs.
4. Save the plan to ${RUN_DIR}/plan.md, then return structured output.`,
  { label: `scope:${lead.id}`, phase: 'Scope', schema: SCOPE_SCHEMA })

if (!scope || !scope.viable) {
  return { status: 'aborted-at-scope', scope }
}

phase('Build')
const build = await agent(`You are implementing the analysis pipeline for a scoped research project. Read ${RUN_DIR}/plan.md first — it is the authoritative analysis plan.
${leadBrief}
${HW}
Tasks:
1. Create ${RUN_DIR}/code/ with a clean, runnable pipeline (python scripts or a Makefile-driven flow — NOT a notebook): data acquisition, processing, analysis, figure generation. Config at top; deterministic seeds.
2. Smoke-test end-to-end on a small sample (the sample in ${RUN_DIR}/data/sample/ or a fresh small slice). Fix until it runs clean.
3. Write ${RUN_DIR}/code/README.md: how to run the full pipeline, expected runtime, disk needs.
Return a short report: what was built, smoke-test result, expected full-run cost. If the smoke test reveals the hypothesis is untestable as planned, say so explicitly and stop.`,
  { label: `build:${lead.id}`, phase: 'Build' })

phase('Execute')
const results = await agent(`You are executing the full analysis for a research project. Read ${RUN_DIR}/plan.md and ${RUN_DIR}/code/README.md, then run the full pipeline per its README.
${HW}
Build notes from the previous stage: ${String(build).slice(0, 3000)}
Tasks:
1. Run the full pipeline. Monitor for failures; fix minor issues in place (record every deviation from plan.md in ${RUN_DIR}/deviations.md).
2. Save results to ${RUN_DIR}/results/ (tables as CSV/JSON, figures as PNG/SVG). Every figure needs axes, units, and a caption file.
3. Run the statistical tests named in plan.md, including any correction for multiple comparisons it specifies.
Return: the headline numbers, whether the pre-registered success criteria were met, and paths to key results files. Report honestly — a null result is a valid result.`,
  { label: `execute:${lead.id}`, phase: 'Execute' })

phase('Review')
const REVIEW_SCHEMA = {
  type: 'object', required: ['verdict','issues','fatal'],
  properties: {
    verdict: { type: 'string', enum: ['sound', 'fixable-issues', 'refuted'] },
    issues: { type: 'array', items: { type: 'string' } },
    fatal: { type: 'boolean' },
  },
}
const lenses = [
  'methodology: confounds, selection bias, data leakage, train/test contamination, inappropriate statistical tests, multiple-comparisons problems, p-hacking degrees of freedom',
  'data-and-code: re-run key computations yourself from ${RUN_DIR}/code, check for bugs that flip the result, verify figures match the underlying numbers, check data quality/coverage assumptions',
]
const reviews = await parallel(lenses.map((lens, i) => () =>
  agent(`You are an adversarial reviewer. Your job is to REFUTE this study if you can. Default to skepticism.
Study dir: ${RUN_DIR} (read plan.md, deviations.md, results/, code/). Executor's summary: ${String(results).slice(0, 3000)}
Your lens: ${lens.replace('${RUN_DIR}', RUN_DIR)}
Actively look for problems — run code, recompute numbers, poke the data. fatal=true only if the headline claim does not survive. List concrete issues with file/line or number references.`,
    { label: `review-${i + 1}:${lead.id}`, phase: 'Review', schema: REVIEW_SCHEMA })
))
const liveReviews = reviews.filter(Boolean)
const refuted = liveReviews.filter(r => r.fatal).length >= 1

phase('Write-up')
const writeup = await agent(`You are writing up a completed research project. Study dir: ${RUN_DIR} (read plan.md, results/, deviations.md).
Executor summary: ${String(results).slice(0, 3000)}
Adversarial review verdicts: ${JSON.stringify(liveReviews)}
${refuted ? 'A reviewer found a FATAL flaw. The write-up must lead with this: describe what was attempted, what broke, and what a fixed study would look like. Do not spin a refuted result as a finding.' : 'Reviews passed (address any non-fatal issues in a limitations section).'}
Write ${RUN_DIR}/report.md: abstract, background + the gap (cite the literature from the lead), methods (from plan.md), results with figures (relative image links into results/), limitations (including every reviewer issue and how it was addressed or why it stands), conclusion, and next steps. Honest, publication-draft tone. Return the abstract and the report path.`,
  { label: `writeup:${lead.id}`, phase: 'Write-up' })

return { status: refuted ? 'completed-refuted' : 'completed', run_dir: RUN_DIR, scope, results: String(results).slice(0, 2000), reviews: liveReviews, writeup: String(writeup).slice(0, 2000) }
