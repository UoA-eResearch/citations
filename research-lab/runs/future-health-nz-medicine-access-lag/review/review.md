# Independent review: future-health-nz-medicine-access-lag (pre-review draft, commit c0386fc)

Reviewer: independent adversarial review agent, 2026-10-17. Scope: plan.md (8d0bc67), deviations.md D1–D7, report.md /
report.html, all code, results tables, data/, validation evidence, git history. Everything I ran is under
`review/reviewer_checks/` (scripts) and `review/reviewer_checks/cache/` (evidence files, PDF text, reproduced forecast).
Nothing outside `review/` was modified; nothing was committed; medsafe.py was not run.

## Recommendation: **fix first**

The two headline numbers survive every stress test I applied: the aggregate regulatory share is 0.40 under the
preregistered definition and stays at 0.39–0.41 when the 13 excluded substances are added back, when the cohort errors
below are corrected, and when provisional consent is bounded; H1b stays Inconclusive. The frozen forecast reproduces
bit-for-bit, and the adjudicate-before-analyse / freeze-before-later-data ordering checks out in git.

But the report cannot be published as written, for four reasons that change what it says rather than how precisely it
says it:

1. **H3 is framed against a definition the source does not use.** The "7.7 years" figure is defined in the report it
   comes from (HealthiNZ, April 2023, as quoted by Shawview 2023, pp. 10 and 26) as the mean time *from submission of
   the funding application to PHARMAC to a funding decision, for the 29 applications that achieved a decision* (median
   6.5 years). It is a decided-only, application-based statistic. The report says the opposite ("not survivor-weighted
   ... the reverse"; "consistent with counting medicines still waiting"; "7.7 years is a reasonable summary"). The
   preregistered T2→T3 test measures a different interval, and the numeric match with RMST(10 y) = 7.0 is a coincidence
   of a horizon choice (RMST is 5.7 y at τ = 7.7, 7.0 at τ = 10, 8.1 at τ = 12).
2. **The stage table silently drops 21 of 70 eligible funded substances** (every sponsor that filed in NZ before the
   first FDA/EMA approval), which inflates the sponsor-delay median from 280 to 494 days and the "total median" from
   1,483 to 2,200 days, and moves the shares from 26/16/58 to 30/14/56.
3. **T1 and T2 are systematically late for provisional-consent medicines, and the validation did not catch it.**
   `link.py` only counts `^New .*Medicine Application` rows, so "Provisional Consent (Section 23)" applications are
   never T1 (11 substances; T1 late by 521–3,484 days or missing in 10 of them). Two of these (atezolizumab,
   vemurafenib) were in the agent's own validation samples with the provisional row visible in the evidence file and
   were scored 1/1/1. The report's limitation mentions T2 only.
4. **Cohort error is about 6%, not "about 2%", and is concentrated in EMA-first entries (~23%).** Drugs@FDA excludes
   CBER-licensed biologics (I checked: Kymriah, Luxturna, Zolgensma, Eloctate, Alprolix, Rixubis, Provenge, Andexxa,
   Vonvendi, Coagadex, Breyanzi, Abecma, Carvykti, Hemgenix, Casgevy all have zero rows), so ~30 cell/gene/coagulation
   products carry an EMA T0 that is 2 days to 3.4 years late; 8 FDA/EMA pairs are unmerged duplicates
   (ado-/fam- prefixes, a typo, USAN/INN); ~9 old substances and 2 diagnostics are in. The report attributes this to
   "proper names" and counts 1 in 150.

Fixing these does not change the H1a/H1b verdicts (I recomputed them under the corrections), but it changes the H3
verdict text, the stage split, the plain-language summary, the TGA paragraph, and the limitations. Details, with
locations and concrete fixes, follow. Issues 1–8 should be fixed before publication; 9–17 should be fixed; 18–24 are
minor.

---

## Issues

### A. Fix before publication

**1. H3: the 7.7-year figure is decided-only and application-based, and the report says it is neither.**
*Location:* report.md "H3: the denominator, and what '7.7 years' measures", the Verdict bullet "'7.7 years' is not
survivor-weighted (H3, Refuted), but the reverse", the plain-language paragraph "7.7 years is a reasonable summary of
it", Figure 3 caption; analysis.py H3 block; plan §5.
*Evidence:* Shawview Consulting, *The future of Aotearoa's medicines access* (Aug 2023), p. 10: "applications that
achieved a funding decision did so on average 7.7 years following their submission to Pharmac"; p. 26: "for the 29
applications that achieved a funding decision did so on average 7.7 years (or median 6.5 years) following their
submission to Pharmac", citing HealthiNZ, *Pharmac's Medicines Waiting Lists: Impacts on Patients in Aotearoa New
Zealand* (April 2023, commissioned by Medicines New Zealand), p. 3. Text extracted to
`reviewer_checks/cache/downloads/shawview_2023.pdf.txt` (lines 380–460, 765–790). PHARMAC's public response (1News,
27 Apr 2023) describes the figure as "average times that things are sitting on our lists" and says that for medicines
it does fund the average is "just over two years", which matches this study's funded-only 2.1-year median.
*Why it matters:* (a) the interval is application→decision, not Medsafe consent→funding, so the preregistered T2→T3
denominators do not test the claim; the D3 application-based block does. (b) The source population is 29 decided
applications: by construction it excludes undecided ones, i.e. it *is* a decided-only statistic, as the lead
hypothesised. This study's decided-only application→approval figure is 3.4 y mean / 2.2 y median (n = 75), nowhere
near 7.7; but restricted to decisions made in 2024–26 it is 6.4 y mean / 5.6 y median (n = 18)
(`reviewer_checks/recompute.py`, last block). The most plausible reading is length-biased sampling of a backlog being
cleared in a particular window, not "counting medicines still waiting". (c) The censoring-aware match is horizon
dependent: RMST to 5/7.7/8/10/12/13 y = 4.0/5.7/5.8/7.0/8.1/8.6 y. τ = 10 was preregistered, so the number is
legitimate, but "7.7 fits" is not a robust statement; the KM median (12 y) is the honest censoring-aware summary.
*Fix:* Re-write the H3 section around the source definition. State it. Report the application-based decided-only
figures (3.4/2.2 y; by decision year) and the KM median application→approval (8.7 y) as the relevant comparison; keep
the T2→T3 table but as context. The preregistered rule on T2→T3 can still be reported ("Refuted under the T2→T3 rule"),
but the headline must say the figure as defined by its source cannot be reproduced from this cohort's decided
applications (3.4 y), that recent decisions on long-waiting applications come closer (6.4 y), and that the
"not survivor-weighted, the reverse" claim is withdrawn. Delete "7.7 years is a reasonable summary of it". Add the
horizon sensitivity to Figure 3 or its caption.

