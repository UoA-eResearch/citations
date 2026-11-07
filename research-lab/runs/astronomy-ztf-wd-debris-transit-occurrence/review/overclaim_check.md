# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | How common are debris transits around white dwarfs? Known systems alone give about 1 in 5,000 within 500 pc after correcting for what ZTF can detect, but nearly 900 unvetted candidates leave the rate unbounded above | primary.json combined rate_lower 2.06e-4, rate_upper 1.23e-2 | Supported |  |
| 2 | standfirst | 109,074 Gaia white dwarfs within 500 pc with at least 100 good ZTF epochs were searched blind with two preregistered rules: recurring faint outliers (hour-scale dips) and runs of faint 30-day bins (day- to year-scale dimming). | primary.json eligible_stars 109074; plan rules | Supported |  |
| 3 | standfirst | The 20 known debris-transiting white dwarfs were compiled from the discovery papers and committed before detection was run. | known_systems.csv; git: committed before detect.parquet | Supported |  |
| 4 | standfirst | Completeness comes from 150,000 injected signals. | inject.parquet 150,000 rows | Supported |  |
| 5 | standfirst | The plan was committed before any light curve was fetched. | git: plan.md before fetch_lc | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive.** The rate of ZTF-detectable debris transits lies between 2.1 × 10⁻⁴ (known systems alone) and 1.2 × 10⁻² (every unvetted candidate counted). | primary.json combined lower/upper | Supported |  |
| 7 | verdict | The bar of 5 × 10⁻⁴ falls between those two bounds. | primary.json H1 Inconclusive | Supported |  |
| 8 | verdict | **H1 (the occurrence of ZTF-detectable debris transits, all classes combined, is below 5 × 10⁻⁴): Inconclusive.** | primary.json H1 | Supported |  |
| 9 | verdict | **Lower rate:** 15 recovered known systems over a completeness-weighted sample of 72,748 stars gives | primary.json combined N_lower 15, sum_completeness 72748 | Supported |  |
| 10 | verdict | **2.1 × 10⁻⁴** (95% Poisson 1.2 × 10⁻⁴ to 3.4 × 10⁻⁴). | primary.json rate_lower_ci [1.15e-4, 3.40e-4] | Supported |  |
| 11 | verdict | Its lower limit is below 5 × 10⁻⁴, so H1 is not Refuted. | primary.json rate_lower_ci | Supported |  |
| 12 | verdict | **Upper rate:** adding the 878 unexplained candidates gives **1.2 × 10⁻²** (1.15 × 10⁻² to 1.31 × 10⁻²). | primary.json N_upper 893, rate_upper_ci [1.15e-2, 1.31e-2] | Supported |  |
| 13 | verdict | Its upper limit is above 5 × 10⁻⁴, so H1 is not Supported. | primary.json rate_upper_ci | Supported |  |
| 14 | verdict | Read on its own, the lower rate says that known systems alone already amount to about 1 in 5,000 white dwarfs once detectability is accounted for. | primary.json rate_lower 2.06e-4 (1 in 4,850) | Supported |  |
| 15 | verdict | A rate below 5 × 10⁻⁴ is plausible, but only vetting the candidates could show it. | interpretation (hedged) | Supported |  |
| 16 | verdict | **The positive controls work.** 18 of the 20 known systems are in the sample (one is fainter than G = 20, one beyond 500 pc), and the rules flag 15 of them. | known_systems.csv in_sample 18; reasons | Supported |  |
| 17 | verdict | The three missed are SDSS J0107+2107 (continuous shallow dips), SBSS 1232+563 (sporadic dimming) and WD 1054−226 (dips of a few per cent, with only 207 epochs). | primary.json known_missed; detect.parquet | Supported |  |
| 18 | verdict | Of the 15 recovered, three are flagged by the short-dip rule alone, six by the long-dip rule alone, and six by both. | detect.parquet x known_systems: 3 / 6 / 6 | Supported |  |
| 19 | verdict | **Completeness.** Injected signals are recovered 66% of the time for WD 1145-like hour-scale dips, 50% for J0139-like day-scale dips and 53% for one-off dimming lasting 30–400 days. | primary.json injection_recovery_by_class | Supported |  |
| 20 | verdict | Recovery falls for fainter stars (F2). | F2; inject.parquet by G bin | Supported |  |
| 21 | verdict | **The candidates are mostly long-dip flags.** | candidates.csv | Supported |  |
| 22 | verdict | 914 stars are flagged, and 21 of them are CVs in Gaia DR3's variability classification. | primary.json flagged 914, gaia_variables_removed 21 | Supported |  |
| 23 | verdict | That leaves 878 candidates beside the 15 known systems: 653 flagged by the long-dip rule only, 205 by the short-dip rule only, and 20 by both. | candidates.csv short/long split 205/653/20 | Supported |  |
| 24 | verdict | The long-dip rule is sensitive to its threshold. | primary.json threshold_variants_flagged | Supported |  |
| 25 | verdict | At 3 standard errors instead of 5 it flags 7,130 stars, at 7 it flags 138, so most long-dip flags are probably slow photometric trends rather than dimming events. | primary.json long_3 7130, long_7 138 (inference, hedged) | Supported |  |
| 26 | verdict | The list is not vetted. | design | Supported |  |
| 27 | verdict | It is in `results/tables/candidates.csv` (Gaia DR3 source IDs, public facts). | candidates.csv | Supported |  |
| 28 | verdict | **Implied geometry.** If a quarter to a half of white dwarfs are metal-polluted, the lower rate implies a transit probability × duty cycle of 4 × 10⁻⁴ to 8 × 10⁻⁴ among polluted stars (descriptive). | primary.json geometric_times_duty_if_polluted_25_50pct | Supported |  |
| 29 | plain terms | When a white dwarf, the dense remnant of a star like the Sun, tears apart an asteroid or small planet, the dusty debris can pass in front of it and make it dim. | background (A3) | Supported |  |
| 30 | plain terms | About twenty such stars are known, most found in the last five years in data from the Zwicky Transient Facility (ZTF), a telescope that photographs the northern sky every few nights. | known_systems.csv discovery years; ledger A3-A10 | Supported |  |
| 31 | plain terms | How common are they? | question | Supported |  |
| 32 | plain terms | We took about 110,000 white dwarfs within 500 parsecs (about 1,600 light-years) that ZTF has observed at least 100 times. | primary.json eligible 109,074; plan sample | Supported |  |
| 33 | plain terms | We searched each one's brightness record with two simple rules fixed in advance: repeated sudden faint measurements, and months-long stretches of dimming. | detect.py rules | Supported |  |
| 34 | plain terms | The rules found 15 of the 18 known debris-transit stars in our sample. | primary.json known_recovered 15 of 18 | Supported |  |
| 35 | plain terms | By planting fake dimming events into real light curves, we measured how often the rules would catch such a star: about half to two-thirds of the time. | primary.json injection recovery 0.50-0.66 | Supported |  |
| 36 | plain terms | Counting only the known systems, and correcting for what the search can catch, about 1 in 5,000 of these white dwarfs shows detectable debris transits. | primary.json rate_lower | Supported |  |
| 37 | plain terms | The rules also flagged nearly 900 other stars. | primary.json candidates 878 | Supported |  |
| 38 | plain terms | Most are probably slow drifts in the measurements rather than debris, but until each is checked, the true rate could be anywhere from about 1 in 5,000 to about 1 in 80. | primary.json rate_lower and rate_upper (1/81); hedged | Supported |  |
| 39 | plain terms | So the study cannot say whether the rate is below the 1-in-2,000 bar the lead proposed. | primary.json H1 | Supported |  |
