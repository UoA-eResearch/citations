# Studies awaiting independent review

Each of these is complete through a pre-review draft: preregistration, code, results, figures, report and a
reviewer brief in `runs/<id>/review/prompt.md`. None may be published to `leads.json`, `index.html`, the README or
the Golden Quadrant artifact until it has been through an independent adversarial review and a confirmation pass.

**Pacing (owner, 2026-10-21 18:30 NZDT): at most one Fable run per 5-hour period.** A run is a review or a
confirmation pass; never two at once. The next run may start only 5 hours after the previous run started (see the
log below). A reviewer cut off by a limit is resumed, not relaunched, and the resume counts as a run.

### Fable run log (start times, NZDT)

| start | study | run | outcome |
|---|---|---|---|
| 2026-10-21 ~17:52 | `frontier-eaa-accessibility-natural-experiment` | confirmation pass |
| 2026-10-21 ~18:01 | `movement-nz-ev-policy-discount-vs-ruc` | confirmation pass |
| 2026-10-21 23:06 | `energy-nz-embedded-solar-edb-demand` | review |
| 2026-10-22 04:07 | `energy-nz-embedded-solar-edb-demand` | confirmation pass |
| 2026-10-22 09:08 | `energy-nz-intermittent-curtailment-ledger` | review |
| 2026-10-22 14:13 | `energy-nz-intermittent-curtailment-ledger` | confirmation pass |
| 2026-10-22 19:13 | `legal-phantom-citations-judicial-opinions` | review |
| 2026-10-23 00:13 | `legal-phantom-citations-judicial-opinions` | confirmation pass (fresh agent; the original could not be resumed after the restart) |
| 2026-10-23 09:21 | `trust-corrected-record-machine-readable` | review |
| 2026-10-23 12:28 | `trust-corrected-record-machine-readable` | confirmation pass (owner relaxed the 5 h limit until the 16:00 quota reset) |
| 2026-10-23 12:28 | six reviews started in parallel (DSI, retraction risk, reef, estuary, kauri, ASR) | five stopped within ~2 min on the owner's advice to run sequentially; DSI ran on |
| 2026-10-23 ~12:50–14:15 | `trust-retraction-risk-frozen-forecast` | review, resumed after DSI finished |
| 2026-10-23 14:15 | `blue-pacific-reef-island-area-tide-corrected` | review, resumed |
| 2026-10-23 14:54 | `auckland-nz-2023-storms-estuary-mud-natural-experiment` | review, resumed |
| 2026-10-23 15:21 | `auckland-nz-kauri-dieback-multitemporal-lidar` | review, resumed |
| 2026-10-23 15:39 | `frontier-edge-asr-quantization-accent-parity` | review (H4 pending), resumed; last run under the exception |
| 2026-10-23 20:39 | `ancestral-dsi-origin-recoverability` | confirmation pass (original reviewer resumed) | publish -> PUBLISHED |
| 2026-10-24 01:39 | `blue-pacific-reef-island-area-tide-corrected` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-24 06:39 | `auckland-nz-2023-storms-estuary-mud-natural-experiment` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-24 11:39 | `auckland-nz-kauri-dieback-multitemporal-lidar` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-24 16:39 | `trust-retraction-risk-frozen-forecast` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-24 21:39 | `frontier-edge-asr-quantization-accent-parity` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-25 02:39 | `energy-nz-edb-quality-standard-ratchet` | review (fresh agent) | fix first |
| 2026-10-25 07:39 | `energy-nz-edb-quality-standard-ratchet` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-25 12:39 | `legal-digital-humanities-public-domain-day-renewal-did` | review (fresh agent) | fix first |
| 2026-10-25 17:39 | `legal-digital-humanities-public-domain-day-renewal-did` | confirmation pass (original reviewer resumed) | publish with edits -> PUBLISHED |
| 2026-10-25 22:40 | `auckland-nz-avf-dvv-hydrological-baseline` | review (fresh agent; pre-review gate G5+G6 done) | fix first |

