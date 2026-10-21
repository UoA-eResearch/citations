# Independent review: energy-nz-embedded-solar-edb-demand

Reviewer: Fable 5.1 (adversarial, independent), 2026-10-21. Scripts and their output are in `review/reviewer_checks/`
(`check_emi.py`, `check_ea.py`, `check_panel_h4.py`, `check_units_tp.py`, `check_misc.py`, `check_solar_geometry.py`; each has a matching `.out`).
All run with the designated venv Python `-I`; nothing outside `review/` was changed.

## Verdict: **fix first**

The preregistered H4 verdict ("Supported" by the stated rule) stands arithmetically, but the report misdescribes what
produced it and promotes the wrong exploratory number. Three things must change before publication: (i) H4 is
identified almost entirely by two small rural units that each added a solar farm, and it is not Supported without
them; (ii) the headline attributes to "rooftop solar" an effect that comes from the farms, while the rooftop component
is Inconclusive; (iii) the "best estimate" (midday minus evening, −0.35) subtracts real solar output, because
18:00–21:00 NZDT is not a no-production window in a New Zealand summer. H1–H3 (Inconclusive, underpowered) and the
data corrections D1–D2 check out.

## Findings

### 1. Major — H4 rests on two solar-farm units; "stable when any one network is left out" is misleading

- EA Networks (EASH) and Top Energy (TOPE) supply **81%** of the ICP-weighted within-unit, within-summer variance of
  the exposure (EASH 54%, TOPE 28%; next is Vector at 5%). In 2025/26 they carry 3.3 and 2.4 kW of solar per ICP
  against 0.1–0.6 for every other unit (`check_panel_h4.py`).
- Dropping both: **−0.48 (−1.31 to +0.19)**, not Supported. Dropping the seven units with farms (EASH, TOPE, MARL,
  HEDL, NPOW, ORON, POCO): −0.05 (−1.45 to +0.55).
- The published interval is a mixture (`check_misc.py`, same seed and scheme, reproduces −1.009/−0.158 exactly):
  13% of bootstrap draws contain neither unit, and those draws have median −0.47 and run from −1.25 to +0.16; draws
  containing both have median −0.87 (−0.98 to −0.77). The upper bound −0.16 is entirely the no-farm draws. With two
  effective identifying clusters, the percentile interval and the MDE (0.55 = 2.8 × a mixture SE) are not reliable
  summaries of uncertainty.
- report.md "stable when any one network is left out (−0.90 to −0.72)" is literally true (each unit is dispensable
  alone) and misleading (together they are the identification).

**Fix.** Say plainly that H4 is identified by two units that each commissioned a solar farm (Lauriston, 48 MW,
Nov 2024; Kaitaia and a second step, 24 MW each, Nov 2023 and Sep 2025); report the drop-both and farm-free variants in
the H4 table; delete "stable"; state the verdict as "Supported under the preregistered rule, but identified from two
solar-farm units and not detectable without them".

### 2. Major — the report credits rooftop solar with an effect that comes from solar farms

- Exposure split in the same H4 model (`check_panel_h4.py`): behind-the-meter only **−1.49 (−2.67 to +0.24)**,
  Inconclusive; industrial (farm) segment only −0.96 (−1.27 to −0.11); both together, behind-the-meter −0.51 (−1.89 to
  +0.54), industrial −0.90 (−1.04 to −0.08). The rooftop component is not separately detectable.
- Yet the title is "What rooftop solar has done…", and the plain-terms section says "Rooftop solar is spreading fast
  … each megawatt of panels cuts summer midday demand on the grid by about a third to half a megawatt". plan.md's
  own title also says rooftop solar while H4's exposure is all distribution-connected solar.

**Fix.** Title and plain terms: "distributed solar, mostly the new solar farms". Add the split to the H4 table and a
sentence that the rooftop effect is Inconclusive at this sample size.

### 3. Major — the midday-minus-evening "best estimate" subtracts real solar output

