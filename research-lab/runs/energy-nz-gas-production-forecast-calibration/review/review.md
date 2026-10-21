# Review of `energy-nz-gas-production-forecast-calibration` (draft at commit b53e197)

Reviewer: independent adversarial review, 2026-10-21. Everything below was checked against the files on disk; the
scripts and their outputs are under `review/reviewer_checks/` (list at the end). Line numbers refer to the draft at
b53e197.

## Verdict: **fix first** (do not publish as drafted)

The parsing, the pairing arithmetic, the bootstrap, the Wilson intervals and every number in the tables reproduce
exactly. The problem is upstream of the arithmetic:

1. **The study's central caveat is false, and it changes the result.** The Internet Archive holds the 1 January
   2025 and 1 January 2026 workbooks, and every vintage back to 2014, at
   `https://www.mbie.govt.nz/assets/Data-Files/Energy/petroleum-reserves/petroleum-reserves-1-jan-YYYY.xlsx`
   (status 200; captured 2025-06-09 for 2014–2025 and 2026-05-14 for 2026). `fetch.py` only ever queried three
   filenames under one other directory. The plan promised "every retrievable vintage"; the study used six of twelve.
2. **With the twelve archived vintages, the preregistered H1 rule returns Inconclusive, not Supported**, and the
   headline pattern ("the gap widens the further ahead they look") disappears: the 2015–2018 vintages were close to
   calibrated at every horizon. The large errors are a feature of the 2019–2022 vintages meeting the post-2020
   decline, not of forecast horizon.
3. **"The totals are not systematically overstated, but the schedule is" is unsupported** by an Inconclusive H2, and
   is contradicted by the PJ-weighted revisions, which the plan promised to report and the draft omits: 2P ultimate
   recoverable was revised *up* in every vintage pair to 2021→2022 and *down* by 180–230 PJ in each of the four
   pairs since.

H2 (Inconclusive) and H3 (Supported) survive the extension to 2017→2026 and every tolerance/size variant I tried.

---

## Findings

### 1. The 2025 and 2026 releases (and 2014–2018) are in the Internet Archive — CRITICAL

**Claim under review.** `deviations.md` D1 §1 (L10–15): "the 2025 and 2026 releases … are published at URLs the
Archive has not captured. The two most recent releases are therefore outside this study". `report.md` L30–32 ("The
caveat that matters most … The Internet Archive holds no copy of the 2025 and 2026 releases, because MBIE moved them
to URLs it never captured"), L180–181, L84–85 ("Seven distinct workbooks give six vintages").

**Evidence.** One CDX prefix query (`reviewer_checks/cache/cdx_reserves_2024_2026.json`) returns, with status 200:

| file | capture | bytes |
|---|---|---|
| `petroleum-reserves/petroleum-reserves-1-jan-2025.xlsx` | 2025-06-09 | 110,411 |
| `petroleum-reserves/petroleum-reserves-1-jan-2026.xlsx` | 2026-05-14 | 95,736 |
| `petroleum-reserves/petroleum-reserves-1-jan-2014.xlsx` … `-2024.xlsx` | 2025-06-09 | 79–157 KB |
| `petroleum-reserves/historical-gas-reserves-data.xlsx` (1 Jan 2005–2013 sheets) | 2026-01-02 | 126,424 |

