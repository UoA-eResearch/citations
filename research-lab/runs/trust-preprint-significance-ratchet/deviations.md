# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 15:51 NZDT — before any statistic was extracted

1. **Linkage routes are not independent.** Europe PMC's "Preprint of" links say "CrossRef Pre-print loader";
   PreprintToPaper's "Published" label is bioRxiv's own link; Crossref's is-preprint-of on bioRxiv DOIs is deposited
   by bioRxiv ("asserted-by subject"). The lead's ">= 2 of 4 routes" would mostly count one assertion twice. Every
   server-asserted link is instead confirmed by an independent title-similarity check (Jaccard >= 0.5): 28,597 of
   31,261 candidates pass.
2. **Version.** 57% of usable pairs have no version in Europe PMC; Research Square DOIs encode it (/vN), bioRxiv and
   medRxiv DOIs do not. The primary uses pairs known to be version 1 (about 11,500); all 23,220 pairs are a labelled
   sensitivity.
3. **No embedding model** for alignment residue; masked TF-IDF plus exact tuple matching, validated blind (plan 6).
4. **Bulk route note.** The bioRxiv /pubs route is slow (~6 s per 100 links) and was still running when linkage was
   confirmed; Crossref carries the same bioRxiv-deposited links, so its absence changes few pairs. If it finishes before
   the pipeline, confirm is not re-run (the pair set is fixed here).
5. **Validation by the agent, not a human**, as plan section 6 states, blind to version order and stratum.
