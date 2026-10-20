# Are New Zealand's gas production forecasts systematically optimistic?

*Six vintages of the production profiles that field operators report to MBIE, recovered from the Internet Archive
and compared, field by field and year by year, with the gas that was actually produced.*

**Verdict: Supported.** The forecasts are optimistic, and the gap widens the further ahead they look.

- **H1 (over-forecasting that grows with horizon): Supported.**
  - Across fields, the median profile exceeds realised production by **37% one year ahead** (95% CI +15% to +83%)
    and by **49% three years ahead** (+15% to +131%), against preregistered bars of +5% and +15%.
  - At the national level the pattern is cleaner still: **every one of the 24 vintage-and-horizon comparisons is
    an over-forecast**, from +0.3% to +101%. The median national error is +32% one year out, +50% at three years
    and +57% at four.
  - 75% of individual field-year forecasts one year ahead are too high.
- **H2 (reserve volumes are overstated): Inconclusive.** Between consecutive vintages, the proved-plus-probable
  (2P) ultimate recoverable volume was revised **down in exactly half** of the 72 field-years that moved by more
  than 1% (95% CI 39–61%). There is no sign of a one-way bias in the volumes themselves.
- **H3 (the proved category is not conservative): Supported.** The proved (1P) ultimate recoverable volume was
  revised down in 43% of field-years (29 of 68; 95% CI 32–54%), far above the 10% a genuinely 90%-confident
  estimate implies.

**What that combination means.** The totals are not systematically overstated, but the schedule is: operators
expect the gas sooner and faster than it arrives. The shortfall looks like optimism about rate and timing rather
than about how much gas exists. With 72 field-years and wide intervals, that reading is suggestive rather than
settled.

**One number for the scale of it.** The workbook published as at 1 January 2022 forecast **206 PJ** of gas for
2025. New Zealand produced **102 PJ**.

**The caveat that matters most.** The Internet Archive holds no copy of the 2025 and 2026 releases, because MBIE
moved them to URLs it never captured. This study therefore covers the vintages from 2019 to 2024 and **not** the
two most recent releases, including the one that cut 2P reserves 23% to 731 PJ.

## In plain terms

New Zealand is running short of natural gas, and faster than expected. Each year the companies that own the gas
fields tell the government how much they expect to produce for the next fourteen years. Those forecasts feed into
decisions about electricity supply, about big industrial users, and about whether the country needs to import gas.

We found six past copies of those forecasts in a web archive, going back to 2019, and compared each with what the
fields actually produced.

The forecasts were consistently too high. Not once in 24 comparisons did the country produce as much as the
forecast said. One year ahead, the typical forecast was about a third too high. Three years ahead, about half too
high. The 2022 forecast for 2025 was double what was actually produced.

Oddly, the companies' estimates of the *total* gas left in each field were not one-sided: they were revised down
about as often as up. So the problem is less "there is less gas than we thought" and more "it is not coming out as
fast as we said it would".

One exception is worth noting: the "proved" category, which is supposed to be a conservative floor that is
exceeded nine times out of ten, was revised downward in more than four cases in ten. It is not behaving like a
floor.

Anyone planning against these profiles should expect less gas, sooner than the numbers suggest.

## What was asked

Under the Crown Minerals Act, field operators file an annual summary report with MBIE giving their remaining
reserves and a roughly fourteen-year expected production profile. MBIE publishes these as the petroleum reserves
workbook. The profiles feed MBIE's gas outlooks, the system operator's security-of-supply work, and commercial and
policy decisions.

The study asks three preregistered questions (`plan.md`):

- **H1:** do the profiles exceed realised production, and does the gap grow with horizon?
- **H2:** are proved-plus-probable (2P) volumes revised down more often than up?
- **H3:** is the proved (1P) category behaving as a conservative floor?

## What was already known

MBIE reports shortfalls descriptively. *Energy in New Zealand 2026* notes that 2025 net production was 102 PJ,
4.1% below the 107 PJ profile published in June 2025, and the May 2026 release notes that 2P reserves fell 23% to
731 PJ with the 2026 profile 15% below the previous year's. A TIMES-NZ methodology page reproduces an MBIE chart
comparing profiles with outcomes for 2020–2025 and observes that actual production "often fell short".

