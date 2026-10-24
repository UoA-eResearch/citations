# Plan (preregistration): how often does "apparent convergence" mislead approximate quantum-circuit simulators?

Lead: `quantum-simulation-convergence-false-assurance`. Written before any instance is simulated.

**Seen before this plan:**
- the Quantum Advantage Tracker's circuit-model files and READMEs (Floquet mixed-field Ising parameters, the
  heavy-hex QASM);
- the APIs of TensorNetworkQuantumSimulator.jl 0.4.6 and PauliPropagation.jl 0.9.2.

## 0. Hypotheses

Approximate simulators are often trusted when their two finest truncation settings agree.

- **H1.** Among instances whose two finest settings agree within 0.01 ("apparently converged"), more than 10% have
  true absolute error above 0.03, for at least one of the two methods (BP-PEPS, sparse Pauli propagation).
  - **Supported** if, for at least one method, the bootstrap 95% lower bound of that share exceeds 0.10.
  - **Refuted** if the upper bound is below 0.10 for both methods.
  - **Inconclusive** otherwise, including when a method has fewer than 20 apparently converged instances.
- **H2.** An interval of k × (the spread of the two finest settings), with k fitted on a random half of instances to
  give 90% coverage, covers the truth for 85–95% of the held-out half.
  - **Supported** if that holds for both methods.
  - **Refuted** if it holds for neither.
  - **Inconclusive** otherwise.

## 1. Instances (300, plus a separate 30-instance pilot)

- **Lattice.** The heavy-hex coupling graph of the tracker's 74-qubit Floquet circuit (from its `rzz` pairs), with a
  3-colouring of its edges.
- **Patches.** Connected subgraphs of n ∈ {20, 22, 24, 26} qubits, grown by breadth-first search from a random seed
  qubit with random tie-breaking.
- **Family F (Floquet mixed-field Ising, after the tracker's model).** U_F is the product over colours m = 1..3 of
  RZZ(θ_zz) on colour-m edges × RZ(θ_z/3) on all qubits × RX(θ_x/3) on all qubits.
  - Each parameter is the published value (θ_x = 1.56567, θ_z = 0.33879, θ_zz = π/3) times U(0.7, 1.3).
  - Cycles N_c ∈ {4, 8, 12, 16}. Initial state |0…0⟩.
- **Family K (kicked Ising).** Per layer: RX(θ) on all qubits, then RZZ(−π/2) on all edges, colour by colour.
  - θ ~ U(0, π/2). Layers ∈ {5, 10, 15, 20}.
- **Observable:** magnetization M = (1/n) Σ ⟨Z_i⟩.
- **Design.** 150 instances per family, stratified 4 sizes × 4 depths, with seeds fixed (20261025). The pilot uses
  different seeds and is not analysed.

## 2. Exact values and approximate methods

- **Exact.** Numpy statevector (complex128), applying each sub-layer's diagonal ZZ and Z phases as one multiply.
  5% of instances are recomputed for reproducibility (agreement to 1e-10).
- **BP-PEPS** (TensorNetworkQuantumSimulator.jl). Gates are applied with `apply_gates` on a BeliefPropagationCache,
  with `maxdim = χ` and cutoff 1e-10, and expectations come from BP.
- **Pauli propagation** (PauliPropagation.jl). M is propagated in the Heisenberg picture with `min_abs_coeff = ε`
  (no weight cap) and its overlap with |0…0⟩ taken.
- **Ladders.**
  - Provisional: χ ∈ {4, 8, 16, 32, 64} and ε ∈ {1e-2, 3e-3, 1e-3, 3e-4, 1e-4}.
  - **Frozen after the pilot (D1)** so that the finest setting still has median absolute error above 1e-3 on the
    pilot, dropping finer settings if they are near-exact. Settings exceeding 15 minutes on the largest pilot
    instances are also dropped.
  - The two finest frozen settings define apparent convergence and spread.

## 3. Analysis

- **False-assurance share** per method, with a bootstrap 95% interval (2,000 instance resamples).
- **H2.** A random half (seed 20261025) fits k as the 90th percentile of |error| / spread among instances with
  spread > 0. Coverage is then evaluated on the other half.
- **Secondary:**
  - shares by family, size and depth;
  - the relationship of error to BP message residuals or Pauli discarded weight, where available;
  - the runtime of each setting.

## 4. Limits stated in advance

- **Scale.** Patches of 20–26 qubits are far smaller than tracker instances (50–100 qubits), so error modes at
  scale may differ.
- **Families.** Only two families. The tracker's Operator Loschmidt Echo needs a trace estimator and is not included.
- **Ladders.** Pilot-frozen ladders scale truncation down, which may not mirror production settings.
