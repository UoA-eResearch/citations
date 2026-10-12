# Deviations from the lead and from the plan

## D1 — 2026-10-13 09:43 NZDT — three departures from the lead, all before any panel prediction

Recorded with the preregistration, so that the plan's own text can be read as final.

1. **The panel axes are the other way round.** The lead says "442 inhibitors x 72 kinases". Davis et al.
   2011 profiled 72 inhibitors against 442 kinase assays; DeepDTA packages 68 of the inhibitors, giving a
   complete 68 x 442 Kd matrix. All estimands are defined on the correct axes: "within-ligand across-target"
   means one of 68 ligands ranked across kinases.
2. **The decoy hypothesis is restated.** The lead predicted a predicted-affinity shift of "< 0.5 log units
   for >= 50% of ligands" when the protein is swapped for an unrelated one. Prior work points the other way
   (Koch's LIT-PCBA target-identification benchmark; and the lead's own critic note cites a ChemRxiv
   preprint reporting >100-fold shifts, which I could not locate in any search and therefore record as
   unverified). The decoy arm is demoted to a descriptive secondary and restated as a comparison of the
   decoy-induced shift with the within-kinome spread of the same ligand's predictions. No verdict depends
   on it. Reasons in plan.md §1.2.
3. **Kinase inputs are the annotated kinase domain plus a 20-residue flank, not the full-length sequence.**
   Davis protein entries are full-length (median 707 aa, up to 2549); co-folding those is unaffordable at
   panel scale and is not what the KINOMEscan competition assay reports. Disclosed as a limitation
   (plan.md §9.3), uniform across kinases, and the crop is derived from UniProt domain annotation by a rule
   fixed in `code/panel.py` before any prediction.

Also set in the plan rather than the lead: AutoDock Vina cross-docking is declared out of scope (plan.md
§5.8), and two arms the lead did not ask for are added — an affinity-sampling arm (§5.4, prompted by
BoltzOmics' finding that within-drug correlation moves with sampling) and a training-support gradient
(§5.6, prompted by MIRAGE).
