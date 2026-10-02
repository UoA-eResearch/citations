export const meta = {
  name: 'research-lead-scout-round2',
  description: 'Fan out 8 domain scouts over the unscouted research areas, then a critic calibrates and dedups the new leads',
  phases: [
    { title: 'Scout', detail: '8 domain scouts, web research only, 3-4 leads each in the leads.json schema' },
    { title: 'Critique', detail: 'one critic: novelty spot-checks, feasibility, score calibration, dedup' },
  ],
}

const DOMAINS = [
  { slug: 'ecology-biodiversity', brief: 'Ecology and biodiversity informatics (GBIF, eBird, iNaturalist, GLOBI, IUCN, TRY, BioTIME): e.g. sampling-effort-corrected range-shift estimation, species-distribution-model benchmark leakage and spatial-block validation, whether published climate-driven range shifts survive observer-effort nulls.' },
  { slug: 'seismology-geophysics', brief: 'Seismology and solid-earth geophysics (EarthScope/IRIS open waveforms, USGS/ISC catalogs, STEAD/INSTANCE datasets): e.g. out-of-region generalization of deep-learning phase pickers, aftershock-forecast benchmark integrity, whether ML-built catalogs change b-value or foreshock conclusions.' },
  { slug: 'formal-math', brief: 'Formal mathematics and proof assistants (Lean 4/mathlib, Isabelle AFP, Coq): e.g. autoformalization benchmark contamination, mining mathlib dependency graphs (lemma redundancy, proof repair), machine-checking published lemmas, prover benchmark validity.' },
  { slug: 'ai-evaluation-science', brief: 'AI evaluation science beyond pretraining: validity of agentic benchmarks (SWE-bench / OSWorld / tau-bench task leakage, reward hacking, solvability audits), LLM-as-judge calibration under adversarial framing, interpretability replication (e.g. sparse-autoencoder feature stability across seeds).' },
  { slug: 'cheminformatics-drug-discovery', brief: 'Cheminformatics and computational drug discovery (ChEMBL, PDBBind, BindingDB, USPTO reactions, PoseBusters, Polaris): e.g. activity-cliff and scaffold-split leakage, docking-score benchmark validity, retrosynthesis evaluation artifacts. (Existing chem-materials leads cover only MLIPs/materials DFT.)' },
  { slug: 'computational-reproducibility', brief: 'Computational reproducibility at execution scale: re-running published notebooks, Snakemake/Nextflow workflows, R replication packages, Dataverse/CodeOcean capsules, to measure how many execute and reproduce their reported numbers, and why they fail.' },
  { slug: 'legal-digital-humanities', brief: 'Legal, regulatory and digital-humanities text corpora (Caselaw Access Project, CourtListener, EUR-Lex, Federal Register, HathiTrust, Project Gutenberg): e.g. citation-network and doctrinal-drift analyses, precedent decay, LLM-era changes in filing or regulatory language.' },
  { slug: 'quantum-simulation', brief: 'Classical simulation of quantum-advantage claims and quantum-algorithm benchmarks (tensor-network, stabilizer, Pauli-path, belief-propagation methods on one A100): well-defined, adversarial, compute-only programs; also reproducibility of published quantum-error-mitigation or variational results on open simulators.' },
]

const LEAD = {
  type: 'object',
  properties: {
    id: { type: 'string', description: 'kebab-case, prefixed with the domain slug' },
    title: { type: 'string' },
    domain: { type: 'string' },
    hypothesis: { type: 'string', description: 'one falsifiable, quantitative hypothesis' },
    gap: { type: 'string', description: 'why this is open as of the given date, naming the closest prior work found' },
    value_score: { type: 'number' },
    cost_score: { type: 'number' },
    value_rationale: { type: 'string' },
    cost_rationale: { type: 'string' },
    est_wall_time: { type: 'string' },
    est_data_gb: { type: 'number' },
    feasibility: { type: 'string', enum: ['local', 'stretch', 'out_of_reach'] },
    requirements_if_out_of_reach: { type: 'string' },
    datasets: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, url: { type: 'string' }, access: { type: 'string' }, size: { type: 'string' } }, required: ['name', 'url', 'access', 'size'] } },
    lit_for: { type: 'array', items: { type: 'string' } },
    lit_against: { type: 'array', items: { type: 'string' }, description: 'closest prior work / reasons it may already be answered or may fail' },
    method: { type: 'string' },
    plan: { type: 'array', items: { type: 'string' } },
    risks: { type: 'string' },
    plain_summary: { type: 'string', description: '1-3 sentences for non-experts: what question, why it matters' },
  },
  required: ['id', 'title', 'domain', 'hypothesis', 'gap', 'value_score', 'cost_score', 'value_rationale', 'cost_rationale', 'est_wall_time', 'est_data_gb', 'feasibility', 'requirements_if_out_of_reach', 'datasets', 'lit_for', 'lit_against', 'method', 'plan', 'risks', 'plain_summary'],
}
const SCOUT_OUT = { type: 'object', properties: { leads: { type: 'array', items: LEAD }, searches_run: { type: 'number' }, notes: { type: 'string' } }, required: ['leads', 'searches_run'] }

