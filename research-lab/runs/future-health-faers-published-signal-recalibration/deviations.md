# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 14:24 NZDT — larger token budget for 64 extraction failures (before any extraction was validated or used)

The first pass extracted 1,766 of 1,830 abstracts. For 58 of the 64 failures the reasoning model spent its whole
4,096-token budget reasoning and returned no answer; the other 4 returned truncated JSON. Those 64 are retried with a
16,384-token budget (`MAX_TOKENS=16384`). The prompt, schema and temperature are unchanged. Papers still failing are
reported as extraction failures and stay in the denominator of papers processed.
