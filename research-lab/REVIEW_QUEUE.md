# Studies awaiting independent review

Each of these is complete through a pre-review draft: preregistration, code, results, figures, report and a
reviewer brief in `runs/<id>/review/prompt.md`. None may be published to `leads.json`, `index.html`, the README or
the Golden Quadrant artifact until it has been through an independent adversarial review and a confirmation pass.

**Why they are queued:** the independent reviewer runs on Fable, and that model's usage limit is exhausted
(last attempt 2026-10-20, HTTP 429). Reviews resume when the limit resets or credits are added
(`/usage-credits`); the alternative is to run them on Opus, which the owner has not chosen.

| study | draft commit | verdicts in the draft | review status |
|---|---|---|---|
| `energy-outage-major-event-day-ratchet` | 2b5cb6b | H1 Inconclusive, H2 Refuted, H3 Refuted | **partial** — reviewer completed checks 1–7 before the limit hit; scripts in `review/reviewer_checks/`, no `review.md` yet. Resume the same agent to keep that work. |
| `ancestral-pacific-rainfall-gauge-circularity` | 0a73d80 | H1 Supported, H2 Refuted | not started |
| `frontier-eaa-accessibility-natural-experiment` | 0c44d7a | H1 Supported, H2 Inconclusive, H3 not testable | not started |
| `energy-nz-gas-production-forecast-calibration` | b53e197 | H1 Supported, H2 Inconclusive, H3 Supported | not started |
| `movement-nz-ev-policy-discount-vs-ruc` | 60012cc | H1 Inconclusive, H2 Inconclusive | not started |

## Order to run them in

1. `energy-outage-major-event-day-ratchet` — resume the existing agent, since its finished checks are reusable and
   they already flagged snapshot gaps and 2015 zero days.
2. `energy-nz-gas-production-forecast-calibration` — a Supported headline, so it carries the most risk if wrong.
3. `ancestral-pacific-rainfall-gauge-circularity` — also Supported.
4. `frontier-eaa-accessibility-natural-experiment` — Supported, but the effect is modest and well hedged.
5. `movement-nz-ev-policy-discount-vs-ruc` — both verdicts Inconclusive, so the least exposed.

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
