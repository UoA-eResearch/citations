# Auckland / Aotearoa New Zealand scouting round (2026-10-03)

**Inputs.**

- Four local-context scouts, one per theme: hazards and climate, urban systems, health and society, and environment and
  biodiversity. Each returned 3 leads (`*.json`, verbatim).
- One calibration critic (`critic.json`). It spot-checked novelty using Crossref, Europe PMC and arXiv, since the
  session's WebSearch quota was exhausted. It also checked feasibility, scores, Te Mana Raraunga handling, duplicates and
  time-sensitivity.

**Merge.** All 12 leads were merged into `../../leads.json` under domain `auckland-nz`. Critic scores were applied, and
scout scores are kept as `scout_*_score` where they changed. Each lead also carries `local_relevance`, `time_sensitive`
and `needs_engagement`.