**2. H3, other industry figures: "7–10 years" is a "for many medicines" claim, and "1,050 days" is a funded-only
registration-to-funding median.**
*Location:* report.md "The other industry figures check out as follows"; plan §5 last line.
*Evidence:* BMS, *Access to Innovative Pharmaceutical Medicines in New Zealand* (2026), p. 4: "Delays of 7-10 years
between Medsafe approval and funding occur for many medicines in New Zealand. By contrast, access times in Australia and
the United Kingdom are typically 6–18 months" (`cache/downloads/bms_2026.pdf.txt` lines 102–106, 485). The 1,050-day
figure is IQVIA AtoM (via Medicines NZ / BMS p. 11): "waited an average of almost three years (1,050 days) for public
funding, nearly double the average wait time for Australians (481 days)", for medicines funded Jan 2011–Jun 2025;
Shawview's Figure 2 labels the earlier AtoM series "MEDIAN DAYS FROM REGISTRATION TO PUBLIC FUNDING".
*Fix:* Test "7–10 years for many medicines" as stated: in this cohort 9 of 79 funded substances waited ≥ 7 y from
consent to funding (4 in 7–10 y, 5 > 10 y, max 13.0 y), and 60% of consented substances are still unfunded at 7 y
(KM). Say that, instead of "the funded-only mean (3.2) is outside that range". For 1,050 days, say it is a funded-only
registration-to-funding average (and that the AU comparator is quoted as 481 or 556 days in different editions), and
compare with the funded-only T2→T3 mean 3.2 y / median 780 d — the mean (1,164 d) is the like-for-like comparison, and
it is *above* 1,050, not below.

