# Deviations from the preregistration

## D1 — 2026-10-21 18:32 NZDT — reading the grid-exit data and the H4 specification (before any panel was built)

Found while checking file formats, before `build_panel.py` was run:

1. **Flow direction.** EMI names metered flows from the grid's side. `Grid_export` (flow X) is energy leaving the grid
   into a network, the networks' offtake; `Grid_import` (flow I) is energy entering the grid from a network (embedded
   generation spilling upstream). Plan section 2 said "net offtake = import − export"; it is **export − import**. The
   Grid_import files hold only about half the grid exit points, which is how this showed up.
2. **Points included.** Only grid-exit points of connection (generation type GN) are summed; grid-connected generators
   (GG) and directly connected consumers (GD) carry their own codes and are not network offtake. The code BOPD (one
   point, Matahina, in Horizon's region) is not one of the 29 distributors and is left out.
3. **File schema.** Column names are upper case to 2019 and mixed case from 2020, and the date format changed; both
   are read.
4. **H4 specification.** Section 3 lists "ICPs" among H4's controls while also saying all slopes are estimated in
   per-ICP form. H4 is estimated per ICP, weighted by ICPs, as for H1–H3; the levels form with ICPs as a control is
   reported with the robustness set. ICPs for H4 come from the Authority's registry (ICPs with solar ÷ uptake rate),
   because summer 2025/26 falls in a disclosure year not yet published.