- 18:00–21:00 NZDT in December–February is daylight for most of the window. Sun elevation at 18:00 NZDT is 26–35°
  (Auckland to Invercargill); a clear-sky plane-of-array proxy (north-facing, 25° tilt) gives evening-window output at
  **20–46%** of the midday-window output (`check_solar_geometry.py`). Under H4's own hypothesis the evening slope
  should therefore be about −0.1 to −0.3 MW per MW from solar alone; the observed −0.49 is partly solar, and the
  contrast removes it. The sentences "hours when panels produce nothing" (report.md, verdict bullets and "The placebo
  did not come back clean") and "Networks adding solar fastest also drew less from the grid at hours when panels
  produce nothing" are wrong for the evening window.
- The night window (02:00–05:00) is clean of solar output. Midday minus night: −0.51 (−0.56 to −0.25); without EASH
  and TOPE, −0.33 (−0.61 to −0.06); midday minus evening without them, −0.31 (−0.55 to −0.13). The contrasts are the
  most robust numbers in the study, but the evening one is biased toward zero by construction.
- The contrast was chosen after the placebo (D4). Calling a post hoc contrast "the study's best estimate" and
  building the plain-terms figure ("a third to half") on it inverts the preregistration.

**Fix.** Lead with the preregistered −0.84 and finding 1's fragility; keep the night placebo (−0.33, interval
including zero) as the warning; present midday-minus-night as the exploratory contrast, with its own confounds named
(night EV charging and controlled hot water, irrigation pumping, battery discharge); drop "best estimate"; replace
"a third to half" with a range that spans the preregistered and netted numbers, or quote only the night contrast.

### 4. Moderate — pre-trend and embedded-generation confounds are present and not reported

- A lead-2 placebo (preregistered for H1–H2, not run for H4): solar two summers ahead, alongside current solar,
  takes midday −0.22 (−0.87 to +0.01) and night **−0.26 (−0.97 to −0.03)** (`check_panel_h4.py`). Units that later
  added solar were already drawing less, especially at night.
- The TOPE unit has been a **net injector** into the grid since summer 2020/21: midday offtake 19–22 MW to 2019/20,
  then +2, −8, −9, −22, −29, −46 MW; night +3 to +5, then −15 to −27 MW (`check_units_tp.py`). The step is Top
  Energy's own Ngawha geothermal expansion (non-solar DG in the registry 33 → 73 MW in 2020). Within TOPE, offtake
  steps down in 2020 and solar steps up in 2023 and 2025, which yields a negative slope at every hour. The report
  does not mention that one of its two identifying units has negative "offtake".
- Adding non-solar DG per ICP as a control, as H1 does, gives midday −0.80 (−1.03 to −0.31), evening −0.44 (−0.68
  to +0.03), night −0.28 (−0.59 to +0.12): it does not cure the placebo, but H4 should carry the same control as H1
  and say so.

**Fix.** Add the lead placebo and the non-solar DG control to the H4 table; disclose TOPE's net-injection status
and EASH's irrigation load (night offtake 98 → 76 → 60 MW over 2023/24–2025/26) as the concrete sources of the
placebo signal.

### 5. Moderate — plan section 4 applied to H4 selectively

D3 says section 4 "applies to H4 as well" but adds only leave-one-out and first differences. The jump filter
(drop unit-summers with |Δlog outcome| > 0.15) gives −0.78 (−1.26 to +0.21). For H4 that filter is a poor test,
because it removes the farm years themselves (EASH 2024/25 and 2025/26, HEDL 2025/26, TOPE 2020/21); the report should
say that rather than omit it. First differences (−0.58, −0.86 to +0.43) already fail the rule and deserve a sentence.

### 6. Minor — exposure segments and exclusions

