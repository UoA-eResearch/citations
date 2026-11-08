# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do "flexible-then-rigid" proofs rot faster in mathlib? Replaying 2,500 old proofs a year later: flagged proofs fail more often, mostly because a tactic many of them used lost its default import; the effect is not reliably 1.5×, and few failures carry the errors the linter's rationale predicts | primary.json primary 1.57 (0.97-2.55); induction_prime; error_classes_by_flag_first | Supported |  |
| 2 | standfirst | Mathlib proofs containing a non-terminal unrestricted `simp`, from the 31 March 2025 master snapshot, were replayed verbatim into the files of 31 March 2026 wherever the statement text was unchanged, then compiled against that snapshot's prebuilt library. | plan.md; rot.py replay | Supported |  |
| 3 | standfirst | The flexible linter's warnings in the old snapshot define "flagged". | rot.py label | Supported |  |
| 4 | standfirst | The plan and all analysis code were committed before any replay result. | git: plan, D1, analyse.py before replays | Supported |  |
| 5 | verdict | **Verdict: H1 Inconclusive.** | primary H1 Inconclusive | Supported |  |
| 6 | verdict | **H1 (flagged proofs fail on 12-month replay with odds at least 1.5 times unflagged ones): Inconclusive.** | plan.md H1 | Supported |  |
| 7 | verdict | Flagged proofs fail **43.6%** of the time against **26.0%** for unflagged ones. | primary.json primary fail_flagged 0.4364, fail_unflagged 0.2603 | Supported |  |
| 8 | verdict | Adjusted for tactic count and simp-call count, with clustering by file, the odds ratio is **1.57** (95% 0.97 to 2.55; p = 0.07). | primary.json primary or 1.5745 (0.9712-2.5524) p 0.0655 | Supported |  |
| 9 | verdict | Population: 2,488 proofs in 1,203 files, of which 110 are flagged. | primary.json primary n 2488 files 1203 n_flagged 110 | Supported |  |
| 10 | verdict | These numbers are corrected after review: the first draft counted 231 terminal `simp` calls with a multi-line argument list as non-terminal (OR 1.48, 0.92 to 2.39 on 2,723 proofs). | D3; primary_v2_pre_d3.json (OR 1.4805); 231 removed | Supported |  |
| 11 | verdict | The adjustment matters. | primary.json primary_unadjusted_or 2.2 vs 1.57 | Supported |  |
| 12 | verdict | The unadjusted odds ratio is 2.20, and with an independence working correlation the adjusted ratio is 1.70 (1.01 to 2.85). | primary.json primary_unadjusted_or 2.2; primary_independence 1.7004 (1.0128-2.8547) | Supported |  |
| 13 | verdict | **Two first-year comparisons clear 1.0, but both rest on one import change:** | primary.json decay O+6_gee, excluding_unknown_identifier_only; excluding_induction_prime | Supported |  |
| 14 | verdict | six months later: OR 1.80 (1.12 to 2.90), with 30% against 14% failing; | primary.json decay O+6_gee 1.7983 (1.1166-2.8962); 0.30 vs 0.1351 | Supported |  |
| 15 | verdict | setting aside failures whose only error is an unknown identifier (a removed or renamed name): OR 1.73 (1.07 to 2.77); | primary.json excluding_unknown_identifier_only 1.7261 (1.0748-2.7723) | Supported |  |
| 16 | verdict | **the `induction'` confound** (found at confirmation, post hoc). | D4; review confirmation N1 | Supported |  |
| 17 | verdict | All 119 population proofs that use `induction'` fail, because Mathlib.Tactic.Common stopped importing it between the snapshots. | primary.json induction_prime fail_rate_among_users 1.0, 119 proofs; Mathlib/Tactic/Common.lean import change (confirmation) | Supported |  |
| 18 | verdict | Flagged proofs use it four times as often (18 of 110 against 101 of 2,378). | primary.json induction_prime 18/110 vs 101/2378 | Supported |  |
| 19 | verdict | Excluding them, no comparison clears 1.0: primary 1.43 (0.84 to 2.43), six months 1.57 (0.88 to 2.78), without unknown-identifier failures 1.55 (0.92 to 2.62), pooled 1.27 (0.83 to 1.95); | primary.json excluding_induction_prime (all CIs include 1) | Supported |  |
| 20 | verdict | the second pair (September 2025 to September 2026): OR 1.03 (0.57 to 1.85). | primary.json secondary_pair 1.029 (0.5723-1.8501) | Supported |  |
| 21 | verdict | Its flagged proofs are what was left after mathlib adopted the linter and rewrote nearly every flagged proof (below), so this is not a replication. | primary.json body_changed_flagged 109/110; reviewer finding 1 (linter adopted in Init between O and O2) | Supported |  |
| 22 | verdict | **Mathlib had already rewritten almost every flagged proof.** | primary.json primary_population body_changed_flagged [109, 110] | Supported |  |
| 23 | verdict | Between the two snapshots, mathlib changed the body of 109 of 110 flagged proofs (99%), against 1,195 of 2,378 unflagged ones (50%). | primary.json body_changed_flagged [109, 110], body_changed_unflagged [1195, 2378] | Supported |  |
| 24 | verdict | The linter entered mathlib's defaults during that year. | D1 (linter injected for O, whose Init does not import it); review finding 1 | Supported |  |
| 25 | verdict | This does not bias H1: failure depends only on the old body and the new library. | design: fail depends on O's body and N's library only (review finding 1) | Supported |  |
| 26 | verdict | The first draft also reported that "proofs whose text mathlib left alone never fail", which is true by construction (such a body is the new file's own). | review finding 1 (same body = N's own file) | Supported | withdrawn |
| 27 | verdict | It is withdrawn. | D3 | Supported |  |
| 28 | verdict | **How proofs rot** (first reported error of the 667 failing proofs; corrected after review): | primary.json error_classes_first (667 failures) | Supported |  |
| 29 | verdict | unknown identifier, a removed or renamed name (32%); | primary.json error_classes_first unknown_identifier 216/667 | Supported |  |
| 30 | verdict | type mismatch (11%), unsolved goals (6%), rewrite failed (5%), "function expected" (4%, typically a changed signature), simp, dsimp or field_simp made no progress (3%), no goals (1%) and timeouts (4 proofs); | primary.json error_classes_first (667) | Supported |  |
| 31 | verdict | other messages (36%). | primary.json error_classes_first other 239/667 | Supported |  |
| 32 | verdict | Of these, 118 are "unknown tactic", the `induction'` import change (18 of the 48 flagged failures). | primary.json first_error_unknown_tactic 118, flagged 18 of 48 | Supported |  |
| 33 | verdict | Another 47 are "invalid field … environment does not contain", renamed names reached by dot notation. | primary.json first_error_invalid_field_env 47 | Supported |  |
| 34 | verdict | **The linter's own failure modes are rare among flagged failures.** The two classes its rationale predicts are simp making no progress and a rewrite pattern no longer found. | primary.json error_classes_by_flag_first | Supported |  |
| 35 | verdict | They are the first error for 3 of 48 failing flagged proofs (6%), against 53 of 619 unflagged ones (9%). | primary.json error_classes_by_flag_first: flagged 2+1 of 48; unflagged 21+32 of 619 | Supported |  |
| 36 | verdict | The first draft's patterns missed both classes entirely, because newer Lean writes "`simp` made no progress" and "Did not find an occurrence of the pattern". | primary_v2_pre_d3.json error_classes (no simp_no_progress, no rewrite_failed); rot.py ERR | Supported |  |
| 37 | verdict | **The pipeline is valid.** In the old snapshot, 99.94% of population proofs compile without error. | label O-side error-free 99.94% | Supported |  |
| 38 | plain terms | Mathlib is a huge, shared library of formally verified mathematics written in the Lean proof assistant. | background | Supported |  |
| 39 | plain terms | Its proofs must keep compiling as the library changes, and when the library changes, some proofs break. | background | Supported |  |
| 40 | plain terms | Mathlib has a style check, the "flexible linter", based on the belief that a common pattern is fragile: an automatic simplification step (`simp`) followed by a precise step that depends on exactly what `simp` produced. | ledger F1 (linter docstring) | Supported |  |
| 41 | plain terms | If `simp` changes, the precise step breaks. | linter rationale (ledger F1) | Supported |  |
| 42 | plain terms | We tested that belief by taking about 2,500 proofs from March 2025 and pasting them, unchanged, into the March 2026 library wherever the theorem itself was unchanged. | primary.json primary n 2488 | Supported |  |
| 43 | plain terms | Proofs the style check had warned about broke more often: 44% against 26%. | primary.json primary fail_flagged 0.4364 vs 0.2603 | Supported |  |
| 44 | plain terms | After allowing for proof length, the odds of breaking were about one and a half times higher. | primary.json primary or 1.5745 (adjusted) | Supported |  |
| 45 | plain terms | That is close to what was predicted, but the uncertainty is wide enough that we can't confirm it, and a second year-long comparison showed no difference. | primary.json primary ci; secondary_pair 1.029 | Supported |  |
| 46 | plain terms | So the extra breakage of flagged proofs is real but mostly comes from one change: a tactic many of them used stopped being imported by default. | primary.json induction_prime; excluding_induction_prime | Supported |  |
| 47 | plain terms | Without those proofs the difference is small and uncertain, and the flagged proofs that broke rarely did so in the way the rule's rationale describes. | primary.json excluding_induction_prime primary 1.43 (0.84-2.43); error_classes_by_flag_first | Supported |  |
