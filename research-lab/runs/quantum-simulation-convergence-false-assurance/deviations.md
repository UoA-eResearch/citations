# Deviations from plan.md

## D1 (2026-10-25 10:26 NZDT; before any approximate-method result on the pilot or main set)

1. **Exact engine: qiskit-aer instead of numpy** (plan section 2).
   - The numpy statevector took more than 10 minutes for one 26-qubit, 12-cycle Floquet instance (single-threaded),
     too slow for 300 instances.
   - Exact values now come from qiskit-aer 0.18.0 (statevector, double precision, multithreaded), on the same gate
     list. The largest pilot instance takes 55 s.
   - The numpy code stays as an independent check. Both match a dense-matrix simulation in code/instances.py test,
     and numpy is re-run on a random subset of n = 20 main instances (`instances.py crosscheck`; agreement to 1e-10
     required). This replaces the plan's "5% recomputed" check, which would be deterministic for a single engine.
2. **Half of patches built from whole hexagons** (plan section 1).
   - The pilot showed that random breadth-first patches of 20–26 qubits are often trees (0 loops). On a tree, BP is
     exact apart from bond truncation, so such patches cannot show the loop-induced BP bias that motivates the lead.
   - An alternating half of instances (odd index within a family) now starts from a random hexagon (12-cycle) of the
     74-qubit lattice, adds adjacent hexagons while the union fits n, then grows at random. These patches have 1 loop
     at n = 20 and 2 at n ≥ 22.
   - Even-index instances keep the plan's random growth. Loop count and patch type are stored per instance and
     reported as covariates.
   - A first attempt (preferring frontier qubits adjacent to two selected qubits) did not produce loops and was
     replaced before any simulation.
3. **Runs are applied layer by layer with a time guard.**
   - A run exceeding 900 s (the plan's 15-minute rule) or 10^8 Pauli strings is abandoned (status timeout or terms),
     and finer settings for that instance are skipped.
   - Abandoned settings count as unavailable. Section 3 then uses the finest two available settings, and instances
     with fewer than two available settings are excluded and counted.
4. **Frozen ladders** (2026-10-25 10:31 NZDT; from the 30-instance pilot, by the plan's rule; no main-set
   instance simulated yet). Median absolute pilot errors:

   | method | setting | median abs error | slowest run |
   |---|---|---|---|
   | BP-PEPS | χ = 4 | 0.068 | 85 s (includes compilation) |
   | BP-PEPS | χ = 8 | 0.017 | 3 s |
   | BP-PEPS | χ = 16 | 0.0035 | 4 s |
   | BP-PEPS | χ = 32 | 0.00040 | 13 s |
   | BP-PEPS | χ = 64 | 0.00027 | 91 s |
   | Pauli propagation | ε = 1e-2 | 0.25 | 3 s (includes compilation) |
   | Pauli propagation | ε = 3e-3 | 0.18 | 0.01 s |
   | Pauli propagation | ε = 1e-3 | 0.11 | 0.1 s |
   | Pauli propagation | ε = 3e-4 | 0.047 | 0.9 s |
   | Pauli propagation | ε = 1e-4 | 0.030 | 9 s |

   - **BP-PEPS ladder frozen at χ ∈ {4, 8, 16}.** χ = 32 and 64 are dropped as near-exact (median below 1e-3). The
     two finest settings are χ = 8 and 16.
   - **Pauli-propagation ladder frozen at all five settings.** The two finest are ε = 3e-4 and 1e-4.
   - No setting reached the 15-minute limit.
   - Pilot observation (not analysed): BP error is far smaller on the kicked-Ising family (Clifford entanglers) than
     on the Floquet family.

## D2 (2026-10-25 11:20 NZDT; after the first main-set results were read)

**Bug fix in code/analyse.py: the "two finest settings" were the two coarsest.**
- The first run of analyse.py sorted settings in the wrong direction for both methods. It compared χ = 4 with 8
  (instead of 8 with 16) and ε = 1e-2 with 3e-3 (instead of 3e-4 with 1e-4).
- The bug showed up because main-set errors were far above pilot errors on comparable instances. Per-instance values
  were then checked by hand (for example main_K000: BP χ = 16 gives 0.581419 against an exact 0.581357, while the
  table showed the χ = 4 error).
- The plan specifies the two finest settings. The sort now uses an explicit fineness key and asserts that the finest
  available setting is the one used.
- The buggy output is kept as `results/tables/primary_v1_coarsest_pair_bug.json`: H1 Supported (BP 7.5%, PP 70%),
  H2 Inconclusive.
- The corrected run is the primary result. No other analysis choice changed.

## Pre-review gate (G5, G6) — 2026-10-25 23:30 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 6 claims, passes):
  - the lead's description of the tracker case was wrong. It had two PEPS-BP bond dimensions "agreeing closely" at
    0.456 and 0.442, far from QESEM and SPP at about 0.39. The tracker's notes give PEPS-BP (BD=700) 0.442, SPP 0.411
    and 0.387, and QESEM 0.390 (0.369–0.412) at 16 cycles, and say neither classical method converges convincingly
    beyond about 12 cycles. The BD=512 value is not tabulated. The report now states the verified figures, and the
    "matches the tracker's warning case" sentence is rewritten (that case is visible non-convergence);
  - "empty error fields" is now quantified as 12 of 13 classical submissions;
  - Gharibyan et al. (arXiv 2507.10771) resolves, and its abstract supports the "reducing δ does not always help"
    claim.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title now notes that the 31% sits mostly on loop-rich Floquet circuits;
  - "at most about 4 times the gap" became "usually within", since it held for about 9 in 10 held-out circuits.
