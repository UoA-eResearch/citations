# Study protocol and quality gates

How every deep dive in this lab is run. The core protocol has been used since the first deep dive. Gates G1–G7 were
adopted on 2026-10-25 after reviewing SciTrue (Tan, Li & Gahegan, EACL 2026 demo; and the SciTrue team's NTCIR-19
SciClaimEval paper, arXiv 2609.00654). Their lessons on packaging leaks, silent fallbacks, error audits and
claim-level attribution matched failures this lab had already had.

The gates apply to every lead started from 2026-10-25. For drafts already queued for review, G5 and G6 run as a
pre-review gate before the draft's Fable slot. The helpers are in `tools/`; they use only the standard library, so
run them with any Python as `python3 -I tools/<name>.py`.

## Core protocol

1. **Lead check.** Novelty and feasibility, with skips recorded in README.md. The lead's own factual claims (data
   sizes, dataset keys, what a paper or code does) are verified under G6 before the plan is written.
2. **Preregistration (`plan.md`)**, committed before the data that decide the hypotheses are looked at.
   - It states the hypotheses, with Supported / Refuted / Inconclusive rules, the data, the primary statistic, the
     secondaries and the limits stated in advance.
   - It records what had been seen before it was written.
   - **New:** a leakage audit section (G1).
3. **Deviations (`deviations.md`)**, as numbered D-entries with an NZ timestamp, each saying whether it came before
   or after the results it could affect. Post-result changes are labelled in the report, the first-version outputs
   are kept, and post hoc analyses are labelled as such.
4. **Code before results.** Analysis code is committed before it is run on the deciding data. Pilots are separate
   from the main data, and frozen choices (ladders, thresholds) are logged before the main run.
5. **Report (`report.md`).** The verdict comes first, with an "In plain terms" section, the results tables, "What
   this does and does not show", process and deviations, and how to reproduce it. Every lead also gets a
   `plain_summary` and a one-word `verdict_tag`.
6. **Independent review.** A fresh Fable reviewer works from `review/prompt.md`, which includes the standard gate
   checks (below). Then come fixes as D-entries, a confirmation pass by the same reviewer, and publication. At most
   one Fable run every 5 hours; the queue is in `REVIEW_QUEUE.md`.
7. **Hygiene.**
   - Commits use explicit paths only, and secrets are grepped for before every commit.
   - Quoted paper text, reviewer evidence dumps and quotes stay in `data/`, outside git.
   - Python on downloaded data runs with `-I`.
   - Third-party code runs only in Docker without credentials.

## G1 — Leakage and packaging audit (in `plan.md`, re-checked before analysis)

A leak lets the answer reach the pipeline through how the data are packaged rather than through their content. In
SciClaimEval the true label was always listed first, and a pipeline using row order scored 99.4.

The plan has a **Leakage audit** section that:
- **lists every field correlated with the label or outcome**, such as row order, IDs and their sequence, file names,
  timestamps, split membership, provenance and duplicate records across train and test, and says how the pipeline is
  kept blind to each;
- **keeps related units in the same split**, including pairs, groups, entities, near-duplicates and records sharing
  provenance;
