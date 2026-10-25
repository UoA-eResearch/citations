# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do "flexible-then-rigid" proofs rot faster in mathlib? Replaying 2,700 old proofs a year later: flagged proofs fail more often, but the effect is not reliably 1.5× | primary OR 1.48 (0.92-2.39); 43.6% vs 25.1% | Supported |  |
| 2 | standfirst | Mathlib proofs containing a non-terminal unrestricted `simp`, from the 31 March 2025 master snapshot, were replayed verbatim into the files of 31 March 2026 wherever the statement text was unchanged, then compiled against that snapshot's prebuilt library. | plan.md; rot.py replay | Supported |  |
| 3 | standfirst | The flexible linter's warnings in the old snapshot define "flagged". | rot.py label | Supported |  |
| 4 | standfirst | The plan and all analysis code were committed before any replay result. | git: plan, D1, analyse.py before replays | Supported |  |
| 5 | verdict | **Verdict: H1 Inconclusive.** | primary H1 Inconclusive | Supported |  |
| 6 | verdict | **H1 (flagged proofs fail on 12-month replay with odds at least 1.5 times unflagged ones): Inconclusive.** | plan.md H1 | Supported |  |
| 7 | verdict | Flagged proofs fail **43.6%** of the time against **25.1%** for unflagged ones. | primary fail_flagged 0.4364, fail_unflagged 0.2511 | Supported |  |
| 8 | verdict | Adjusted for tactic count and simp-call count, with clustering by file, the odds ratio is **1.48** (95% 0.92 to 2.39; p = 0.11). | primary or 1.4805 (0.9178-2.3881), p 0.108 | Supported |  |
| 9 | verdict | Population: 2,723 proofs in 1,294 files, of which 110 are flagged. | primary n 2,723, files 1,294, n_flagged 110 | Supported |  |
| 10 | verdict | **The direction is consistent, but not across every comparison:** | decay, excluding-unknown, secondary, pooled ORs | Supported |  |
| 11 | verdict | six months later: OR 1.67 (1.01 to 2.77), with 30% against 13% failing; | decay O+6_gee 1.673 (1.012-2.768); 30.0% vs 13.0% | Supported |  |
| 12 | verdict | setting aside failures whose only error is an unknown identifier (a removed or renamed name): OR 1.62 (1.01 to 2.59); | excluding_unknown_identifier_only 1.619 (1.010-2.594) | Supported | was 'removed or renamed lemmas' (unknown identifier covers any removed or renamed name) |
| 13 | verdict | the second pair (September 2025 to September 2026): OR 0.99 (0.55 to 1.78); | secondary_pair 0.994 (0.555-1.783) | Supported |  |
| 14 | verdict | pooled: 1.29 (0.89 to 1.88). | pooled 1.295 (0.892-1.878) | Supported |  |
| 15 | verdict | **How proofs rot.** | heading | Supported |  |
| 16 | verdict | A quarter of proofs fail verbatim a year later. | primary_population fail_rate 0.2585 | Supported |  |
| 17 | verdict | Half of those whose text mathlib itself changed fail; none whose text mathlib left alone do. | same_body_fail_rate 0.0; changed_body_fail_rate 0.4961 | Supported |  |
| 18 | verdict | The most common first error is an unknown identifier, a name the proof uses (usually a lemma) having been removed or renamed (37% of failures). | error_classes unknown_identifier 258 / 704 = 37% | Supported | was 'the largest single cause' (first error class, not a causal attribution) |
| 19 | verdict | Then come unsolved goals (25%), type mismatches (12%), "function expected" errors (4%, typically a changed signature) and "no goals" (4%). | error_classes: unsolved 179 (25%), type mismatch 83 (12%), function expected 31 (4%), no goals 27 (4%) | Supported | 'changed lemma signatures' -> '"function expected" errors (typically a changed signature)' |
| 20 | verdict | **The pipeline is valid.** In the old snapshot, 99.94% of population proofs compile without error. | label O-side error-free 99.94% | Supported |  |
| 21 | plain terms | Mathlib is a huge, shared library of formally verified mathematics written in the Lean proof assistant. | background | Supported |  |
| 22 | plain terms | Its proofs must keep compiling as the library changes, and when the library changes, some proofs break. | background | Supported |  |
| 23 | plain terms | Mathlib has a style check, the "flexible linter", based on the belief that a common pattern is fragile: an automatic simplification step (`simp`) followed by a precise step that depends on exactly what `simp` produced. | ledger F1 (linter docstring) | Supported |  |
| 24 | plain terms | If `simp` changes, the precise step breaks. | linter rationale (ledger F1) | Supported |  |
| 25 | plain terms | We tested that belief by taking about 2,700 proofs from March 2025 and pasting them, unchanged, into the March 2026 library wherever the theorem itself was unchanged. | 2,723 proofs; statement-unchanged population | Supported |  |
| 26 | plain terms | Proofs the style check had warned about broke more often: 44% against 25%. | 43.6% vs 25.1% | Supported |  |
| 27 | plain terms | After allowing for proof length, the odds of breaking were about one and a half times higher. | OR 1.48 adjusted for tactic and simp counts | Supported |  |
| 28 | plain terms | That is close to what was predicted, but the uncertainty is wide enough that we can't confirm it, and a second year-long comparison showed no difference. | CI 0.92-2.39 includes 1; second pair 0.99 | Supported |  |
| 29 | plain terms | So the style rule points the right way, but its effect is modest next to the most common reason proofs break: names, usually lemmas, being renamed or removed. | OR 1.48 vs unknown identifier 37% of failures | Supported | 'lemmas being renamed or removed' -> 'names, usually lemmas' |
