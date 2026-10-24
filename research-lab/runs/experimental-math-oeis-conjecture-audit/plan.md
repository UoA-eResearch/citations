# Plan (preregistration): how many machine-guessed OEIS conjectures are false?

Lead: `experimental-math-oeis-conjecture-audit`. Written before any OEIS entry is parsed.

**Seen before this plan:**
- the format of one entry (A000045);
- the layout of the OEIS data repository (entries in `seq/`, b-files in Git LFS served from oeis.org);
- the LODA programs repository and its interpreter release.

## 0. Hypothesis

**H1.** At least 100 of the conjectured recurrences and generating functions recorded in OEIS entries are false.
False means contradicted by further terms that two independent sources agree on: a LODA program run locally and
the entry's b-file.
- **Supported** if the count of such confirmed falsifications is at least 100.
- **Refuted** if it is below 100.

The count is a lower bound: only conjectures this pipeline can parse and screen are tested (§3).

## 1. Data

- **Entries.** The OEIS data repository (github.com/oeis/oeisdata, shallow clone of `main` on 2026-10-25), every
  `seq/A*/A*.seq` file. Data terms come from %S/%T/%U, and the offset from %O.
- **Candidate lines.** %F (formula) lines that contain "conjecture" or "empirical" (case-insensitive) and state one
  of:
  - **(C)** a linear recurrence with constant coefficients, a(n) = Σ cᵢ a(n−i) (+ constant);
  - **(G)** a rational generating function, G.f.: P(x)/Q(x), with integer-polynomial P and Q;
  - **(D)** a P-recursive relation ("D-finite with recurrence", or Σ pᵢ(n) a(n−i) = 0 with polynomials pᵢ).

  Other conjectures (closed forms, sums, products, inequalities, asymptotics) are counted as "not parsed".
- **LODA.** github.com/loda-lang/loda-programs (shallow clone, 2026-10-25), interpreter loda-cpp v26.8.1 (linux-x86).
- **b-files.** `https://oeis.org/A{n}/b{n}.txt`, fetched only for screened disagreements (§3), at most one request
  per second and at most 2,000 files.

## 2. Executable conjectures

- **Parsing.** Each candidate line is parsed into a predictor. (C) and (D) are run forward from the data's initial
  terms. (G) is expanded as a power series and aligned to the offset.
- **The data check.** The predictor must reproduce every data term it can reach. A conjecture that fails on the
  data itself is classed "contradicted by its own data" and reported separately (often an offset or typing
  slip). It does not count toward H1.

## 3. Screening and confirmation

- **Screening.**
  - For each entry with a data-consistent conjecture and a LODA program, `loda eval` computes terms up to twice the
    number of data terms (at most 1,000), with a 20-second limit per program.
  - A LODA program that does not reproduce the entry's data terms is discarded.
  - A **screened disagreement** is the first index beyond the data where the conjecture's prediction differs from
    the LODA term.
- **Confirmation.**
  - The entry's b-file is fetched. A **confirmed falsification** requires the b-file term at the disagreement
    index (or at an earlier index beyond the data where the conjecture already fails) to differ from the
    conjecture.
  - The b-file must agree with the data terms.
  - If the b-file does not reach that index, the case is "screened, unconfirmed".
- **Conjectures not screened** (no LODA program, or LODA fails) are counted by class.

## 4. Secondary (labelled as such)

1. The false rate among screened conjectures, by class (C, G, D), with Wilson intervals.
2. How far beyond the data the first failure occurs (absolute and relative index).
3. Whether falsified conjectures cluster by entry age or keyword. A-numbers of confirmed falsifications are listed
   (public facts useful to OEIS editors). Contributor names are not analysed or reported.
4. LODA programs that disagree with b-files are reported in aggregate as a by-product.

## 5. Limits stated in advance

- **Coverage.** Only parseable C/G/D conjectures with LODA programs are screened, and confirmation needs a b-file
  that reaches the disagreement.
- **LODA programs are not proofs.** They are mined to match known terms. Agreement of LODA and b-file is strong,
  not certain, evidence.
- **Certification is out of scope.** The lead's certification arm (proofs by closure properties) is not
  attempted.
- **Fetching from oeis.org is kept small and slow** by design.