**3. Stage table: 21 early-filing substances are dropped by the `T0 <= T1` filter.**
*Location:* analysis.py `st = st[(st.t0 <= st.t1) & ...]`; report.md "The stage split. Among the 49 funded substances
with all four dates"; Figure 1 and caption; stage_table.csv; the plain-language "Waiting for the company to apply in
New Zealand: about 30%".
*Evidence:* 25 of 89 funded substances have T1 < T0 (sofosbuvir, ledipasvir, fingolimod, obinutuzumab, umeclidinium,
glecaprevir, pibrentasvir, nintedanib (by 8 days), …); 21 of them meet every other stage-table condition
(`reviewer_checks/probe2.py`, `recompute.py` "stage split"). With them included and the sponsor delay clipped at 0:
n = 70, medians sponsor/Medsafe/funding/total = 280/268/778/1,483 days, shares 25.8/16.1/58.1%, T0→T2 share 41.9%.
Reported: n = 49, 494/269/931/2,200, 29.8/13.8/56.4%. The caption "all four dates" is wrong: the 21 have all four. The
sentence "The total median is 2,200 days" sits two paragraphs after H1b's 1,556 with no explanation.
*Fix:* Use the n = 70 table (clip sponsor delay at 0, or report negative delays explicitly) as the primary stage
table; state that 21 sponsors filed in NZ before the first FDA/EMA approval (30% of funded substances — itself a
finding worth a sentence); re-draw Figure 1; change "about 30%" to "about a quarter" and "14%" to "about 16%".

**4. T1 ignores "Provisional Consent (Section 23)" applications; T2 is the later full consent for converted
products.**
*Location:* link.py `NEW_APPL = re.compile(r"^New .*Medicine Application")`; deviations D6.4 and report limitation
"Late T2" (T2 only); link_validation.csv rows r018, m116; link_validation_v2 counts.
*Evidence:* `reviewer_checks/provisional_t1.py`: 11 substances have a Section 23 application; in 10 it precedes the
linked T1 or T1 is missing: alpha1-proteinase inhibitor (3,484 d), vemurafenib (1,442), polatuzumab vedotin (1,047),
glofitamab (761), atezolizumab (521), and amivantamab, cilgavimab, epcoritamab, tixagevimab, zanubrutinib (T1 missing).
For converted products the product "approval date" is the full consent (Zelboraf 17/12/2015 after a 2011 provisional
application; Tecentriq 14/02/2019 after a 2016 provisional application; Columvi 29/05/2025; Polivy 16/03/2023; Paxlovid
12/11/2024), so T2 is late by one to four years for 5 of 209 consented substances. Atezolizumab is in the H1
population; the aggregate share barely moves (S3 bound 0.400), so this is a correctness and validation issue, not a
verdict issue.
*Fix:* Add `Provisional Consent \(Section 23\)` to NEW_APPL (it is a new-medicine application). For T2, the earliest
consent is not recoverable from the Product search; either (i) use the provisional application date as a lower bound
and report an interval, or (ii) look up the gazette notice for the 5 converted products. Re-run link.py and the
affected tables; correct D6.4 and the limitation to cover T1. Re-score r018/m116/r059/m073 in the validation files.

**5. Cohort T0: Drugs@FDA excludes CBER biologics; unmerged FDA/EMA duplicates; old substances; diagnostics.**
*Location:* cohort.py (`fda()`, ALIAS, EXCLUDE, DIAG_RE), names.py `norm`, deviations D6.2 ("1 of 150") and D7
("about 2%"), report "Cohort impurity. About 2% of entries", "Late T0 ... about 1 in 150".
*Evidence (`reviewer_checks/cohort_checks.py`, `probe3.py`):*
- CBER products with earlier FDA approval than the EMA T0 used (my dates from FDA records): nonacog gamma (Rixubis
  2013-06-26 vs 2014-12-19; **funded, in H1**), eftrenonacog alfa (Alprolix 2014-03-28 vs 2016-05-12; **funded**, now
  excluded as "consent before T0"), efmoroctocog alfa, turoctocog alfa, susoctocog alfa, lonoctocog alfa,
  albutrepenonacog alfa, damoctocog alfa pegol, turoctocog alfa pegol, nonacog beta pegol, efanesoctocog alfa, eptacog
  beta, vonicog alfa, human coagulation factor x, radamts13, andexanet alfa, tisagenlecleucel, axicabtagene ciloleucel,
  brexucabtagene autoleucel, idecabtagene vicleucel, lisocabtagene maraleucel, ciltacabtagene autoleucel, onasemnogene
  abeparvovec, voretigene neparvovec, etranacogene dezaparvovec, exagamglogene autotemcel, fidanacogene elaparvovec,
  talimogene laherparepvec, Provenge (2 entries; FDA 2010-04-29 vs 2013-09-06). About 30 of 195 EMA-first entries.
