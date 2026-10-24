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