- **for every LLM- or agent-judged step** (blind labellers, matchers, judges, a reviewer's spot checks), states
  that:
  - inputs hide the system's own choice and the gold label;
  - candidate order is shuffled per item;
  - an **order-swap probe** is run: each item is judged in two orders, a judgement is kept only if both agree, and
    the agreement rate is reported;
- **names any leak found later as a D-entry**, with the affected numbers recomputed and the leaky variant reported
  only as such.

## G2 — Coverage accounting; no silent fallbacks (`tools/coverage.py`)

Every stage that can fail for a single unit records what happened to each unit: attempted, ok, fallback (value
replaced) or dropped (unit excluded), with reasons. The counts go to `results/tables/coverage.json`, and the report
carries a **Coverage** line (`python3 -I tools/coverage.py RUN_DIR` prints it).

A fallback that changes a value fails loudly unless the plan names it (`Coverage(..., allowed=(...))`). Code may not
turn a failure silently into a default value, NaN or zero that then enters a statistic.

## G3 — Plausibility gate (`results/plausibility.md`, before report.md is written)

1. **Expected ranges.** Each headline number is compared with its expected range: the pilot, a known case, earlier
   literature, a positive or negative control. Anything implausible is investigated before it is written up. (The
   quantum study's coarsest-pair bug and SciTrue's 99.4 were both caught this way.)
2. **Hand traces.** Three random units are traced end to end by hand (raw input → intermediate values → output) and
   the values recorded.
3. **Invariants.** Key invariants are asserted in code and listed: counts reconcile between stages, the setting used
   is the one the plan names (for example "the finest available"), no NaN reaches a primary statistic, and joins
   neither duplicate nor drop units.

## G4 — Error audit for validation metrics (`tools/error_audit.py`)

Before any precision, recall, accuracy or agreement figure for a classifier, matcher, labeller or LLM step is
reported, each error is inspected and classed as:
- an **artefact** of the validation set-up (the item could not be judged; for example the system's choice was not
  shown to the labeller);
- **gold-label noise** or ambiguity;
- a **genuine** error.

Report all three counts, the metric as measured, and the metric on the judgeable denominator, with its definition.
(Public Domain Day: 16 of the "false links" were artefacts, so precision was 0.81 as measured and 0.99 on judgeable
items.)

## G5 — Overclaim check (`tools/overclaim_check.py`, before queuing review and after every fix)

`overclaim_check.py RUN_DIR` lists every sentence of the title, standfirst, verdict block and "In plain terms" in
`review/overclaim_check.md`. Each sentence gets:
- its **backing**: the table or figure and the number;
- a **label**:
  - Supported;
  - Partially supported;
  - Overstated;
  - Not addressed;
  - Exploratory-labelled, when the sentence reports an exploratory result and says so.

Every Overstated, Not addressed or Partially supported sentence is rewritten in report.md. `--verify` must pass
before the draft is queued. A title or headline that mentions an exploratory or post hoc result labels it there.

## G6 — Attribution ledger (`tools/attribution.py`, `results/attribution_ledger.csv`)

Every literature claim and every external data fact we rely on gets a ledger row. That covers the lead (gap,
lit_for, lit_against, datasets), plan.md and report.md (prior work, the gap, what a dataset or its code does). Each
row records:
- the claim in our own words;
- where we use it;
- the source type and ID (DOI, OpenAlex W-id, arXiv id, URL, GBIF datasetKey, repo@commit);
- a **locator** (section, paragraph, table, field, file:line);
- for papers, the **role** of the cited text (main finding, background, limitation, method);
- **support** (supports / conditional / refutes / not addressed / not found);
- **conditions** (population, years, version, model organism);
- how and when it was checked.

**Check the version of record.** A preprint, a press summary or a search snippet can differ from the published paper, so a claim marked "not found" or "refutes" must be checked against the published abstract or text first. (AVF, 2026-10-25: the 0.05% that G6 called unsupported after reading only the arXiv preprint is in the published abstract of Brenguier et al. 2008.) Quotations go to `data/attribution_quotes/` (not git). `attribution.py check RUN_DIR` validates the rows, resolves
every DOI, OpenAlex, arXiv and GBIF id through public APIs, and fails if a claim marked refutes / not addressed / not
found is still used as support. `--show` prints each resolved identifier's title. Confirm that each one is the work the claim names, because an identifier that exists can still be the wrong paper. Free-text references can also be resolved with the OpenAlex MCP `resolve_references`
tool. (The SDM lead claimed a Czech Vegetation Database dataset that is not in SAGE's download; under G6 that is
caught at plan time.)

## G7 — Two independent blind labellers (`tools/agreement.py`)

Any validation sample labelled by an agent (or a person) is labelled by **two independent labellers**:
- fresh contexts and the same blind brief;
- independently shuffled candidate order, which doubles as G1's order-swap probe.

`agreement.py A.json B.json` reports percent agreement and Cohen's kappa and lists the disagreements. A third blind
pass adjudicates them, and `agreement.py --merge` builds the final labels.

Report the agreement, the kappa, the metrics on adjudicated labels, and each labeller's metrics as a sensitivity.
This doubles labelling cost, and sample sizes are not reduced to pay for it.

## Standard gate checks for reviewer briefs

Paste into every `review/prompt.md`:

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check 5 claims against
>   their sources, including the role and conditions.
> - **G7:** validation labels come from two blind labellers, with agreement reported.
>
> Report any gate that is missing or hollow as a finding.