- Unmerged duplicates: ado-trastuzumab emtansine / trastuzumab emtansine (**funded**; the EMA entry is 9 months late
  and therefore excluded from H1 as "consent before T0"; the FDA entry is unlinked because Medsafe writes
  "Trastuzumab emtansine"); fam-trastuzumab deruxtecan / trastuzumab deruxtecan (**funded**, T0 13 months late);
  lutetium lu-177 vipivotide tetraxetan / lutetium vipivotide tetraxetan; dalfampridine / fampridine; ezogabine /
  retigabine; voxilaprevir / voxilaprevi (EMA typo); birch triterpenes / birch bark extract; asparaginase erwinia
  chrysanthemi / crisantaspase. The audit file `t0_audit_candidates.csv` listed trastuzumab deruxtecan, trastuzumab
  emtansine and lutetium vipivotide tetraxetan but matched them to Herceptin/Lutathera and dismissed them.
- Old substances not caught by D2.2 because they were never in NZ: c1 inhibitor (FDA Cinryze 2008-10-10, so T0 is
  pre-2010), chlormethine (mechlorethamine 1949), human coagulation factor viii and human von willebrand factor
  (Voncento; Humate-P 1986), alpha1-proteinase inhibitor (Prolastin 1987), pancreas powder, para-aminosalicylic acid
  (**counted as funded** via the first HML edition), asparaginase erwinia chrysanthemi (Erwinaze 2011), polidocanol
  (**counted as funded**; a 1960s sclerosant).
- Diagnostics in the cohort: xenon xe-129 hyperpolarized (Xenoview, MRI contrast; "xe" is not in DIAG_RE), c-11
  (choline C-11, PET). "lutetium" (Lumark, a radiolabelling precursor, ATC V10) is not a medicine.
- Multi-component products counted as several substances: Zalmoxis (3), Strimvelis (3), Provenge (2), Voncento (2),
  Teysuno (3), Eurartesim (2).
Total ≈ 45 of 705 (6%); ≈ 23% of EMA-first entries. Direction: a late T0 shrinks numerator and denominator alike, so
the aggregate share is nearly unchanged (0.401 after corrections, n = 77: dimethyl, eftrenonacog alfa and trastuzumab
emtansine join), the H1b median rises to 1,668 d [1,329, 2,134], and the duplicates inflate the unconsented/unfunded
denominators behind "three in ten" and "one in eight".
*Fix:* (i) Add a CBER source (FDA's "CBER-regulated products" approval lists or the Purple Book) or hand-override the
~30 listed; (ii) merge the 8 duplicate pairs (strip `ado-`/`fam-` prefixes in `norm`; add the aliases); (iii) exclude
xenon xe-129, c-11, lutetium, the old substances listed; (iv) count a multi-component product once; (v) replace
"about 2%" and "1 in 150" with the measured figure and the correct cause (source coverage, not naming).

**6. "dimethyl": a salt-stripping residue that false-matches dimethyl sulfoxide in the first HML edition.**
*Location:* names.py SALT_RE ("fumarate" stripped from "dimethyl fumarate"); link.py matching; primary.json
`funded_before_consent: 5`.
*Evidence:* `probe4.py`: the 2013-10-01 HML row matched is "Dimethyl sulfoxide, Soln 50%". Dimethyl fumarate's true
T3 is the community listing 2016-02-01 (T0 2013-03-27, T2 2014-07-24), which puts it in the H1 population with share
0.47 instead of in "funded before consent". `cohort_checks.py` shows ~30 other single-word residues of salt stripping;
the others are proper INN stems (alectinib, edoxaban, …) and harmless, but the rule has no guard against a residue that
is a common chemical word.
*Fix:* Never let a stripped name collapse to a word in a small stoplist of chemical adjectives (dimethyl, ferric,
sodium, …); special-case dimethyl fumarate ("dimethyl fumarate" should keep its second word, as PHARMAC and Medsafe
both write it). Recount the 13 excluded.

**7. TGA comparison: the ARTG file holds current entries, and this is not a small caveat.**
*Location:* report "A secondary regulator comparison ... Medsafe consented a median 427 days after Australia's TGA";
plain-language "Its regulator approved the same medicines a median of about 14 months earlier"; D3.3.
*Evidence (`gap_tga_prov.py`, evidence files):* 25 of 209 NZ-consented substances have no TGA match; at least 18 of
them were ARTG-registered and later cancelled (Victrelis, Incivo, Daklinza, Viekira Pak, Zepatier, Olysio, Picato,
Lyxumia, Praluent, Invokana, Sirturo, Xiaflex, Brinavess, Jetrea, Zurampic, Truberzi, Fotivda, Sovaldi; all return 0
rows in tga_artg.csv). Dated entries can also be late: Striverdi/Spiolto 2020 (registered 2014–15), Keytruda
2016-03-08 (first registered 2015-04-16; the 50 mg vial entry is gone), Aubagio → a 2019 generic. Spot check of 14
substances: 11 right, 3 late by 0.9–6 years. Medsafe T2, by contrast, comes from a full-history register including
lapsed and revoked consents. The two sources are not comparable, and the paired median of 427 days is computed on the
subset of substances still marketed in Australia.
*Fix:* Either drop the paired-median sentence and the plain-language claim, or restrict both regulators to products
still current and say so; keep the KM "by 2 / 5 years" comparison only with an explicit statement that the AU curve is
a lower bound on TGA registration.

**8. Scoring rule for H4 does not match the linking rule.**
*Location:* score_forecast.py uses `re.escape(s)` on the bare `substance`; link.py used `match_names` (aliases and the
first-word rule).
*Evidence (`forecast_check.py`):* 22 of the 125 forecast substances have `match_names != substance`, including
isavuconazole (Medsafe and PHARMAC write "isavuconazonium"), polatuzumab vedotin, sacituzumab govitecan, cabozantinib
("cabozantinib s"), baloxavir marboxil. A funding of isavuconazonium in 2027 would be scored as not funded. The
forecast itself reproduces exactly (sha256 70b7aec5…, max |Δp| = 0), with no post-origin feature information found.
*Fix:* Freeze a companion file now (`results/forecast_2026_match_names.csv` with its sha256, committed before any 2027
Schedule is read) and make score_forecast.py read it. This changes the scoring rule, not the forecast, and must be
logged as a deviation dated before scoring. Also state that 24 of the 125 have lapsed or revoked consent.

### B. Should fix

**9. H1a's "Refuted" headline depends on counting the sponsor's delay as "regulatory".**
*Location:* Verdict paragraph "Refuted, on the lead's two main claims ... the regulatory stage is not a small share".
*Evidence:* The lead says "the Medsafe regulatory stage accounts for less than 25%". Medsafe's own review (T1→T2 with
T1 clipped at T0) is 16.1% [13.4, 19.2] of T0→T3 among the 70 H1 substances with a T1 (`cohort_checks.py`); under
that reading the lead's claim is Supported with the whole interval below 25%. The plan preregistered T0→T2 (D1.2), so
the verdict is faithful to the plan, but the top-line sentence attributes to "the regulatory stage" what is mostly the
sponsor's choice, which the report itself says two paragraphs later.
*Fix:* Headline both: "T0→T2 share 40% (Refuted as preregistered); Medsafe's own review 16% (the lead's claim holds for
the regulator alone)".