The international literature on overconfidence in petroleum estimates (Capen 1976; Bratvold and Begg) is not about
New Zealand. No horizon-resolved, field-level calibration of these profiles, and no test of whether the
probabilistic reserve categories are calibrated, was found (searches 2026-10-20).

## How it was done

**The forecasts.** Every retrievable vintage of MBIE's petroleum reserves workbook, taken from Internet Archive
raw copies because MBIE's own site refuses scripted downloads. Seven distinct workbooks give **six vintages, as at
1 January 2019 through 1 January 2024**; the 2021 workbook was published twice and the later version is used (D1).
The vintage is read from the text inside each workbook, never from the capture date. Each gives a gas production
profile by field, in petajoules, running about fourteen years ahead.

**The outcomes.**
- **By field:** MBIE's gas data tables, gross and net production per field, 1974–2023.
- **National:** MBIE's energy overview, to 2025. That series reproduces the sum of the published field-level net
  production to within 0.05 PJ in every overlapping year, and its 2025 value (102.4 PJ) matches the 102 PJ MBIE
  published, so it is the net series (D1). Net is the headline basis, as in MBIE's own comparison.
- **Cross-check:** Gas Industry Co's daily production for the four field groups it publishes.

**Matching.** The workbooks name more fields than MBIE publishes, so the finer names are mapped onto MBIE's
published fields by a table written from the two name lists alone and committed before any pairing. Fields without
a published counterpart fall into MBIE's "Others" residual. A field enters the analysis if it was forecast **or**
produced, so a field that produced without being forecast counts against the hypothesis rather than being dropped.

**The measure.** For vintage *v*, field *f* and year *t*, the error is ln((F + ε)/(A + ε)) with ε = 0.05 PJ fixed in
advance; positive means over-forecast. The horizon is h = t − Y(v). The headline statistic is the median over
(vintage, field) pairs at each horizon, with a field-cluster bootstrap (2,000 resamples). Because the field-level
outcome series ends in 2023 and the national one in 2025, the national comparison reaches further out.

**Reserve calibration.** Rather than relying on a production series, the reserve tests use the **ultimate
recoverable** volume, which should change between vintages only through genuine re-estimation. Among field-years
that moved by more than 1%, the share revised downward is compared with what each category implies.

## Results

### H1: the forecasts are too high, and increasingly so (`results/tables/by_horizon.csv`)

| years ahead | median field-level error | 95% CI | vintages | national total error |
|---|---|---|---|---|
| 0 (part-observed) | +21% | +2% to +40% | 5 | +9% |
| **1** | **+37%** | **+15% to +83%** | 4 | +32% |
| 2 | +48% | +14% to +92% | 3 | +39% |
| **3** | **+49%** | **+15% to +131%** | 2 | +50% |
| 4 | +35% | −1% to +167% | 1 | +57% |

The preregistered rule asks for +5% at one year and +15% at three, with intervals excluding zero. Both hold, so
**H1 is Supported**.

- **Every national comparison overshoots.** Across the 24 (vintage, horizon) pairs with a realised outcome, the
  error runs from +0.3% (the 2021 vintage's view of 2021) to +101% (the 2022 vintage's view of 2025). None is
  negative.
- **The sensitivities preregistered in the plan all hold** (`primary.json`, `sensitivity`):

  | variant | 1 year | 3 years |
  |---|---|---|
  | preregistered | +37% | +49% |
  | excluding the "Others" residual | +28% | +41% |
  | only fields producing above 0.5 PJ | +50% | +54% |
  | clustering by vintage rather than field | +37% | +49% |

- **It is not uniform across fields.** Over horizons 1–3 the most over-forecast named fields are Tui (+1,300%,
  which stopped producing), Ngatoro (+257%), Kowhai (+157%), Waihapa (+108%) and Maari (+102%); the largest field,
  Maui, was **under**-forecast by 21%, as was Rimu by 62% and Mangahewa by 5%. Fourteen of the eighteen fields
  were over-forecast on balance.

