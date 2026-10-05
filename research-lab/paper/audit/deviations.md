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

## A6. Inventory adjudication: outcome blinding (2026-10-06 01:39 NZDT)

**Why the codebook needed fixing.** It mixed two ideas under "outcome_blinding": keeping outcomes away from the
analyst, and how outcomes are verified.

**What was recoded.** In `audit/inventory/plan_inventory_adjudicated.csv`:

- **humid-heat:** prospective → none. Its outcomes are computed by the agent's own pipeline, so they are not external
  data that did not yet exist.
- **formal-math:** formal → none for blinding. Machine-checked verification is recorded in a separate column,
  `verification_formal`.

**What remains.** Outcome blinding now covers sealed (speed-limit, quantum) and externally prospective (CRL). The
coder's raw file is unchanged.

## A7. Adjudication rules and review issue counts (2026-10-06 01:46 NZDT)

**Basis.** Adjudication starts from coder A's file, because it identified entries more conservatively. B's extra
`D27c-review` is folded into D27c, as A did. Three rules were applied to the 27 disagreements, and each decision and
its reason is logged in `audit/adjudication.csv`:

1. **Category follows the cause.** A data problem that forced a change of specification is coded C2.
2. **Verdict relevance takes the cautious side.** When coders split, yes beats unclear, and unclear beats no.
3. **Timing takes "unclear"** when one coder said unclear.

**Review issue counts.** Exact agreement on the count of review issues was 24%, and per-category agreement was
29-100%. These counts are not adjudicated. The paper reports both coders' totals.

## A8. Measure D: matcher bug found by coder B (2026-10-06 01:55 NZDT)

**The bug.** While classifying untraced numbers, coder B found two faults in the number matcher:

- it split numbers with thousands separators in source files ("1,184,764") into separate pieces;
- it did not scrub "§4.3"-style section references from reports.

**The fix and its effect.** Both are fixed in `audit_numbers.py`, and measure D was rerun:

| Measure | Before | After |
|---|---|---|
| Substantive numbers | 2,272 | 2,256 |
| Share that trace | 95.8% | 95.5% |
| Cross-run chance rate | 62.0% | 61.6% |
| Corrected rate, 3 significant figures | 94% | 92% |

**The classified sample.** The 85-number sample the coders classified was drawn under the old matcher. It is kept
unchanged as `D_sample_untraced.csv` (with a copy in `D_sample_untraced_v1.csv`), and its classification is reported
as such. Some of those numbers now trace.

## A9. A deviation entry created by the audit (2026-10-06 02:12 NZDT)

**The entry.** The rounding correction added to the MCF deviation log at 02:02 is a result of this audit, not one of
its subjects. Coder A coded it after the fact, as U1 / C8 / T4.

**Treatment.** It is excluded from the deviation counts and the agreement statistics, which cover the entries that
existed when coding began. It is reported in the paper as an audit finding.

## A10. Measure D redesigned after review (2026-10-06 02:28 NZDT)

**What the reviewer found (M7).** Matching values against other studies' files is not a size-matched control.

**A second control.** We added a perturbation null in `audit_numbers.py --perturb`:

- each printed number is shifted by 3-7 units of its last digit;
- the shifted value is tested against the study's own sources;
- the test is reported for all sources and for `results/` only.

**What it showed.** Shifted values still "trace" 75% of the time against `results/` alone, and 67% at three
significant figures. Results files hold many values close to any reported one. Automated value matching therefore
cannot establish that a number traces, and it cannot detect a wrong number that coincides with some value.

**Direct verification instead.** Both coders now verify a seeded random sample of 119 substantive numbers, 7 per
report (`audit/D_verify_sample.csv`). For each one they locate the specific source (file and cell, or a derivation)
and judge whether the printed value is consistent with it. This sample replaces automated tracing as the primary
measure of whether report numbers are accurate. The automated rates are reported only to show that the method fails.

## A11. Changes after the confirmation pass (2026-10-06 03:42 NZDT)

**Push lags.** The confirmation pass (`review/confirmation.md`) showed that the push lags in A_push_lag.csv were
wrong. On 2026-10-01 a `filter-branch` rewrite changed the IDs of five commits, and lags had been matched by the
current IDs. Two changes follow:

- `audit_git.py --rewrite` now writes `A_rewrite_map.csv`, which pairs the original and current IDs. Trees and
  timestamps are identical, and author identities are not written.
- `make_numbers.py` now matches each push through the original ID. All 19 plans were pushed within 4 seconds.

**Untraced sample.** `D_sample_untraced.csv` was overwritten again by the `--perturb` rerun, so A8's statement that
it was "kept unchanged" stopped being true. It is restored to the classified 85-number sample, which is the same as
`D_sample_untraced_v1.csv`. `audit_numbers.py` now writes any regenerated sample to
`D_sample_untraced_latest.csv`, and `make_numbers.py` reads the v1 file.

**Verification sample.** `code/sample_verify.py` regenerates `D_verify_sample.csv`. It uses seed 20261006+7 and the
reports at commit 90930ab, the state they were in when the sample was drawn, and `--check` confirms an exact
match.

**Bibliography check.** `audit_refs.py --bib` writes `E_bib_refs.csv`: 33 of 33 arXiv identifiers and 6 of 6 DOIs
resolve.

**Disagreement count.** A7's count of 27 entries with any coder disagreement covers all 19 studies. For the
135 entries in reported studies the count is 26.