I downloaded them (`reviewer_checks/cache/new_vintages/`, sha256 in `MANIFEST_reviewer.json`) and parsed them
(`new_vintages2.py`). They are what they claim: the 2025 workbook is "as at 1 January 2025" with a 19-field gas
profile 2025–2075; the 2026 workbook is "as at 1 January 2026" with an 18-field profile 2026–2060 and a Gas sheet
whose 2P remaining total is 742.6 PJ (arithmetic; MBIE's 731 is the probabilistic total). The new-URL 2019 file is
cell-for-cell identical to the study's 2019 vintage (311 cells, max diff 0.0).

The plan's three validation statements (§5), which the draft silently dropped, all reproduce from these files:
2025 profile for 2025 = 106.8 PJ vs 102.44 realised = **−4.1%** (MBIE: 107 PJ, −4.1%); 2026 vintage's 2026 = 85.3
vs 2025 vintage's 100.0 = **−14.7%** (MBIE: "15% below"); 2P remaining 742.6 vs 959.3 = **−22.6%** (MBIE: −23%).

**Why it was missed.** `code/fetch.py` L26–31 hard-codes one directory
(`nz-energy-quarterly-and-energy-in-nz/`) and three filenames. `logs/fetch.log` shows the CDX query for the gas web
table failing six times with HTTP errors and being logged as "CDX gave nothing" — a failure recorded as absence. No
query was ever made for other reserves URLs; the "never captured" statement was an inference from the old asset
serving the same bytes after August 2024.

**Fix.** Re-run the fetch against the `petroleum-reserves/` directory (one CDX prefix query finds them), add the
2014–2026 workbooks to the MANIFEST, re-parse (the 2014–2018 layouts differ: year headers stored as strings, a
combined "Gas and LPG" sheet with P90/P50/P10 labels in 2014, starred fields that include LPG in 2014–2016, no
profile sheet in 2014), rerun everything, and rewrite D1 and the report. Validation §5 must then be reported.

### 2. With all archived vintages, H1 is Inconclusive under the preregistered rule — CRITICAL

`reviewer_checks/new_vintages2.py` reruns the study's own measure (ε = 0.05, net basis, union rule, field-cluster
bootstrap with the study's seed) with the twelve vintages that carry a gas profile (2015–2026; field-level outcomes
to 2023, so 2015–2022 contribute at h = 1 and 2015–2020 at h = 3). Names in the older workbooks were mapped with the
study's table plus five name-only additions (Onaero → Turangi group, Greater Ngatoro → Ngatoro, "Turangi and Turangi
McKee Overthrust" → Turangi, Ahuroa → TarikiAhuroa, Puka/Moturoa → Others).

| vintages | h=1 median [field CI] | h=3 median [field CI] | h=4 | h=5 | h=6 | H1 rule |
|---|---|---|---|---|---|---|
| 2019–2024 (the draft) | +37% [+15, +83] | +49% [+15, +131] | +35% | – | – | Supported |
| 2015–2018 only | +12% [−1, +59] | +1% [−18, +22] | −2% | +6% | −1% | Inconclusive |
| **all, 2015–2024** | **+26% [+5, +62]** | **+13% [−2, +38]** | +6% | +6% | −1% | **Inconclusive** (m(3) < ln 1.15; CI includes 0) |
| all, gross basis | +13% [−2, +53] | +5% [−11, +35] | +1% | −4% | −1% | Inconclusive |

Per-vintage medians at h = 1: 2015 +11%, 2016 +4%, 2017 −5%, 2018 +35%, 2019 +10%, 2020 +68%, 2021 +49%, 2022 +41%.
At h = 3: +3%, −9%, −16%, +20%, +25%, +55%. National totals against the overview series, all vintages: h = 1 median
+18% (n = 10, one negative), h = 3 +15% (n = 8), h = 5 +12%, h = 7 +2%, h = 8 −4% — against the draft's +32%, +50%,
+44% (L11–13, L116–120).

One honest caveat on the extension: the older workbooks omit several small oil-field gas producers (Maari, Rimu,
Sidewinder, Surrey, Tui), so the preregistered union rule adds 13 forecast-zero pairs at h = 1 and h = 3. Without
them the all-vintage medians are +35% [+12, +68] and +25% [+3, +55] (`union_sensitivity.py`), which would pass the
rule — at roughly half the draft's magnitude and still with no growth beyond h = 2. Either way, the draft's verdict
line (L6), the +37%/+49% headline (L9–10), "the gap widens the further ahead they look" (L6), the figure F2 title,
and the plain-terms paragraph (L43–45) do not survive the data the plan said it would use.