![Profiles against realised production](results/figures/F1_profiles_vs_realised.png)

![Error by horizon](results/figures/F2_error_by_horizon.png)

### H2 and H3: the volumes are even-handed, the proved category is not (`results/tables/revisions.csv`)

| category | revised down | share | 95% CI | what calibration implies |
|---|---|---|---|---|
| proved (1P) | 29 of 68 | 43% | 32–54% | rarely down (about 10%) |
| proved + probable (2P) | 36 of 72 | 50% | 39–61% | about half |
| proved + probable + possible (3P) | 40 of 79 | 51% | 40–61% | often down |

- **H2 is Inconclusive**: the 2P interval straddles 50%, so no one-way bias in the volumes is detected, and none is
  ruled out either.
- **H3 is Supported**: a proved volume that is exceeded nine times in ten should rarely be cut, and this one is cut
  in more than four field-years in ten.
- **3P behaves like 2P**, which is not what a 10%-probability upper case implies, though the interval is wide.

![Reserve revisions](results/figures/F3_reserve_revisions.png)

### Power

The minimum detectable effect, from the bootstrap standard errors, is about **42%** at one year and **61%** at
three. The measured effects (+37% and +49%) sit near those limits, which is why the intervals are wide even though
the direction is unambiguous. The direction rests on 24 national comparisons that all point the same way; the
*size* is imprecise.

### Validation (`primary.json`, `validation`)

- National net production reproduces MBIE's published 2025 figure: 102.4 PJ against 102 PJ.
- The national series matches the sum of published field-level net production to within 0.05 PJ in 2019–2023.
- Gas Industry Co's four published field groups track the same decline (121.7 PJ in 2018 to 72.1 PJ in 2025).
- First-year profile totals: 192 PJ (2019 vintage), 189, 158, 189, 167, 139 (2024).

## What this does and does not show

- **It shows** that, over 2019–2024, the published profiles were optimistic at every horizon tested, on a basis
  that matches MBIE's own, and that the proved reserve category is not behaving as a conservative floor.
- **It does not cover the two most recent releases.** The 2025 and 2026 workbooks are not in the Internet Archive.
  MBIE's own statements about them point the same way, but they are outside this analysis.
- **It cannot separate optimism from changed plans.** A profile is conditional on a development plan that may later
  change for commercial or technical reasons. The study measures the calibration of the published numbers, not
  intent.
- **The size is imprecise.** Two vintages contribute at three years on the field-level measure, and the
  field-cluster bootstrap treats fields as independent when a bad year hits them together. The national table,
  where every comparison overshoots, is the more robust statement of direction.
- **"Others" is a residual bucket** and the single most over-forecast "field"; the sensitivity excluding it is
  reported.
- **It is not a resource assessment.** Nothing here says how much gas is in the ground.
- **Units are fields and company filings**, not people or communities.

## Process and deviations

- **Preregistration.** `plan.md` was committed before any forecast was paired with any outcome, and after only the
  structure of one workbook and the archive listings had been examined.
- **Code before outputs.** `fetch.py`, `parse.py`, `analysis.py` were each committed before the outputs they
  produced; `figures.py` was written after the results, as the report states.
- **D1** records what the archive could give (six vintages, not the latest two), the one-capture-per-vintage rule,
  the 2023 cut-off on field-level outcomes, and the identification of the national series as the net basis.
- **A first analysis run double-counted the 2021 vintage** because two captures carry it; the rule in D1 was added
  and the run repeated before any result was written down.

## Reproducing it

`code/fetch.py`, then `code/parse.py`, `code/analysis.py`, `code/figures.py`.

- **Raw inputs** are Internet Archive raw copies listed with their sha256 in `data/raw/MANIFEST.json`.
- **Results** are in `results/tables/`: `primary.json`, `by_horizon.csv`, `pairs.csv`, `national_pairs.csv`,
  `revisions.csv` and `vintages.csv`.