**10. "Correctly absent" is under-verified when Medsafe's ingredient naming is coarser than the INN.**
*Location:* validate.py; D6.1 "Absences ... loose substring match on the first seven letters"; report "Re-validation.
A fresh 100 then gave T1 1.000, T2 0.990, T3 1.000".
*Evidence:* tenofovir alafenamide (n023) is recorded by Medsafe as "Tenofovir" for Vemlidy (consent 26/10/2017),
Genvoya (10/11/2016), Descovy, Odefsey and Biktarvy; the study has T1/T2 absent. The first-word rule cannot apply
because "tenofovir" is an old token. The 7-letter loose check cannot see it either. The same mechanism can hide any
new ester/prodrug of an old moiety. The agent's "cannot tell" category was also used for 4 of 150 T1 cells where the
provisional application was present in the evidence (r059, m073).
*Fix:* For the ~45 multi-word cohort names whose first word is an old token, inspect Medsafe rows returned for the
old token by product name (Vemlidy, Genvoya…) and hand-link; report the count.

**11. Validation adjudication speed and reproducibility.**
*Location:* results/tables/link_validation_v2_raw.csv (mtime 22:41:20) vs data/validation/evidence_v2 (22:38:53 –
22:40:05); link_validation_raw.csv (22:10:02) vs evidence (22:05:38 – 22:07:24).
*Evidence:* 100 three-cell adjudications in ~75 s and 150 in ~2.6 min, with 98 of 100 D7 rows all-1 and no notes.
My re-adjudication of 40 of those rows plus 30 new (`reviewer_checks/readjudication.csv`, `build_readj_sample.py`;
sample enriched for present dates, so not a precision estimate) disagrees on 4 substances / 6 cells, all provisional
consent cases, and finds 7 T1, 4 T2 and 0 T3 errors in 64/70/69 judgeable cells (0.89 / 0.94 / 1.00). The analysis did
run after the adjudication file was written (22:41:43), as required.
*Fix:* Report both adjudications side by side; add the provisional-consent class to the evidence format (mark Section
23 rows with "+").

