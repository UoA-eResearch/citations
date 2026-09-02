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

// Operational notes for the build/execute stages (kept out of the scope prompt so a resumed run keeps its cached scope).
const ENV = `OPERATIONAL NOTES (read carefully):
- GPU: the A100 is normally occupied (~80GB) by the user's vLLM server, which runs in the docker container named \`vllm\`. The user has AUTHORIZED stopping that container to free the GPU. Protocol: run \`docker stop vllm\` immediately before a GPU-heavy stage, confirm with \`nvidia-smi\` that memory is free, do the GPU work, then \`docker start vllm\` the moment GPU work is done. ALWAYS restart it — including on failure or interruption (wrap GPU stages in a shell trap / python try-finally that runs \`docker start vllm\`). Do not stop it for CPU-only work. Keep the stopped window as short as practical (e.g. in the Build stage, smoke-test on CPU and stop the container only briefly once to verify the GPU code path). The venv has CUDA-enabled jax (jax[cuda12]); CPU fallback (jax cpu backend, dynesty/nautilus with multiprocessing over 32 cores) remains available if the GPU is unexpectedly unavailable.
- Long jobs: the Bash tool times out at 10 minutes per call. Launch anything longer with nohup in the background, log to ${RUN_DIR}/logs/, and poll with short sleep loops. Never block a single call on a multi-hour job.
- Wall-clock budget for the FULL pipeline run: about 12 hours. If the preregistered scale (e.g. 200 mock catalogs, nested-sampling live points) does not fit, scale it down explicitly (e.g. 100 mocks, cheaper point-estimate statistics for the mock arm) and record every such deviation in ${RUN_DIR}/deviations.md with the reason.
- Existing state: ${RUN_DIR} may already contain plan.md, a venv/, data/sample/, and a partially written code/ tree from an earlier interrupted session. Read what is there before writing; keep what is sound, finish or replace what is not. Do not start from scratch if the existing code is usable.`

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
const BUILD_SCHEMA = {
  type: 'object', required: ['ok','summary','smoke_test_passed','full_run_estimate','blockers'],
  properties: {
    ok: { type: 'boolean', description: 'true only if the pipeline exists end-to-end, the smoke test passed, and code/README.md documents how to run the full pipeline' },
    summary: { type: 'string', description: 'what was built, module by module' },
    smoke_test_passed: { type: 'boolean' },
    full_run_estimate: { type: 'string', description: 'expected wall time, CPU/GPU needs, disk for the full run' },
    blockers: { type: 'string', description: 'empty if none; otherwise what stops a full run' },
  },
}
const build = await agent(`You are implementing the analysis pipeline for a scoped research project. Read ${RUN_DIR}/plan.md first — it is the authoritative analysis plan.
${leadBrief}
${HW}
${ENV}
Tasks:
1. Create/complete ${RUN_DIR}/code/ as a clean, runnable pipeline (python scripts driven by a Makefile or a single run_all.py with stage selection — NOT a notebook): data acquisition, processing, analysis, figure generation. Config at top; deterministic seeds. Every stage must be resumable (skip if its outputs exist).
2. Smoke-test END-TO-END in a fast mode (small sample / few live points / few mocks) using ${RUN_DIR}/data/sample/ or a fresh small slice. Fix until it runs clean. The smoke test must exercise every stage, including figure generation.
3. Write ${RUN_DIR}/code/README.md: exact commands for the full pipeline, expected runtime per stage on this CPU-only machine, disk needs, and how to resume after interruption.
Set ok=true ONLY if all three are done and the smoke test passed. If the hypothesis turns out untestable as planned, set ok=false and explain in blockers.`,
  { label: `build:${lead.id}`, phase: 'Build', schema: BUILD_SCHEMA })

if (!build || !build.ok) {
  return { status: 'aborted-at-build', scope, build }
}

