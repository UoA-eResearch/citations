# Plausibility (G3), added after the independent review

- **The N axis.**
  - The preregistered N is non-embedding parameters, recomputed from the configs as L(12d² + 13d) + 2d (D3).
    `fix_n.py` asserts that the first run's N equals this plus one 50,304 × d output head, for all sizes.
  - Under this N the fitted α (median 0.10) is low against the Chinchilla paper's α = 0.34, which was fitted with
    total parameters. Under total N it is 0.25, so α is not a stable property of this ladder.
  - The fitted asymptote E has a 5th percentile of 0.16 nats, implausibly low for Pile text. The extrapolation is
    therefore ill-conditioned under the preregistered N.
- **The size of the seed effect.** The 410M seed SD (0.132) comes almost entirely from two runs. Without them it is
  0.010, in line with 70M and 160M (0.029, 0.019).
  - The PolyPythias authors flag exactly these two runs as outliers. That they dominate a forecast built on the
    largest rung is the expected consequence.
- **Three units traced.**
  - **410M seed 4, step 143k:** loss 2.41 against 1.98 for seed 0. Neighbouring checkpoints agree (2.43, 2.42, 2.41
    at 141k–143k), and a batch-1 re-evaluation reproduces it (`spike_check.csv`).
  - **14M seed 0 against seed 4:** seed 0 falls monotonically; seed 4 ends 0.43 nats above its minimum.
  - **The 2.8B target (fp16):** 1.704 nats. The fp16–fp32 difference at 1B and 1.4B is at most 6×10⁻⁵, so precision
    does not explain the overshoot.
- **Evaluation noise against effect sizes.** The paired document-bootstrap SD of the 2.8B-minus-410M loss is 0.0076
  nats, far below both the seed width (0.10) and the overshoot (0.06), so neither is an evaluation artefact.