**12. The HML archive starts in October 2013 and its first edition is not a funding event.**
*Location:* D2.1 says HML "2011–2025"; report says "2013–2026"; link.py has no left-censoring for the first HML
edition (the community Schedule has `b <= first_ed` in D2.2, the HML has nothing).
*Evidence:* 4 funded substances have T3 = 2013-10-01: defibrotide (T0 2013-10-18, so "funded" 17 days before first
approval), para-aminosalicylic acid, polidocanol, and dimethyl (false match, issue 6). PHARMAC took over hospital
medicines in July 2013; medicines in the first HML had been DHB-funded for years.
*Fix:* Treat presence in the first HML edition as left-censored (exclude from T3H dating, or flag), as D2.2 does for
the 2006 Schedule; correct D2.1's years.

**13. The 678/678 "independent" cross-check is not independent of the matching rule.**
*Location:* D3.2, report "Cross-check. Agreement with the independent Medsafe register snapshot is 678 of 678".
*Evidence:* crosscheck_medsafe.py applies `has_any(match_names, …)` to the same register's "Active ingredients"; any
systematic naming miss (ceftaroline before D6, tenofovir alafenamide now) is replicated on both sides. It verifies
crawl completeness only.
*Fix:* Say "crawl completeness check (same register, same matcher)".

**14. Report numbers mix populations.**
*Location:* Verdict bullet "about 40% ... Most of it is the sponsor's delay (30%). Medsafe's own review is 14%, and
funding takes the remaining 56%".
*Evidence:* 40% is Σ(T2−T0)/Σ(T3−T0) over n = 74; 30/14/56 are from n = 49 (where T0→T2 is 43.6%). The three
percentages cannot be read as a decomposition of the 40%.
*Fix:* Give the decomposition on one population (the n = 70 set of issue 3: 26/16/58, T0→T2 42%).

**15. Items promised by the plan and missing from the report.**
2024 approvals "reported separately" (53 substances, 3 consented, 2 funded: not in the report); the third H3
denominator "all cohort substances from T0" (KM median not reached, RMST to 10 y 9.2 y: in primary.json, not in the
report); the plan's cutoff "1 November 2026" vs the 2026-10-01 used (state the change); recall check result 10/10 is
reported but the 40 non-cohort chemicals are not characterised (fine, but say they were old or vaccines).

**16. "before any later Schedule Update was read" is not literally true.**
*Location:* report H4 paragraph; commit message 4577be4.
*Evidence:* `data/su_listings.csv` contains rows effective 2026-11-01 from the 16 Oct 2026 Update (pioglitazone,
taurine, fluconazole, naltrexone, cetirizine, hydrocortisone, sildenafil, venlafaxine). None is a cohort substance,
so there is no leakage, but the sentence should say so.
*Fix:* "committed before any Schedule edition after the origin was used; the 16 Oct 2026 Update (effective 1 Nov) had
been parsed and contains none of the 125".

**17. D4 gap fill changed nothing, and that should be stated.**
*Evidence (`recompute.py`, `gap_tga_prov.py`):* 16 substances have a gap-window T3B from the Schedule Update PDFs; in
every case the HML XML gives the same month, so T3 is unchanged by D4. Recall of the SU parser inside the June 2024 –
Dec 2025 gap is complete (all 28 Section B chemicals new between the May 2024 and Jan 2026 XML appear in the SU gap
rows). The parsed SU rows are quadruplicated (each listing appears 4×), harmless for `min()`.
*Fix:* One sentence in D4 or the report.

### C. Minor

**18.** MSW `T3_AU` takes the first record with a "Medicine listed on the PBS" date, which can be a "Change to
listing" (olodaterol: 2021-03-01 vs PBS listing in 2015). Irrelevant within the 2019–2024 H2 window, but
`results/tables/linked.csv` publishes the column for all 705; label it "first MSW-recorded listing date, 2019+".

**19.** H2: MSW listing dates start 2019-11-01 and meetings start July 2019; a 2019 first approval whose PBAC
submission predated July 2019 is not tracked. Say "submissions considered from July 2019".

**20.** Forecast: the `year` feature at the origin (8) is outside the training range (−6..6); leave-one-snapshot-out
Brier skill is ≈ 0 (−0.36 to +0.08 by year; in-sample 0.06). Worth one sentence so a null result in 2027 is not read as
a surprise.

**21.** D6.2 attributes the undetectable FDA approvals to "a different brand and proper name"; the mechanism is
Drugs@FDA's exclusion of CBER products (Velphoro, the other override, is a CDER product listed under a different
ingredient string — that one is a naming case).

