# Deviations from the self-audit protocol (paper/audit_plan.md, commit f424e29)

## A1. Measure A: classifying same-commit cases (2026-10-06 01:32 NZDT)

Under the strict criterion (plan committed strictly before the first output), 15 of 19 runs pass. In the other four,
the plan and some `results/` file were added in the same commit. We inspected those files:

- **speed-limit** (e74eaea): pre-period tables, the pre-period MDE, a placebo space, and the SHA-256 of the sealed
  post-period file.
- **wastewater-gap** (311bd7e): the catchment list and SHA-256 sums.
- **FluSight** (1f0956b): a data-coverage table.
- **GWTC-4** (258616c): the plan arrived in the same commit as "full-run results through E1-E5".

The first three contain only pre-outcome material. GWTC-4 does not, so its preregistration cannot be verified from the
public record. The paper reports both the strict count (15 of 19) and the classified count (18 of 19, with GWTC-4
failing). The GWTC-4 report receives a correction note.

## A2. Measure D: chance-match check and significant-digit stratification (2026-10-06 01:32 NZDT)

Matching each report's numbers against **other** studies' results "traced" 62% of them on average, against 95% for the
study's own results. The planned traced fraction is therefore an upper bound that is badly inflated by chance matches.

Two additions are reported alongside it (`audit_numbers.py --null` and `--sig`):

- the cross-run chance rate;
- own and chance rates by number of significant digits, with a chance-corrected rate (own − chance) / (1 − chance).

## A3. Measure E: two parser artifacts (2026-10-06 01:32 NZDT)

Two DOIs failed only because of how they were parsed:

- one carried a "v1" version suffix;
- one was cut off at a parenthesis.

Both resolve in full (`10.64898/2025.12.26.696646` and `10.1016/s0967-070x(97)00007-3`).

## A4. Measure F: effort cannot be measured reliably (2026-10-06 01:32 NZDT)

The protocol planned to measure effort from git. Commit times reflect when work was committed, not when it was done.
Several studies were committed in bursts lasting minutes, and some reports were last touched by batch edits.

As an alternative we derived effort from the session transcripts (`audit_effort.py`). Tool calls rarely name the run
directory, and studies 2-8 ran in parallel through the executor workflow, so these numbers are also unreliable.

The paper reports only the calendar span and the degree of parallelism, and states why per-study effort is not given.

## A5. An added coder: protocol-feature inventory (2026-10-06 01:32 NZDT)

Quick text searches showed that safeguards varied between plans:

- sealing appears in 2 of 19 plans;
- a power or MDE statement appears in 3 of 19.

A third coder (Opus model, the same instructions apply) therefore inventories, for each plan:

- disclosure;
- decision rule;
- power;
- outcome blinding;
- validation;
- multiplicity;
- independent review;
- open data;
- the type of primary analysis.

The output is `audit/inventory/plan_inventory.csv`. This inventory was not in the protocol.