phase('Execute')
const EXEC_SCHEMA = {
  type: 'object', required: ['ok','headline','criteria_verdict','results_paths','deviations','notes'],
  properties: {
    ok: { type: 'boolean', description: 'true only if the full pipeline ran to completion and results/ contains the preregistered primary endpoints' },
    headline: { type: 'string', description: 'the headline numbers for every preregistered primary endpoint' },
    criteria_verdict: { type: 'string', enum: ['confirmed','refuted','indeterminate','not-run'], description: 'per plan.md success criteria' },
    results_paths: { type: 'array', items: { type: 'string' } },
    deviations: { type: 'string', description: 'every deviation from plan.md (also recorded in deviations.md)' },
    notes: { type: 'string' },
  },
}
const results = await agent(`You are executing the full analysis for a research project. Read ${RUN_DIR}/plan.md and ${RUN_DIR}/code/README.md, then run the full pipeline per its README.
${HW}
${ENV}
Build notes from the previous stage: ${build.summary}
Full-run estimate from the builder: ${build.full_run_estimate}
Tasks:
1. Run the full pipeline (background + polling for long stages). Monitor for failures; fix minor issues in place (record every deviation from plan.md in ${RUN_DIR}/deviations.md).
2. Save results to ${RUN_DIR}/results/ (tables as CSV/JSON, figures as PNG/SVG). Every figure needs axes, units, and a caption file.
3. Run the statistical tests named in plan.md, including any correction for multiple comparisons it specifies, and apply plan.md's preregistered success/refutation criteria.
Return the headline numbers, the verdict under the preregistered criteria, and paths to key results files. Report honestly — a null or indeterminate result is a valid result. Set ok=false if the pipeline did not complete.`,
  { label: `execute:${lead.id}`, phase: 'Execute', schema: EXEC_SCHEMA })

if (!results || !results.ok) {
  return { status: 'aborted-at-execute', scope, build, results }
}

phase('Review')
const REVIEW_SCHEMA = {
  type: 'object', required: ['verdict','issues','fatal'],
  properties: {
    verdict: { type: 'string', enum: ['sound', 'fixable-issues', 'refuted'] },
    issues: { type: 'array', items: { type: 'string' } },
    fatal: { type: 'boolean' },
  },
}
const execSummary = `Headline: ${results.headline}\nVerdict under preregistered criteria: ${results.criteria_verdict}\nDeviations: ${results.deviations}\nNotes: ${results.notes}\nKey files: ${(results.results_paths || []).join(', ')}`
const lenses = [
  'methodology: confounds, selection bias, data leakage, inappropriate statistical tests, multiple-comparisons problems, p-hacking degrees of freedom, whether the preregistered criteria in plan.md were applied as written (not reinterpreted after seeing the data)',
  `data-and-code: re-run key computations yourself from ${RUN_DIR}/code, check for bugs that flip the result, verify figures match the underlying numbers, check data quality/coverage assumptions and the selection-function treatment`,
]
const reviews = await parallel(lenses.map((lens, i) => () =>
  agent(`You are an adversarial reviewer. Your job is to REFUTE this study if you can. Default to skepticism.
Study dir: ${RUN_DIR} (read plan.md, deviations.md, results/, code/). Executor's summary:
${execSummary}
Your lens: ${lens}
Actively look for problems — run code, recompute numbers, poke the data. fatal=true only if the headline claim does not survive. List concrete issues with file/line or number references.`,
    { label: `review-${i + 1}:${lead.id}`, phase: 'Review', schema: REVIEW_SCHEMA })
))
const liveReviews = reviews.filter(Boolean)
const refuted = liveReviews.filter(r => r.fatal).length >= 1

phase('Write-up')
const writeup = await agent(`You are writing up a completed research project. Study dir: ${RUN_DIR} (read plan.md, results/, deviations.md).
Executor summary:
${execSummary}
Adversarial review verdicts: ${JSON.stringify(liveReviews)}
${refuted ? 'A reviewer found a FATAL flaw. The write-up must lead with this: describe what was attempted, what broke, and what a fixed study would look like. Do not spin a refuted result as a finding.' : 'Reviews passed (address any non-fatal issues in a limitations section).'}
Write ${RUN_DIR}/report.md: abstract, background + the gap (cite the literature from the lead and plan.md section 9), methods (from plan.md), results with figures (relative image links into results/), limitations (including every reviewer issue and how it was addressed or why it stands), conclusion, and next steps. Honest, publication-draft tone. Return the abstract and the report path.`,
  { label: `writeup:${lead.id}`, phase: 'Write-up' })

return { status: refuted ? 'completed-refuted' : 'completed', run_dir: RUN_DIR, scope, build, results, reviews: liveReviews, writeup: String(writeup).slice(0, 2000) }