**22.** cohort.py splits FDA ingredient strings on ";" only, so comma-separated co-packaged strings
("ELEXACAFTOR, IVACAFTOR, TEZACAFTOR") survive as single names and had to be aliased by hand; split on "," too and the
ALIAS table shrinks.

**23.** report.html matches report.md numerically (checked by diffing all numeric tokens). Figure captions match the
.txt files. The F1 caption needs the n = 70 change (issue 3).

**24.** deviations.md D2.1 "HML ... 2011–2025" vs files 2013-10 – 2026-10; plan §4 "Data cutoff. 1 November 2026" vs
analysis cutoff 2026-10-01.

---

## Recomputed numbers

All from `review/reviewer_checks/recompute.py`, `cohort_checks.py`, `forecast_check.py`, `gap_tga_prov.py`,
`provisional_t1.py` on the study's own data; "corrected" = reviewer T0/T3 corrections of issues 5–6 with the old and
duplicate entries dropped (list in `recompute.py`).

| quantity | report | reviewer | note |
| --- | --- | --- | --- |
| cohort / FDA-first / EMA-first | 705 / 510 / 195 | 705 / 510 / 195 | reproduced |
| excluded old / analysed / T0 2010–23 / funded / H1 used | 25 / 680 / 627 / 87 / 74 | same | reproduced |
| H1a aggregate share, n = 74 | 0.40 [0.33, 0.48] | 0.404 [0.327, 0.484] | reproduced |
| H1a incl. 13 excluded (T2 clipped into [T0,T3]), n = 82 | — | 0.398 [0.328, 0.478] | |
| H1a corrected cohort, n = 77 | — | 0.401 [0.333, 0.480] | dimethyl, eftrenonacog alfa, trastuzumab emtansine join |
| H1a provisional lower bound (T2 := T1 for provisional-route) | — | 0.400 | atezolizumab only in H1 |
| Medsafe-only share T1→T2 / T0→T3, n = 70 | "14%" (n = 49) | 0.161 [0.134, 0.192] | |
| sponsor share (clipped), n = 70 | "30%" (n = 49) | 0.258 [0.191, 0.335] | |
| H1b median T0→T3, n = 74 | 1,556 [1,329, 2,200] | 1,556 [1,329, 2,200] | reproduced |
| H1b all 87 funded | 1,447 | 1,447 | |
| H1b corrected cohort, n = 77 | — | 1,668 [1,329, 2,134] | still Inconclusive |
| stage medians sponsor/Medsafe/funding/total | 494/269/931/2,200 (n = 49) | 280/268/778/1,483 (n = 70) | 21 early filers restored |
| stage shares | 29.8/13.8/56.4% | 25.8/16.1/58.1% | |
| funded with T1 < T0 | not reported | 25 of 89 (21 eligible for the table) | |
| H3 funded-only mean / median (y) | 3.2 / 2.1 (n = 79) | 3.19 / 2.14 | reproduced |
| H3 KM median, consented (y) | 12.0 (n = 204) | 11.95 | reproduced |
| H3 RMST to 10 y | 7.0 | 6.99 | RMST 5/7.7/8/12/13 y = 3.99/5.66/5.84/8.05/8.55 |
| funded by 5 / 10 y | 33% / 43% | 0.331 / 0.434 | reproduced |
| consented ≥ 10 y ago: funded share, funded-only mean | — | 40/80 = 50%, 3.98 y | |
| application→approval decided-only mean / median (y) | 3.4 / 2.2 (n = 75) | 3.42 / 2.20 | reproduced |
| … decisions in 2022–23 / 2024–26 | — | 4.13/3.57 (n = 10); 6.43/5.56 (n = 18) | cf. HealthiNZ 7.7/6.5 on 29 decided |
| funded with T2→T3 ≥ 7 y / in 7–10 y / > 10 y | — | 9 / 4 / 5 of 79 | BMS "7–10 years for many" |
| consented still unfunded at 7 y (KM) | — | 60% | |
| provisional-route substances | 12 of 209 | 12; 11 with a Section 23 application; 10 with T1 late/missing | |
| funded with T3 = first HML edition (2013-10-01) | — | 4 (defibrotide, dimethyl*, PAS, polidocanol) | *false match |
| D4 gap-window T3B rows / T3 changed | — | 16 / 0 | |
| TGA: consented NZ, no ARTG match | 209 − 184 = 25 | 25, ≥ 18 known cancelled registrations | |
| TGA spot check of dated entries | — | 11 of 14 right; Keytruda +11 mo, Striverdi +6 y, Aubagio +6 y | |
| Medsafe application-search failures | 16 | 16 (log.jsonl) | |
| forecast sha256 / n / base rate | 70b7aec5… / 125 / 6.9% | identical / 125 / 0.0686 | max Δp = 0 |
| forecast substances with match_names ≠ name / lapsed consent | — | 22 / 24 of 125 | |
| cohort entries with wrong T0 or wrong inclusion (reviewer) | "about 2%", "1 in 150" | ≈ 45 of 705 (6%); ≈ 23% of EMA-first | |

