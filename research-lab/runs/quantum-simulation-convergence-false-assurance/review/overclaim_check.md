# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | When two truncation settings agree, is the answer right? In 300 exactly solvable circuits, Pauli propagation's agreement misled 31% of the time with 3× steps in its threshold, mostly on loop-rich Floquet circuits; BP-PEPS's 2% | primary.json pp 40/129 = 31% (ε 3e-4 vs 1e-4), bp 2/103; posthoc_steps.json shows the step dependence | Supported | title qualified after review (finding 1) |
| 2 | standfirst | 300 heavy-hex patch circuits of 20–26 qubits (Floquet mixed-field Ising after the Quantum Advantage Tracker's model, and kicked Ising) were simulated exactly by statevector and approximately by BP-PEPS (TensorNetworkQuantumSimulator.jl) and sparse Pauli propagation (PauliPropagation.jl), on truncation ladders frozen from a separate pilot. | plan.md; deviations D1 | Supported |  |
| 3 | standfirst | An estimate is "apparently converged" when its two finest settings agree within 0.01. | plan.md H1 definition | Supported |  |
| 4 | standfirst | The question is how often such an estimate is still off by more than 0.03. | plan.md H1 definition | Supported |  |
| 5 | verdict | **Verdict: H1 Supported. | primary H1 Supported | Supported |  |
| 6 | verdict | H2 Supported, but Pauli propagation's calibration fails within the Floquet family.** | primary H2 Supported; pp coverage_by_family F 0.795 | Supported |  |
| 7 | verdict | **H1 (more than 10% of apparently converged estimates are wrong by more than 0.03, for at least one method): Supported.** | plan.md H1 | Supported |  |
| 8 | verdict | **Pauli propagation (ε 3e-4 vs 1e-4):** 40 of 129 apparently converged estimates are wrong, **31%** (95% 23–39%). | pp n_conv 129, n_fa 40, share 0.310 (0.234-0.390) | Supported |  |
| 9 | verdict | **This share depends on the ladder's step size** (post hoc, prompted by the review). | posthoc_steps.json pairs: share varies 4.3%-31% with the PP step | Supported | post hoc |
| 10 | verdict | The finest Pauli-propagation setting's median error (0.030) equals the 0.03 threshold, and the error falls only 1.5× per step, against 2.5× for BP-PEPS. | posthoc_steps.json finest_setting_median_error pp 0.0303; adjacent_error_ratio_median pp 3e-4->1e-4 1.534, bp 8->16 2.489 | Supported |  |
| 11 | verdict | With a 10× step (ε 1e-3 vs 1e-4) the share is 4.3% (2 of 46). | posthoc_steps.json pairs 'pp 0.001 -> 0.0001': converged 46, false_assurance 2, share 0.0435 | Supported |  |
| 12 | verdict | The two ladders were frozen by the plan's rule but are not comparable objects. | posthoc_steps.json: PP 3x steps vs BP 2x steps; error ratio per step 1.5 vs 2.5 | Supported |  |
| 13 | verdict | The 31% against 2% is partly a property of the ladders, not only of the methods. | posthoc_steps.json: shares change with step choice within each method (PP 4.3-31%, BP 1.9-7.5%) | Supported | hedged ('partly') |
| 14 | verdict | **BP-PEPS (χ 8 vs 16):** 2 of 103, **1.9%** (0–5.1%). | bp n_conv 103, n_fa 2, share 0.019 (0-0.051) | Supported |  |
| 15 | verdict | **Where it happens.** | heading | Supported |  |
| 16 | verdict | Pauli propagation's false assurance sits almost entirely in the Floquet circuits: **39 of 51 (76%; 64–88%)**, against 1 of 78 for kicked Ising. | pp by_family F 39/51 = 0.765 (0.635-0.875); K 1/78 | Supported |  |
| 17 | verdict | At 16 Floquet cycles, all 22 apparently converged estimates are wrong. | pp by_depth_family F16 22/22 | Supported |  |
| 18 | verdict | It is concentrated in patches containing loops: 34 of 66 hexagon-based patches, against 6 of 63 random patches. | pp by_compact True 34/66, False 6/63 | Supported |  |
| 19 | verdict | **The verdict depends on that D1 design change.** On the plan's original random-growth patches alone, the share is 9.5% (3.1–17.4%), which would be Inconclusive. | pp by_compact False 6/63 = 0.095 (0.031-0.174) (post hoc sensitivity) | Supported |  |
| 20 | verdict | The hexagon-based half was added before any approximate result because random patches are often trees, but readers should weigh it (post hoc sensitivity). | deviations D1 (before approximate results) | Supported |  |
| 21 | verdict | **The cause is a shared bias.** In 85% of false-assurance cases the estimate is shrunk toward zero. | instances.csv: 85% of pp false-assurance cases with abs(v1) < abs(exact) | Supported |  |
| 22 | verdict | Both thresholds discard weight in the same direction, so they agree with each other while both miss the truth. | instances.csv: pp signed error negative in F (mean -0.114) | Supported |  |
| 23 | verdict | **H2 (a "k × spread" interval, with k fitted on half the instances, covers 85–95% of the other half, for both methods): Supported on the preregistered pooled test.** | plan.md H2 | Supported |  |
| 24 | verdict | BP-PEPS: k = 3.8, coverage **93%**. | bp h2 k 3.82, coverage 0.933 | Supported |  |
| 25 | verdict | Pauli propagation: k = 12.5, coverage **87%**, but only 79% within the Floquet family (94% for kicked Ising). | pp h2 k 12.49, coverage 0.867; by family F 0.795, K 0.935 | Supported |  |
| 26 | verdict | A single multiplier does not calibrate Pauli propagation across circuit types. | pp coverage F 0.795 vs K 0.935 | Supported |  |
| 27 | verdict | **BP-PEPS's own diagnostics are informative:** | heading | Supported |  |
| 28 | verdict | its gate-truncation error tracks the true error (Spearman 0.72); | exploratory_diagnostics bp spearman 0.722 | Supported |  |
| 29 | verdict | its ladder spread tracks the true error more tightly than Pauli propagation's does (0.89 against 0.56). | exploratory_diagnostics spread-error spearman bp 0.890, pp 0.559 | Supported |  |
| 30 | verdict | **D2:** the first analysis run accidentally compared the two coarsest settings. | deviations D2 | Supported |  |
| 31 | verdict | The fix and the buggy output (H1 Supported, H2 Inconclusive) are recorded; the stored buggy output was regenerated after the fix, for the record. | deviations.md D2 note: v1 file written 3 s before primary.json (file times; review finding 2) | Supported |  |
| 32 | plain terms | Computers that simulate quantum circuits approximately have a dial: turn it up and the answer gets more accurate, but slower. | background | Supported |  |
| 33 | plain terms | A common way to decide an answer is trustworthy is to turn the dial up a notch and see whether the answer changes. | background | Supported |  |
| 34 | plain terms | If it barely moves, people assume it has "converged". | background | Supported |  |
| 35 | plain terms | Classical entries in the public Quantum Advantage Tracker are judged largely this way, without error bars. | ledger Q1 (12 of 13 classical submissions without error bounds) | Supported |  |
| 36 | plain terms | We tested that habit on 300 small circuits whose true answers we could compute exactly. | 300 instances, exact statevector | Supported |  |
| 37 | plain terms | For one popular method, Pauli propagation, about a third of the answers that looked converged were wrong by a meaningful amount. | pp share 0.31 | Supported |  |
| 38 | plain terms | For the circuit type modelled on a real tracker challenge, three-quarters were. | pp Floquet 0.765 | Supported |  |
| 39 | plain terms | The reason: as that method discards small terms, its answers drift steadily toward zero, and a slightly finer setting drifts the same way, so the two agree while both are wrong. | pp shrinkage toward zero in 85% of FA cases | Supported |  |
| 40 | plain terms | The other method, a tensor-network approach, was rarely fooled in this way: when its two finest settings agreed, it was almost always right. | bp FA 2/103 | Supported |  |
| 41 | plain terms | A simple rule of thumb ("the true error is usually within about 4 times the gap between the last two settings", which held for about 9 in 10 held-out circuits) gave it honest error bars. | bp h2 k 3.82, held-out coverage 0.933 | Supported | was 'at most about 4 times' (covers about 9 in 10, not all) |