- Behind-the-meter (Res + Com) contains farm-sized single-month steps: TOPE Commercial +20.0 MW (May 2025), POCO
  Residential +11.5 MW (Nov 2023), WAIP Residential +9.3 MW and ORON Residential +8.9 MW (Jul 2025)
  (`check_misc.py`). Industrial does hold the large farms (EASH +48.3 Nov 2024, TOPE +23.7 Nov 2023 and +24.0 Sep
  2025, NPOW +17.0 Dec 2024, HEDL +23.8 Aug 2025), but the segment split is not clean. Res + Com + Ind = All within
  ±1.6%, so the segments partition and SME is cross-cutting, as the plan says. H2–H3 are Inconclusive regardless.
- Excluded embedded-network participants hold 11.5 MW of 1,277 MW (Sep 2026), physically on the parent networks
  (mostly Vector). Negligible; say so in one line.
- All 29 participant codes map to the right distributors; no exposure is missing in the annual panel.

### 7. Minor — process

- plan.md fd5d815 (18:17) precedes the code (7879594, 18:19) and the first results (2e2e76e, 19:35). D1 and D2 were
  committed before the panel and before any estimate, as claimed. The bootstrap rewrite left primary.json unchanged.
- D3's code was committed in the same commit as the first results (its outputs came later, fine). **D4's code and
  its outputs were committed together** (8f12116), so "code preceded its outputs" does not hold for D4. Log it.
- The Commerce Commission and EA files were downloaded (18:08–18:12) before the plan was committed; the plan declares
  what was looked at. Nothing more can be verified from the repository.

### 8. Minor — wording and numbers

- Every number in report.md and report.html matches primary.json and robustness.json; the installed-solar table
  (17/19, 102/110, 363/489 MW; 31,305 / 32,574 / 33,583 GWh) matches panel_annual.csv.
- "roughly half to three-fifths of the midday slope" is 0.39 and 0.58: "two-fifths to three-fifths".
- The H4 MDE (0.55) and the asymmetric interval should be flagged as artefacts of finding 1.
- "could not have succeeded" (H1–H3) is fair for this design (MDE 8, 18, 2.8 against 1.2, 0.5, 0); write "with the
  disclosed totals" rather than implying no annual design could work.

## Checks that passed (brief items the brief asked for)

- **Accounting.** Net grid supply = "entering system" − "supplied from DG" equals GXP in − GXP out − net transfers to
  other EDBs; it differs from gxp − gxp_export by about 93 GWh/yr for Network Tasman (supply passed to Nelson
  Electricity), and the chosen definition is the right one for a per-ICP outcome. The H2 self-consumption logic is
  right. Moving the lead's 1.0 GWh/MW to grid supply was done in plan.md with the accounting shown, before any outcome
  series: legitimate preregistration.
- **D1 direction.** Grid_export files are all flow X and hold HAM0331 (WEL, 224–244 MWh per midday window, about
  75–80 MW); Grid_import files are flow I and their GN points are embedded generators (Ngawha KOE1101/TOPE, Kinleith
  KIN0112/POCO, WRK0331 and TAB0331/HAWK, Matahina MAT1101/BOPD). Export − import is right. No duplicate POC-date rows.
- **Trading periods.** Northpower's Dargaville farm injection (MTO0331) and the Huntly-area GXP (HLY0331) peak at
  TP28 (13:30–14:00 clock), where solar noon falls in NZDT; under NZST the peak would sit at TP26. TP25–30 is
  12:00–15:00 local summer time.
- **D2.** Registry ICPs are justified (uptake rate carries five decimals; the Westpower 2024 ratio is wrong) and the
  disclosure-ICP variant changes no verdict (H1 −2.53, H2 −0.05, H3 +0.56).
- **Merged units** follow shared POCs in the metered data; the non-distributor codes at shared points (NZ Steel at
  GLN0332, Winstone at TNG0111, LLNW at FKN0331) are correctly left out. Every unit-summer has 90 or 91 days.
- **Weighting.** Unweighted (−0.89) and weighted (−0.84) agree; the Powerco-dominated LINE unit is not the issue.
- **Power.** 2.8 × SE is the standard 80%-power, 5% two-sided formula.
