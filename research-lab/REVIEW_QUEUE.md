# Studies awaiting independent review

Each of these is complete through a pre-review draft: preregistration, code, results, figures, report and a
reviewer brief in `runs/<id>/review/prompt.md`. None may be published to `leads.json`, `index.html`, the README or
the Golden Quadrant artifact until it has been through an independent adversarial review and a confirmation pass.

**Pacing (owner, 2026-10-21 18:30 NZDT): at most one Fable run per 5-hour period.** A run is a review or a
confirmation pass; never two at once. The next run may start only 5 hours after the previous run started (see the
log below). A reviewer cut off by a limit is resumed, not relaunched, and the resume counts as a run.

### Fable run log (start times, NZDT)

| start | study | run |
|---|---|---|
| 2026-10-21 ~17:52 | `frontier-eaa-accessibility-natural-experiment` | confirmation pass |
| 2026-10-21 ~18:01 | `movement-nz-ev-policy-discount-vs-ruc` | confirmation pass |
| 2026-10-21 23:06 | `energy-nz-embedded-solar-edb-demand` | review |
| 2026-10-22 04:07 | `energy-nz-embedded-solar-edb-demand` | confirmation pass |
| 2026-10-22 09:08 | `energy-nz-intermittent-curtailment-ledger` | review |
| 2026-10-22 14:13 | `energy-nz-intermittent-curtailment-ledger` | confirmation pass |
| 2026-10-22 19:13 | `legal-phantom-citations-judicial-opinions` | review |
| 2026-10-23 00:13 | `legal-phantom-citations-judicial-opinions` | confirmation pass (fresh agent; the original could not be resumed after the restart) |
| 2026-10-23 09:21 | `trust-corrected-record-machine-readable` | review |
| 2026-10-23 12:28 | `trust-corrected-record-machine-readable` | confirmation pass | owner relaxed the 5 h limit until the 16:00 quota reset
| 2026-10-23 12:28 | `ancestral-dsi-origin-recoverability` | review | resumed ~12:50, finished: publish with edits; STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time
| 2026-10-23 12:28 | `trust-retraction-risk-frozen-forecast` | review | STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time
| 2026-10-23 12:28 | `blue-pacific-reef-island-area-tide-corrected` | review | STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time
| 2026-10-23 12:28 | `auckland-nz-2023-storms-estuary-mud-natural-experiment` | review | STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time
| 2026-10-23 12:28 | `auckland-nz-kauri-dieback-multitemporal-lidar` | review | STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time
| 2026-10-23 12:28 | `frontier-edge-asr-quantization-accent-parity` | review (H4 pending) | STOPPED within ~2 min (still reading) on the owner's advice to run sequentially; to be resumed one at a time

**Fable limit RELAXED by the owner until the 2026-10-23 16:00 quota reset, but SEQUENTIAL (owner: "7 at once would likely hit the 5h limit, I'd still recommend sequential").** Retraction-markers confirmation FINISHED (publish with edits; PUBLISHED). DSI review FINISHED (publish with edits). Retraction-risk review FINISHED (fix first). Running now: reef islands review (resumed). Then, one at a time until 16:00: reef islands, estuary mud, kauri, ASR (resume the stopped agents, which had only read files). After 16:00 the 1-per-5h rule applies again.

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
| `ancestral-dsi-origin-recoverability` | 87273a8 | H1 Inconclusive (usable +2.9 pp, -5.9 to +10.8; placeholders +9.1); H2 Refuted (24/300 test records determinable; 61% lab material, 30% not stated, 9% findable) | reviewed 2026-10-23: **publish with edits**; fixes in b0149e2 (D10: nine gold labels to the plan's rule, ceiling 6.3%, all arms 0%; placeholder claim withdrawn); confirmation queued (review/confirm_prompt.md) |
| `trust-retraction-risk-frozen-forecast` | b314e0f | H1 Inconclusive (E@1% 3.7x, 1.4-13.3); H2 Supported (authors+references 11.4x, 6.0-14.1); H3 sealed for 2028-12-31 | reviewed 2026-10-23: **fix first** (degenerate 10-tree fit; PMC-host 59% of top 1% via host_rate shift; Crossref self-update dates; Hindawi claim untested; notices in cohort; H3 seal needs decision rule) |
| `blue-pacific-reef-island-area-tide-corrected` | ed14c61 | H1 not testable (guard: Landsat C1 vs S2-30m +1.24%/yr; Inconclusive without it, D +0.15, -0.52 to +0.86); H2 Supported (tide bias 2.08%/yr, 1.57-2.65; noise floor 0.29); D6 made after the first rates run | awaiting review (brief: review/prompt.md) |
| `auckland-nz-2023-storms-estuary-mud-natural-experiment` | fb30a30 | H1 Inconclusive (+1.93 pp, -2.33 to +5.67); H2 Inconclusive (-0.21 pp/IQR, -3.06 to +3.20); exposure mostly harvest; post hoc region-wide 2023 pulse +4.26 pp | awaiting review (brief: review/prompt.md) |
| `auckland-nz-kauri-dieback-multitemporal-lidar` | e8a1bff | H1 Refuted (change AUC 0.51, 0.44-0.56); H2 Inconclusive (gain +0.048); 2021 labels faint (0.55) | awaiting review (brief: review/prompt.md) |

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