**Pre-review gate (from 2026-10-25, METHODS.md):** before launching a draft's Fable review, run G5 (`tools/overclaim_check.py RUN --verify`) and G6 (`tools/attribution.py check RUN`) on it, fix what they find as a D-entry, and add the standard gate-check block to its `review/prompt.md`. New leads apply all of G1–G7.

**The owner's exception ended at 16:00 on 2026-10-23; the 1-per-5 h rule applies again. AVF review started 2026-10-25 22:40; next Fable run not before 03:40 on 2026-10-26.** Order: confirmations of DSI (b0149e2), reef (d7c2ace), estuary (3dd86a7), kauri (920bde5) and retraction risk (6d4c885), one per 5 h slot; then the ASR confirmation (fixes in f8a6d4d); then the EDB ratchet review (fb7efde), then the Public Domain Day review (26ff608), then the AVF dv/v review (35e9d7a).

| study | draft commit | verdicts in the draft | review status |
|---|---|---|---|
| `energy-outage-major-event-day-ratchet` | 2b5cb6b | H1 Inconclusive, H2 Refuted, H3 Refuted | **published** 2026-10-21 (Refuted on H3; H2 only with the 2015 baseline; H1 Inconclusive) |
| `ancestral-pacific-rainfall-gauge-circularity` | 0a73d80 | H1 Supported, H2 Refuted | **published** 2026-10-21 (verdicts unchanged after removing no-estimate stations and implausible gauge years) |
| `frontier-eaa-accessibility-natural-experiment` | 0c44d7a | H1 Supported, H2 Inconclusive, H3 not testable | **published** 2026-10-21 (Inconclusive on size; direction supported) |
| `energy-nz-gas-production-forecast-calibration` | b53e197 | H1 Supported, H2 Inconclusive, H3 Supported | **published** 2026-10-21 (Inconclusive: H1 passes only within Monte Carlo error; re-run on all editions) |
| `movement-nz-ev-policy-discount-vs-ruc` | 60012cc | H1 Inconclusive, H2 Inconclusive | **published** 2026-10-21 (Inconclusive) |
| `auckland-nz-jade-water-value-calibration` | 96c8a7c | H1 Supported, H2 Refuted | **published** 2026-10-21 (H1 Supported; H2 Refuted but unreachable; reinterpreted) |
| `energy-nz-embedded-solar-edb-demand` | 8f12116 | H1-H3 Inconclusive, H4 Supported by rule | **published** 2026-10-22 (Inconclusive: H4 passes its rule but is carried by two solar-farm networks) |
| `energy-nz-intermittent-curtailment-ledger` | f83332e | gate fails; H1 Refuted, H2 Supported by rule (noise-dominated; price-driven core 2.2%) | **published** 2026-10-22 (Inconclusive: gate fails; dispatched-down core is two wind farms) |
| `legal-phantom-citations-judicial-opinions` | 09c9990 | H1 Refuted by rule (0 of 300 sampled; upper bound 40; recall 0/4 judge incidents) - not robust; H2 not scorable; 45 court-flagged opinions | **published** 2026-10-23 (Inconclusive; review fix first, confirmation fix first on one item repaired in D10: 38 of 43 flags in the database, five unrecorded) |
| `trust-corrected-record-machine-readable` | 72af844 | H1 Refuted (2.4% unmarked in PMC XML), H2 Supported (sidecar 95.6%), H3 Refuted; peS2o 11.9% marked | **published** 2026-10-23 (Refuted at the source; peS2o downstream loss on the PMC overlap; review fix first, confirmation publish with edits) |
| `ancestral-dsi-origin-recoverability` | 87273a8 | H1 Inconclusive; H2 Refuted (19/300 test records determinable after D10; all arms 0% at 90% precision; 61% lab material) | **published** 2026-10-23 (Refuted on recovery; review publish with edits -> D10 b0149e2; confirmation publish, wording edits applied) |
| `trust-retraction-risk-frozen-forecast` | b314e0f | H1 Inconclusive; H2 Supported; H3 sealed | **published** 2026-10-24 (review fix first -> D3 6d4c885; confirmation publish with edits -> D4) |
| `blue-pacific-reef-island-area-tide-corrected` | ed14c61 | H1 not testable (guard -0.58, -1.17 to +0.14); H2 Supported (tide bias 0.88%/yr after the Theil-Sen fix) | **published** 2026-10-24 (Supported on H2; review fix first -> D7 d7c2ace incl. Theil-Sen bug; confirmation publish with edits -> D8) |
| `auckland-nz-2023-storms-estuary-mud-natural-experiment` | fb30a30 | H1/H2 Inconclusive; post hoc region-wide 2023 pulse | **published** 2026-10-24 (Inconclusive; review publish with edits -> D5 3dd86a7; confirmation publish with edits -> D6) |
| `auckland-nz-kauri-dieback-multitemporal-lidar` | e8a1bff | H1 Refuted, H2 Refuted after D1 | **published** 2026-10-24 (Refuted; review fix first -> D1 920bde5; confirmation publish with edits -> D2) |
| `energy-nz-edb-quality-standard-ratchet` | fb7efde | H1/H2 Inconclusive, H3 Supported | **published** 2026-10-25 (Inconclusive; review fix first -> D3; confirmation publish with edits -> D4) |
| `legal-digital-humanities-public-domain-day-renewal-did` | 26ff608 -> fixes, edits | Inconclusive (count RR 1.86 rests on 2024 cohort); exploratory any-edition RR 3.53 robust | PUBLISHED 2026-10-25 (review fix first; confirmation publish with edits) |
| `auckland-nz-avf-dvv-hydrological-baseline` | 35e9d7a -> fixes 4f87c4f | H1 Refuted (median -0.27, -0.35 to -0.15; 31 pairs); month-scale wander 0.074% | fixes done (4f87c4f); confirmation pass queued (review/confirm_prompt.md) |
| `legal-digital-humanities-precedent-erosion-before-overruling` |  e09bf03 | H1 not testable (D(+5) 0.27, -0.13 to 0.49); co-cite exclusion pre-share 0.31; D1 post-result 2019 coverage break; post hoc pre-2019: cited 55% MORE before overruling | queued; pre-review gate G5+G6 done 2026-10-25 (Feldman misattribution corrected; post hoc labelled in title) |
| `frontier-edge-asr-quantization-accent-parity` | (draft 2f02159 review) | H1 Inconclusive; H2 Supported by rule, not robust, not replicated; H3 Refuted; H4 not testable | **published** 2026-10-24 (Inconclusive; review fix first -> D4/D5 f8a6d4d; confirmation publish with edits -> D6) |
| `ecology-biodiversity-globi-temporal-link-holdout` |  bfe2f58 | H1 Refuted (taxonomic advantage over effort grows on future records: rho 1.68, 1.10-2.30) | queued; pre-review gate G5+G6 done 2026-10-25 (title narrowed to the taxonomic model; turnover table added) |
| `health-econ-procyclical-mortality-multiverse` |  ed2f4fc | H1 Inconclusive (47.4% of 2,304 specs negative-significant; joint test p<0.002; window and measure decide it); H2 Refuted (1.6% of 576 post-2010 drug specs) | queued; pre-review gate G5+G6 done 2026-10-25 (variance-share overclaim fixed) |
| `software-security-ai-code-supply-chain-exposure` |  3cfbf04 | H1 Refuted (npm R 1.03, P_w 22.3% < 30%; PyPI R 1.91); H2 Refuted (latency ratio 1.01); a third of releases flagged by Sep 2026 | queued; pre-review gate G5+G6 done 2026-10-25 (monorepo-qualified headline; prior work verified) |
| `llm-ml-science-scaling-fit-seed-uncertainty` |  f33d2b6 | H1 Inconclusive (W1 0.123 nats, 0.038-0.160); H2 Inconclusive (shrinkage 0.16); post hoc: two unstable 410M runs drive the width | queued; pre-review gate G5+G6 done 2026-10-25 |
| `metascience-retraction-citer-contagion` |  6ab7aea | H1 Inconclusive (prereg DiD +0.068, pre-trend); H2 not testable; H3 Refuted as prereg; post hoc not-yet-treated: no penalty (+0.003, -0.015 to +0.021) | queued; pre-review gate G5+G6 done 2026-10-25 (post hoc labelled in title; unfound citation replaced) |
| `experimental-math-oeis-conjecture-audit` |  a0127a5 | H1 Refuted (2 confirmed falsifications; 15 of 14,671 screened disagree with LODA) | queued; pre-review gate G5+G6 done 2026-10-25 (silent drops stated; citations corrected) |
| `health-econ-hub-vintage-rescore` |  53d30c6 | H1 Refuted (6.2% pairwise reversals); H2 Supported narrowly (2024-25 leader changes at h1/h2) | queued; pre-review gate G5+G6 done 2026-10-25 |
| `computational-reproducibility-notebook-noise-aware-verdicts` |  b67028b | H1 Inconclusive (20.6%, 10-37%); H2 Inconclusive (1.26, 1.09-1.58); D3 re-run after backend bug | queued; pre-review gate G5+G6 done 2026-10-25 |
| `formal-math-mathlib-proof-rot-flexible-linter` |  b62e129 | H1 Inconclusive (OR 1.48, 0.92-2.39); 6-month 1.67 (1.01-2.77); second pair 0.99 | queued; pre-review gate G5+G6 done 2026-10-25 |
| `quantum-simulation-convergence-false-assurance` |  b7b7321 | H1 Supported (PP 31%, 23-39%; BP 1.9%); H2 Supported pooled; random-patch-only PP 9.5% | queued; pre-review gate G5+G6 done 2026-10-25 (tracker case corrected) |