**Fix.** Rerun on all vintages; report the vintage-window sensitivity (2015–2018 vs 2019–2024) as the main result,
because it *is* the finding: forecasts made before the 2020 decline were close to calibrated and those made during it
were not. State the union-rule sensitivity. Do not describe the error as growing with horizon.

### 3. "The schedule is optimistic, not the volumes" is unsupported and contradicted by the PJ-weighted revisions — MAJOR

`report.md` L22–25 ("The totals are not systematically overstated, but the schedule is"), L47–49 (plain terms:
"the problem is less 'there is less gas than we thought' and more 'it is not coming out as fast'"), F3's title
("revised down about as often as up").

- An Inconclusive H2 with a 39–61% interval cannot support "not systematically overstated". The draft half-concedes
  this at L24–25 and then asserts it anyway in the summary and the plain-terms section.
- The count-based share (plan §1) weights Surrey (0.34 PJ) the same as Maui (4,100 PJ). Plan §4 promised "the 2P,
  1P and 3P revision distributions, in PJ and relative terms"; the PJ view is absent. `recompute.py` gives the net
  2P ultimate-recoverable revision by vintage pair, study window: **+226, +108, +60, −198, −177 PJ**; extended
  (`new_vintages2.py`): 2017→18 +73, 2018→19 +303, 2019→20 +226, 2020→21 +242, 2021→22 +60, **2022→23 −198,
  2023→24 −177, 2024→25 −233, 2025→26 −107**. 3P: −284, −502, −371, −222 in the last four pairs. The sign count is
  ~50% throughout, so the test the plan chose is blind to a regime change in which every large field (Mangahewa
  −178 PJ in 2022→23, Maui −76, Kapuni −53, Pohokura −33, Turangi −28) has been cut in each recent year, and the
  2026 release cut 2P by 23%.

**Fix.** Report the PJ-weighted revisions by vintage pair as preregistered; delete or reframe the "schedule not
volumes" reading as a hypothesis the sign test cannot address; retitle F3.

### 4. Provenance: nothing of the data is committed, and the national series has no provenance — MAJOR