## Re-adjudication

Table: `review/reviewer_checks/readjudication.csv` (70 rows; evidence per substance in
`reviewer_checks/cache/evidence/<id>.txt`, built by `build_readj_sample.py` with the independent register snapshot,
the PHARMAC application tracker, TGA and MSW rows added to what the agent saw). Sample: 40 from the agent's two
samples (33 with a present T2 or T3, plus every flagged row) and 30 new (seed 20261030; 20 with a present date, 10
absent). It is enriched for present dates and is not a precision estimate.

- Reviewer: T1 57/64 (0.89), T2 66/70 (0.94), T3 69/69 (1.00); T0 or inclusion wrong in 5 of 70.
- Agent vs reviewer on the 40 shared rows: 4 substances disagree, all provisional-consent cases — atezolizumab (T1, T2),
  vemurafenib (T1, T2), tixagevimab (T1), cilgavimab (T1).
- New errors found in the 30: amivantamab (T1), epcoritamab (T1), tenofovir alafenamide (T1, T2 false absent).
- Other T0 findings in the sample: trastuzumab deruxtecan, nonacog beta pegol, human coagulation factor x (CBER/
  duplicate), crisantaspase and chlormethine (old substances).

## Process checks

- plan.md committed 8d0bc67 at 16:31; validation adjudications written 22:10:02 (v1) and 22:41:20 (v2); primary.json
  and stage_table.csv written 22:41:43; forecast written 22:42:09 and committed in 4577be4 at 22:42:18; `git branch
  -r --contains 4577be4` → origin/main. c0386fc (report) is not pushed. Ordering is as claimed.
- data/linked.csv was rewritten at 22:37:32 after link.py's 22:26:51 change (D6.3/D7), before the v2 evidence; the
  v1 evidence (22:05) therefore reflects pre-D6 linking, as deviations.md says.
- The 16 Oct 2026 Schedule Update (effective 1 Nov 2026) was downloaded and parsed before the freeze; none of the 125
  forecast substances appears in it (issue 16).
- No LLM-assisted matching, as stated. No pip installs were made into the study venv by this review.

## Plain-language summary, line by line

- "the regulator's own review: about 14%" → about 16% (n = 70, CI 13–19%), and say the 30%/14% split is from a
  different, smaller set than the 40% headline, or recompute on one set (issue 3, 14).
- "Waiting for the company to apply in New Zealand: about 30%" → about a quarter; 21 of 70 sponsors applied in NZ
  before the first FDA/EMA approval (issue 3).
- "7.7 years is a reasonable summary of it" → withdraw. The source figure is the mean application-to-decision time for
  29 decided applications; this study's equivalent is 3.4 years (6.4 for 2024–26 decisions); the censoring-aware
  medians are 12 years (consent→funding) and 8.7 years (application→approval) (issue 1).
- "The often-quoted '7.7 years to funding' is not exaggerated by leaving out medicines that were never funded ... If
  anything, the opposite holds" → withdraw; the source leaves them out by construction (issue 1).
- "Its regulator approved the same medicines a median of about 14 months earlier than Medsafe" → withdraw or
  restrict to "medicines still registered in both countries" (issue 7).
- "Only about three in ten have been approved by Medsafe, and about one in eight funded" → still approximately right
  after removing duplicates; say "roughly".
- "This measures process timing. It does not judge whether any funding decision was right" and the Māori and Pacific
  leadership note: accurate, appropriately scoped, keep.

## Files produced by this review

`review/review.md` (this file); `review/reviewer_checks/readjudication.csv`, `readjudication_sample.csv`;
scripts `probe1.py`–`probe5.py`, `recompute.py`, `cohort_checks.py`, `forecast_check.py`, `gap_tga_prov.py`,
`provisional_t1.py`, `build_readj_sample.py`, `pdf_text.py`; `cache/evidence/*.txt`, `cache/evidence_compact_rest.txt`,
`cache/forecast_repro.csv`, `cache/downloads/shawview_2023.pdf(.txt)`, `cache/downloads/bms_2026.pdf(.txt)`.
