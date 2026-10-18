# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 16:50 NZDT — generator details fixed before any item was generated

- **Stability editions.** The PBS API's earliest schedule is 1 November 2025, so the NZ stability edition is also
  November 2025, not the plan's October 2025. Both jurisdictions then use 11 months.
- **Families (a) and (b)** are restricted to single-ingredient tablets and capsules. Each item is keyed by its
  normalised chemical, its strength (first number and unit, with mcg/µg unified) and a modified-release flag.
  - Questions are rendered in the same generic form in both jurisdictions, for example "budesonide 3 mg capsule
    (modified release)", so the wording does not reveal the source.
  - Other dose forms cannot be matched reliably across the two documents' formulation vocabularies.
- **AU scope.** The General Schedule program only (`program_code` GE), comparable to the NZ Community section (B).
- **AU "authority required"** means benefit type A or S (Streamlined Authority).
- **NZ "Special Authority required"** means a Rule of Type "Special" with Attribute "Subsidy", on the formulation,
  its chemical or an ATC ancestor.
- **Mixed items are excluded from (b):** formulations whose packs or brands carry different flags, in either
  jurisdiction.
- **Grouping for counterfactual criteria (d).** Groups use the matched chemical's ATC level 2 from the NZ Schedule,
  in both jurisdictions (the PBS item table carries no ATC code).
- **The criteria themselves:**
  - NZ: the MathML criterion texts in the chemical's Special Authority request forms;
  - AU: the prescribing texts linked to the chemical's GE items through their restrictions.