## Order to run them in

1. `energy-outage-major-event-day-ratchet` — resume the existing agent, since its finished checks are reusable and
   they already flagged snapshot gaps and 2015 zero days.
2. `energy-nz-gas-production-forecast-calibration` — a Supported headline, so it carries the most risk if wrong.
3. `ancestral-pacific-rainfall-gauge-circularity` — also Supported.
4. `frontier-eaa-accessibility-natural-experiment` — Supported, but the effect is modest and well hedged.
5. `auckland-nz-jade-water-value-calibration` — a Supported headline about a *named public agency's published
   model*, so it carries the most reputational risk of any draft here and the reviewer brief leads with the
   question the whole study stands on: whether JADE's HAY price and the HAY2201 settled price are comparable
   quantities at all. Run it early if the queue is reordered.
6. `movement-nz-ev-policy-discount-vs-ruc` — both verdicts Inconclusive, so the least exposed.

## After each review

Follow the lab's usual loop: apply the fixes, send the same agent a confirmation pass, then publish — update
`leads.json` (status, report_url, verdict_tag, verdict_note, headline, plain_summary), the embedded JSON in
`index.html`, a README row, rebuild the artifact with `build_artifact.py` and republish it, then update memory.

## Collecting in the background (not awaiting review)

- `movement-akl-crl-full-timetable-reliability` — the Auckland Transport GTFS-Realtime archive has been recording
  since 2026-10-20 via cron. It is deliberately **collection only**: preregistration follows once Auckland
  Transport announces the full-timetable date (committed to within six months of the 13 September 2026 opening).
  See that run's `COLLECTION.md`.

## Blocked on an account the lab cannot create

- `auckland-nz-hirds-out-of-sample-exceedance-audit` (value 6, cost 4) needs a free ESNZ DataHub account with a
  stated purpose, and possibly manual approval, to reach the HIRDS v4 design-depth tables. Everything else in it
  is open. If the owner creates that account, this is the next lead worth starting on merit.