const RUBRIC = 'value_score: 2-3 minor replication | 4-5 solid incremental | 6-7 fills an actively discussed gap | 8-10 major open question / broad impact. cost_score: 1-2 hours-to-a-day CPU-only | 3-4 days, some GPU, <50GB | 5-6 one-two weeks, 50-300GB | 7-8 weeks, near hardware limits | 9-10 exceeds this machine (then feasibility out_of_reach and fill requirements_if_out_of_reach).'

const existing = args.existing.map(e => `- ${e.id}: ${e.title}`).join('\n')

phase('Scout')
const scouted = await parallel(DOMAINS.map(d => () => agent(
`You are a research-lead scout for an autonomous in-silico research lab. Today is ${args.date}. Domain: ${d.slug}.
Brief: ${d.brief}

Find 3-4 NEW research leads in this domain that one machine can execute end to end. Machine: ${args.hardware}. Only open data and open-source tools (no logins, paywalls, or data-use agreements that need human approval). The lab preregisters each study, so each lead needs one sharp, falsifiable, quantitative hypothesis.

Required process:
1. Use web search (and fetch where useful) to find what is actively debated and where the gaps are; prefer 2024-2026 work.
2. For EACH candidate lead, search specifically for prior work that may already answer it (arXiv, journals, preprints, 2025-2026 especially). Drop candidates that are already answered. Record the closest prior work in lit_against and say in gap what remains open.
3. Verify each dataset URL exists and is openly downloadable; give a realistic size.
4. Mix lead styles: at most half may be "audit / re-measure an existing claim"; include constructive leads (new method, new measurement, new dataset built from open sources, prospective test).

Scoring rubric: ${RUBRIC}
Score honestly; most leads are 5-7 value. Cost must reflect this machine.
plain_summary: 1-3 sentences a non-expert can follow.
plan: 5-8 concrete steps a subagent could execute.

Do NOT duplicate these existing leads:
${existing}

Constraints on you: research only. Do not download large files, run models, or use the GPU (it is busy with another study).
Return the leads in the schema; set searches_run to the number of searches you made.`,
  { label: `scout:${d.slug}`, phase: 'Scout', schema: SCOUT_OUT })))

const leads = scouted.filter(Boolean).flatMap(r => r.leads || [])
const failed = DOMAINS.filter((d, i) => !scouted[i]).map(d => d.slug)
if (failed.length) log(`scouts with no result: ${failed.join(', ')}`)
log(`${leads.length} candidate leads from ${scouted.filter(Boolean).length} scouts`)

const CRITIQUE = {
  type: 'object',
  properties: {
    assessments: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      keep: { type: 'boolean' },
      value_score: { type: 'number' },
      cost_score: { type: 'number' },
      feasibility: { type: 'string', enum: ['local', 'stretch', 'out_of_reach'] },
      critic_note: { type: 'string', description: 'what the critic checked and why scores changed (or not)' },
      duplicate_of: { type: 'string', description: 'id of an existing or new lead it duplicates, or empty' },
    }, required: ['id', 'keep', 'value_score', 'cost_score', 'feasibility', 'critic_note', 'duplicate_of'] } },
    overall: { type: 'string', description: 'assessment of the batch: coverage, style mix, calibration' },
    unscouted_angles: { type: 'array', items: { type: 'string' } },
  },
  required: ['assessments', 'overall', 'unscouted_angles'],
}

phase('Critique')
const critique = await agent(
`You are the completeness and calibration critic for a batch of new research leads. Today is ${args.date}. Machine: ${args.hardware}.
Rubric: ${RUBRIC}

For EVERY lead below:
- Spot-check novelty with your own web searches (at least one targeted search per lead for 2025-2026 work that may already answer it). If answered, keep=false and say by what.
- Check feasibility on this machine with open data only (no logins or human-approved data agreements); fix feasibility and cost_score if unrealistic.
- Calibrate value_score against the rubric and against each other; scouts tend to over-score.
- Flag duplicates of each other or of these existing leads:
${existing}
Write a concrete critic_note for each (what you checked, what changed).

Then give an overall assessment of the batch and list angles still unscouted.

New leads (JSON):
${JSON.stringify(leads)}`,
  { label: 'critic', phase: 'Critique', schema: CRITIQUE, effort: 'high' })

return { leads, critique, failed_scouts: failed }