- `.gitignore` L139/L143 exclude `research-lab/runs/*/data` and `logs`; `git ls-files` shows no data file, no
  MANIFEST and no log in the repository. `report.md` L208 ("Raw inputs are Internet Archive raw copies listed with
  their sha256 in `data/raw/MANIFEST.json`") describes a file that is not in the record.
- The MANIFEST covers only `reserves/` and `gas/`. The energy overview (`mbie_other/energy-overview_20260917134627.xlsx`),
  which supplies the only 2024–2025 outcomes and therefore the largest national errors (+101%, +82%, +67%), the energy
  balance, and the GIC file have no URL, hash or fetch code anywhere. `data/raw/gas/20260902050342.xlsx` is on disk but
  absent from the MANIFEST (it is an empty web-table shell like the 2026-04 capture).

**Fix.** Record URL/capture/sha256 for every raw file; commit the MANIFEST and the tidy CSVs (or their hashes in
`results/`); describe how the overview file was obtained.

### 5. The union rule is not implemented as preregistered; two material cells are dropped — MODERATE

Plan §3: a cell enters "if the field appears in that vintage's profile **or** has realised production that year".
`analysis.py` L81 skips a realised cell when the field is in the vintage but its cell for that year is blank
("field known to that vintage but not that year"). A blank profile cell is a forecast of zero (the workbooks' Total
rows sum it as zero). The two material cases are Maui from the 2019 vintage, whose profile ends in 2021: Maui
produced 27.5 PJ in 2022 and 38.2 PJ in 2023 (`recompute.py`). Adding them (`extra_checks.py` (a)): h = 3 median
+49% → **+43%**, h = 4 +35% → +27%. The verdict within the study window is unchanged; the deviation runs in the
hypothesis's favour and is unreported. Conversely the six union pairs the draft does add (L98–99, "counts against the
hypothesis") are five Surrey cells of 0.001–0.002 PJ and one Rimu cell of ~0 — cosmetic.

### 6. The field map misplaces Kauri; "Rimu under-forecast by 62%" is an artefact — MODERATE

`report.md` L137–140 and L188–189. MBIE's Gas.xlsx publishes "Rimu" (no Kauri row); the 2019 workbook's own LPG
block lists "Rimu/Kauri" as one entry; Kauri gas is processed through the Rimu station. The map (`parse.py` L37)
sends Kauri and "Kauri & Manutahi" to "Others". `extra_checks.py` (d): at h = 0 the workbook forecasts Rimu ≈ 0.01 PJ
and Kauri 0.13–0.38 PJ, while realised Rimu is 0.11–0.32 PJ and realised "Others" is **0.000** from 2021 on even
though the workbook forecasts 0.27–3.7 PJ for the fields mapped there. Rimu's "under-forecast" and a large part of
Others' "+3,462%" are the same misallocation seen from both sides. Both are small fields, so the medians move
little (excluding Others gives +27%/+41%), but the per-field narrative is wrong and the Greymouth fields
(Turangi/Kowhai/Ngatoro, shared facilities; Kowhai over-forecast even at h = 0 in every vintage) have the same
allocation ambiguity. **Fix:** group Rimu with Kauri on the forecast side (the plan allows grouped entries built from
names), say that a name-only map cannot resolve shared-facility allocations, and drop the per-field ranking or
label it as such.

### 7. The revision test keys on raw names and drops six 2020→2021 comparisons — MODERATE

`analysis.py` L198 keys ultimate-recoverable volumes by `field_raw`; between the 2020 and 2021 workbooks MBIE renamed
Turangi\*, Ngatoro\*, Maari\*, Cheal, Cheal E and Kauri/Manutahi to their grouped forms (`recompute.py`, "raw-name
matching"), so those six fields — including Turangi (2P UR ~550 PJ) — are silently excluded from that pair, contrary
to plan §3's harmonisation. With harmonised names (`extra_checks.py` (b)): 1P 32/74 = 43% [33, 55]; 2P 38/77 = 49%
[39, 60]; 3P 44/85 = 52%. Verdicts unchanged; the deviation should be fixed and the recovered pairs (Maari & Manaia
+179%, Cheal and Cardiff −44%, Turangi +23%) included.

### 8. Uncertainty is understated: the clusters are not the independent units, and the "24 comparisons" are neither 24 nor independent — MODERATE

- At a fixed horizon, clustering by vintage and by target year is the **same partition** (t = v + h). The
  "clustering by vintage rather than field" row (L135) prints only medians, which are identical by construction, and
  the text says "all hold" (L128). The intervals in `primary.json` for that variant come from 4 clusters at h = 1 and
  **2 clusters at h = 3**; a two-cluster percentile bootstrap has three possible resamples and "[+25%, +55%]" is just
  the two vintage medians. The field-cluster interval treats 18 fields as independent when every field shares the
  target-year shock (the draft admits this at L185–187 but keeps the field CI as the headline).
- The honest units are target years: 4 at h = 1 (vintage medians +10%, +68%, +49%, +41%; year-cluster CI
  [+12%, +52%]) and 2 at h = 3 (+25%, +55%). The MDE arithmetic (2.8 × SE, L122) is correct but uses the field-cluster
  SE, so "42%/61%" (L164) is also optimistic.
- L11–13, L125–127, L43–44 and L166: "every one of the 24 vintage-and-horizon comparisons". `national_pairs.csv` has
  27 rows (all positive on the net basis); 21 have h ≥ 1; "24" is h ≤ 4, which includes three part-observed h = 0
  nowcasts and excludes three h ≥ 5 rows. They are 6 vintages looking at 7 overlapping target years, not 24 pieces of
  evidence. On the **gross** basis 4 of 15 national comparisons are negative (2019 vintage, h = 1: −0.4%), the h = 3
  median is +14.5% (below the 15% bar) and h = 4 is +3.9% (`recompute.py`); the draft does not mention this.
- Volume-weighted over the *same* field-years as the medians, the error is +22% at h = 1 and +33% at h = 3 (net),
  +16%/+27% gross: the medians are dominated by small fields.

**Fix.** Report year-cluster intervals (or a vintage-level analysis) as primary; correct the count; present gross and
net national errors side by side.

### 9. The basis question is settled by assertion — MODERATE

`report.md` L91–93 and D1 §4 call net "the headline basis, as in MBIE's own comparison". The workbooks' Notes state
only unit conversions; nothing says whether operators report wellhead or sales gas. The ultimate-recoverable identity
(UR change = remaining-reserve change + year's production) cannot discriminate (`extra_checks.py` (c): summed
|residual| 163.7 PJ with gross production vs 165.6 with net). The identification of the overview line as the **net
production** series is correct (Gas.xlsx footnote 3 defines net = gross − flared − reinjected − LPG; the overview
equals the Gas.xlsx net header to the PJ in 2017 and 2019–2023; 2018 differs by 2.25 PJ because the overview is a
later revision). But D1 §4's reasoning — "labelled gross petajoules, but it reproduces … net production" — conflates
the *gross calorific value* unit convention printed on every MBIE table (including the net-production block) with
gross production; please correct the sentence. Within the study window H1 passes on gross at field level
(+31%/+39%), so the verdict did not hinge on the basis; the national numbers do (finding 8).

### 10. H3's interpretation goes beyond what a revision count can say — MODERATE

`report.md` L18–20 ("far above the 10% a genuinely 90%-confident estimate implies"), L51–53, L156–157. A calibrated
P90 means at most ~10% of fields end *below* their 1P estimate; it does not bound the frequency of downward annual
revisions, which also follow development-plan changes (Pohokura 1P −7% and −8% in 2019→20 and 2020→21; Mangahewa
−10% in 2022→23). The preregistered 10% bar is a heuristic the plan chose, and the report should say so. The result
itself is robust: 44% at 0% tolerance, 34% [21, 51] at 5%, 45% for fields ≥ 10 PJ, 46% for fields ≥ 100 PJ, 47%
over 2017→2026 (`recompute.py`, `new_vintages2.py`). Phrase it as "1P is cut in roughly four field-years in ten
under every tolerance and size cut, which is not the behaviour of a one-way floor", not as a calibration test
of P90.

### 11. Preregistered outputs that are missing — MINOR

Plan §4: trimming the largest 5% of |e| (not implemented); the share of field-years with zero realised but positive
forecast and the reverse (not reported); error by vintage (not reported; see finding 8 for the numbers);
deliverability against realised (not reported); revision distributions in PJ (finding 3). Plan §5: items 1–3 dropped
without comment (finding 1); "each vintage's profile total … against MBIE's published national expectation" — L174
lists the totals and compares them with nothing. Plan §1 H2: "whether d reaches the lead's 0.60 is reported either
way" — in `primary.json` but not in the report.

### 12. Process and timing statements that are not accurate — MINOR

- `report.md` L197–198: "`analysis.py` [was] committed before the outputs [it] produced". `primary.json` committed in
  9ee7439 (20:56:03) already contains the `sensitivity` block; the code producing it was committed in b53e197
  (20:58:58). The H1 numbers are unaffected (the sensitivity draws come after the horizon loop in the RNG sequence),
  but the sentence is false.
- D1 L7: "Recorded … before any forecast was paired with an outcome". D1 was committed at 20:56:54, after the
  results (20:56:03), and the report itself (L201–202) says a first run had been done and double-counted the 2021
  vintage before D1's rule was added. Say "recorded after a first run, before the results were written up".
- D1 §2 "the later, more revised publication": the two 2021 captures carry **identical** gas profiles (351 cells) and
  reserves (verified, `cache/…`); say so. The 3ee755a fix also relabelled the overview series from gross to net after
  the first run; the evidence for net is sound, but the relabel should be listed as a post-hoc change.
- `parse.py` L169 docstring and `national.csv`'s column name still say "gross".

### 13. Smaller numeric and wording points — MINOR

- L133: excluding Others at h = 1 is **+27%** (27.47), not +28%.
- L137–140: Tui +1,300%, Ngatoro +257%, Kowhai +157%, Waihapa +108%, Maari +102%, Maui −21%, Rimu −62%, Mangahewa
  −5%, "fourteen of eighteen" all reproduce *as medians of three yearly log errors*; say so. By volume over the same
  years Maui is +3% (over-forecast) and Waihapa +1,089%. Tui's +1,300% is a receivership (Tamarind, late 2019), the
  clearest "plan change" case in the data; L182–184 should cite it.
- L116: h = 0 in the H1 table and F2 is a part-observed nowcast; the capture dates bound publication at Jan 2020
  (2019 vintage), Jan 2021, Dec 2021, Apr 2022–Jan 2023, Nov 2023, Aug 2024, Jun 2025, May 2026, and the 2021
  vintage's +0.3% national h = 0 error shows late-year information. This does **not** undermine h = 1 (a forecast
  for Y+1 formed during Y has, if anything, more information than a strict one-year-ahead forecast, which makes the
  optimism finding conservative), but "one year ahead" should be glossed as an effective lead of about 0.5–1.5 years.
- L171–173: MBIE revised realised 2019 net production from 177.9 PJ (2020–21 publications) to 184.3 PJ (2022 on);
  "latest capture wins" is the right choice and conservative; worth one sentence.
- F2: the "preregistered bars" annotation overlaps the x-axis labels; F3's title (finding 3).

---

## What was checked and found correct

- **Parsing (check 1).** Independent re-extraction of all seven workbooks (`reextract.py`): vintage years confirmed
  from the Gas-sheet titles (including `petroleum-reserves-2019.xlsx` = "as at 1 January 2020"); 2,231 profile cells
  and 151 reserve rows identical to `data/profiles.csv` and `data/reserves.csv`; the gas block ends at "Total" and the
  LPG block follows in every workbook; field sums equal the workbooks' Total rows to 0.0000 PJ in every year of every
  vintage; UR/RR PJ columns equal the arithmetic totals; no field dropped or double-counted. The Gas sheets' footnote 3
  changes wording in 2020 ("combined total of gas and LPG") but the data stay gas-only (the combined sheet differs).
- **Realised series (check 2).** Net identification correct (finding 9); gross/net field sums equal the Gas.xlsx
  headers; latest-capture rule verified.
- **Pairing (check 3).** My own implementation of the union rule reproduces all 516 pairs; the 6 union pairs are as
  claimed (and trivial).
- **Statistics (check 4).** Medians, field-cluster bootstrap intervals (replicating the RNG order), SEs, MDE = 2.8 × SE,
  the H1 decision, the share of positive errors (75.4%), and the revision counts 29/68, 36/72, 40/79 with Wilson
  intervals all reproduce to the digit.
- **Reserve tests (check 5).** Using ultimate recoverable rather than remaining + production is the right choice and
  the two are consistent (identity residuals < 2 PJ for all large fields except Kupe's 2020 entry, ±50 PJ).
- **Figures.** Consistent with the tables; `report.html` carries the same numbers as `report.md`.
- **Gas web tables.** The 2026-04 and the orphan 2026-09 captures contain no cached values, so field-level 2024
  outcomes really are unavailable from the recovered files.

## Scripts (all run with the CRL venv Python, `-I`)

`reviewer_checks/dump_structure.py` (workbook layouts → `cache/structure/`), `dump_realised.py`, `reextract.py`
(check 1; `cache/reextract_report.txt`), `recompute.py` (checks 3–5, 8; `cache/recompute_report.txt`),
`extra_checks.py` (findings 5–7, 9; `cache/extra_checks_report.txt`), `new_vintages.py` / `new_vintages2.py`
(findings 1–3; `cache/new_vintages2_report.txt`), `union_sensitivity.py` (finding 2). Downloads: one CDX query and
nine workbook fetches from web.archive.org, 3 s apart, in `cache/new_vintages/` with `MANIFEST_reviewer.json`.

---

## Confirmation pass

Revised study at commits b63d203 → b449f11, checked 2026-10-21 against the files on disk. Scripts:
`reviewer_checks/confirm_captures.py`, `confirm_stats.py`, `confirm_extra.py`; outputs in `cache/confirm_*.txt`.

### Verdict on the revision: **publish with edits** (minor; nothing requires another run)

The fetch, parse and analysis fixes are correct, every number in the revised report reproduces from the revised
tables, and the Inconclusive tag is the right call — for a reason that is stronger than the one the report gives.

### Each earlier finding

| # | finding | status |
|---|---|---|
| 1 | 2025/2026 and 2014–2018 editions not fetched | **Resolved.** 13 editions in `data/raw/reserves/` (81 captures, 20 distinct files); fetch searches both directories; a failed CDX query is recorded in `_failed_queries` and fatal; all three plan §5 statements reproduce (−4.1%, −14.7%, −22.6%). |
| 2 | H1 verdict an artefact of the six-edition window | **Resolved.** All editions used; "widens with horizon" withdrawn; F2 retitled; the fragility is stated. My +13% vs the study's +15.1% at h = 3 is the Kauri→Rimu and blank-cell choices, both now reported. |
| 3 | "schedule not volumes" | **Resolved** in the text (PJ table by edition pair; reading withdrawn). Residual: F3's title still says "revised down about as often as up" with no hint of the turn in volumes — retitle or add the PJ turn to the caption. |
| 4 | provenance | **Resolved** for the inputs: `MANIFEST.json` now has an `other` group with URL and sha256 for the energy overview, energy balance and GIC files; all three hashes match the files on disk; the two MBIE files were re-downloaded from exact captures. Still true that `data/` and the MANIFEST are gitignored, so the record the report points to (L243–244) is not in the repository; commit the MANIFEST or copy its hashes into `results/`. |
| 5 | blank cells skipped | **Resolved.** Blank cells in listed fields are zero forecasts within the edition's own horizon; 106 union-rule pairs (71 absent fields, 35 blank cells). The remaining asymmetry — a blank cell with zero outcome is excluded, an explicit zero cell with zero outcome (2017/2018 workbooks) enters as e = 0 — involves 2 and 4 cells and moves nothing (h = 3 without the four: +16.1% [+0.4, +42.9]). |
| 6 | Kauri mapped away from Rimu | **Resolved.** Residual judgement call: the 2015 edition's "Onaero" is sent to Others, though the later workbooks' own footnote places Onaero in the Turangi group; moving it changes h = 1 to +27.1% and leaves h = 3 at +15.1% (`confirm_stats.py`). Either is defensible; say which and why. |
| 7 | revisions keyed on raw names | **Resolved.** Harmonised fields, raw names summed within an edition, Others excluded. |
| 8 | clustering, "24 comparisons", gross national | **Resolved.** Cluster-by-edition now carries intervals (6 clusters at h = 3) and reads Inconclusive; the by-edition table shows the year-shock structure; gross national errors reported (+7.8%, +5.4%, −1.1%); the "24" claim is gone. |
| 9 | basis settled by assertion | **Resolved.** Gross alongside net; the series is called net; D1's "labelled gross … but" sentence survives only as superseded history. |
| 10 | H3 over-interpreted | **Resolved** (L181–184). The report says the tolerance/size check "was not repeated on all editions"; it is now: 1P revised down 44% at 0% tolerance, 43% at 1%, 33% [24, 45] at 5%; 43% for fields ≥ 10 PJ and ≥ 100 PJ; 47% [37, 56] over 2017→2026 alone (`confirm_extra.py`). The report may cite these. |
| 11 | missing preregistered outputs | **Resolved** except deliverability, which D2 §6 states was not done. |
| 12 | process statements | **Resolved.** The false "code before outputs" sentence is gone; D2 records the sequence. |
| 13 | numeric slips | **Resolved.** Every quoted number re-derived (see below). Maari by volume rounds to −24% in my computation against the report's −25%; immaterial. |

### The new parse and analysis

- **Re-captures.** "Latest capture wins" now selects 2025-06-09 or 2026-01 captures for the 2019–2024 editions. I
  compared every multiply-captured edition cell by cell: 0 differing profile cells and 0 differing reserve rows in all
  seven comparisons (`confirm_captures.py`). The report (L90) could say the captures are identical.
- **2014–2016 gas-only table.** The "Gas and LPG" sheet carries "Natural Gas and LPG Reserves" first and "Natural Gas
  Reserves" second; the parser takes the second, and `reserves.csv` has Kupe 1P = 249.6 (2015), 247.9 (2016), 335.8
  (2017) — gas-only, as stated. Year headers stored as text, the leading blank column and the P90/P50/P10 labels are
  handled; the 2017 and 2018 profiles read explicit zeros (700 and 684 cells), which is correct.
- **Statistics.** Replicating the RNG order from `pairs.csv`: h = 0…5 net +12.6, +27.5, +24.4, +15.1, +6.0, +6.0%
  with intervals [+3.2, +34.0], [+9.1, +60.9], [+6.3, +64.0], [+0.7, +41.2], [−11.2, +28.9], [−17.5, +39.7]; gross
  +5.8, +15.3, +14.9, +8.3, 0.0, −3.5%; MDE 35.7% / 33.8%; by volume +14.9% / +12.0%; by edition at h = 1 (+0.6, +4.1,
  +14.8, +34.7, +11.5, +76.6, +48.9, +41.5%); by field (Pohokura +19/+24, Mangahewa −5/−1, Maui −1/−2, Kupe −2/+3,
  Turangi +29/+34, Kapuni +12/+19, Kowhai +108/+91, McKee +69/+65, Ngatoro +172/+172; 11 of 18 over on the median);
  zero shares 5.6% / 16.6%; national net +4.4, +17.8, +18.0, +15.4, +8.9, +12.3%; revisions 60/138, 71/142, 85/155
  with the stated Wilson intervals; the 2P PJ table to the PJ; first-year totals; the three MBIE statements. All
  reproduce exactly. The rule's margin at h = 3 is 0.0012 in log terms (0.1 point), as stated.

### The Inconclusive tag

Agree, and the report should give the stronger reason. The preregistered rule needs the h = 3 interval to exclude
zero. With the preregistered seed the lower bound is +0.67%; over 20 other seeds at B = 2,000 it ranges from −0.62%
to +0.68% and **15 of 20 seeds would read Inconclusive**; at B = 20,000 with the study's seed it is +0.00%
(P(draw ≤ 0) = 0.026). The pass is therefore inside the bootstrap's own Monte Carlo error, on top of the 0.1-point
median margin. The seed was fixed in advance, so "Supported by its rule" is a legitimate statement of what the
preregistered procedure returned; but a test whose outcome flips with the random seed cannot carry a one-word
Supported, and the FAERS precedent applies cleanly. Suggested wording for L11–14 and L216–217: "the three-year median
clears its bar by 0.1 point and its interval's exclusion of zero depends on the bootstrap seed (lower bound −0.6% to
+0.7% across seeds)". The one-year result is robust in every variant and should stay the headline of what *is* shown.

### Anything new

- **F3 title** (above): the only place the withdrawn reading still shows.
- **2014 edition methodology.** Six fields in the 2014 gas table (Kowhai, Ngatoro, Onaero, Cheal, Moturoa, Surrey)
  are footnoted "a reserve depletion method has been applied", so their 2014→2015 revisions partly reflect a change
  of method. Verdicts do not depend on it (H3 over 2017→2026 alone: 47% [37, 56]); one clause in the report suffices.
- **2015–2016 profile basis.** Those editions' reserves mark starred fields "includes LPG"; whether their gas
  *profiles* also include LPG cannot be read from the workbooks (the 2016 sheet has a separate LPG block, the 2015
  sheet does not). The h = 0 national errors of +2% and +1% suggest gas-only. State it as unverifiable.
- **Gitignored record** (finding 4): unchanged.

Nothing else is wrong that I could find. The report's plain-terms section now matches the results.
