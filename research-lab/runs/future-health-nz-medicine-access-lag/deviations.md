# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 16:31 NZDT — before any Medsafe, PHARMAC or PBS date was linked

1. **Australian benchmark restricted to T0 2019–2024.** Historical PBS listing dates are no longer openly available
   (legacy extracts discontinued; the public API holds 12 months). The Medicine Status Website covers submissions from
   about 2019 (plan section 6).
2. **Stages refined.** Medsafe's application search gives a submission date, so the lead's "regulatory stage" is
   split into the sponsor's filing delay (T0→T1) and Medsafe's review (T1→T2). H1a keeps the lead's definition
   (T0→T2).
3. **Primary window 2010–2023 for H1**, following the critic's note on the February 2024 parallel-assessment and 2026
   Rule of Two changes; 2024 is reported separately.
4. **Entity resolution** by deterministic name normalisation, not RxNorm/ATC tooling, validated by an agent check of
   150 substances. No LLM-assisted matching.
5. **No PHARMAC application dates.** The PHARMAC application tracker is not used, so the funding stage runs from
   Medsafe consent, as in the lead, not from a funding application.

## D2 — 2026-10-17 16:38 NZDT — before any Medsafe, PHARMAC or PBS date was linked

1. **T3 from PHARMAC's monthly XML archive instead of the Schedule Update PDFs.** Two archives exist:
   - the community Pharmaceutical Schedule as monthly XML, 2006–2026 (/pub/schedule/archive);
   - the Hospital Medicines List (Section H) as monthly XML, 2011–2025, plus the current file (/pub/HML).

   Schedule Updates stop reporting Section H changes after 2013, and their PDF layouts vary. So:
   - T3B is the first monthly community Schedule (Section B, including PCT) in which a Chemical, or a Formulation of
     a combination, contains the substance's name;
   - T3H is the same for the HML;
   - T3 is the earlier of the two, dated to the edition's effective month;
   - the Schedule Update PDFs are kept for the validation cross-check.
2. **Old-substance exclusion.** EMA-first substances have no new-active-substance flag. Old medicines first
   centrally authorised inside a 2010+ combination enter the cohort: the first crawl rows include acetylsalicylic
   acid. A cohort substance is therefore excluded as not new if:
   - its Medsafe consent (T2) is more than 1 year before T0; or
   - it is present in the first available community Schedule XML (2006) or more than 1 year before T0.

   Counts are reported. The rule uses only the direction "older than its own first international approval", so it
   cannot shorten or lengthen any included lag.
3. **Crawler.** Medsafe results stream in after the page loads. The first crawler version waited a fixed 1.2 s and
   missed application rows; it was replaced before any results were used (commit de1125a), and the crawl restarted
   from scratch.

## D3 — 2026-10-17 18:51 NZDT — additional sources from UoA-eResearch/pharmac (suggested by the user), before any date was linked

The user pointed to https://github.com/UoA-eResearch/pharmac (commit 3e3e850, 2026-10-13; files copied to
`data/raw/uoa_pharmac/` with SHA256SUMS). Three of its datasets are added. Nothing in it had been linked to the
cohort before this entry.

1. **PHARMAC application tracker** (`pharmac_approvals.csv`, 2,015 funding applications): application-received
   dates, stage dates, decision dates and outcomes.
   - **New dates per substance** (matched with the same whole-word rule on Chemical_Name__c):
     - T_app, the earliest funding application received;
     - T_dec, the first decision recorded as an approval to fund.
   - **New secondary decomposition** of the funding stage among funded substances: Medsafe consent to funding
     application (T2→T_app) and application to listing (T_app→T3).
   - **H3 extension.** The "7.7 years to a funding decision" claim is also checked on application-based durations
     (T_app → decision, and T2 → decision), under the same three denominators: decided only; all applications with
     undecided ones censored; all consented substances. H3's preregistered verdict still uses T2→T3.
2. **Medsafe register snapshot** (`medsafe_register.csv`, 14,828 products, scraped by wildcard search on
   2026-03-30). It is an independent scrape of the same register, used to cross-check T2 for every cohort substance
   (agreement within 31 days, or both absent), alongside the 150-substance hand check. It is not used to fill gaps,
   so the primary T2 remains this study's crawl.
3. **TGA ARTG** (`tga_artg.csv`, 97,618 entries with RegistrationDate). T_TGA is the earliest RegistrationDate
   among ARTG entries whose name contains the substance. This gives a new **secondary regulatory benchmark** for the
   whole 2010–2024 cohort:
   - median T2 − T_TGA among substances with both;
   - Kaplan–Meier share approved by 2 and 5 years from T0, in NZ (T2) and Australia (T_TGA).

   It compares regulators, not funders; H2 (PBS funding) is unchanged and still limited to T0 2019–2024. Limitation:
   the ARTG public summary lists current entries, so a substance whose first entry was cancelled shows a later date.

Licences: Pharmac CC BY 4.0; TGA CC BY 4.0; Medsafe Crown copyright. The report credits the repository.

## D4 — 2026-10-17 18:53 NZDT — XML archive gap filled from Schedule Update PDFs, before any date was linked

The community-Schedule XML archive has no editions for January 2018 or for June 2024 to December 2025 (20 months).
That was checked against the archive's own directory listing: the files do not exist. The HML archive is complete.
A community listing first made in the gap would otherwise be dated to the next available edition, up to 19 months
late. `code/su_listings.py` therefore parses the detailed "New Listings – effective <date>" sections of every
Schedule Update PDF (upper-case chemical headers). Listings effective inside the two gap windows are added as T3B
candidates, and T3B is the earlier of the XML first edition and a gap-window Schedule Update listing. Outside the
gaps, the PDFs are used only for validation.

## D5 — 2026-10-17 20:19 NZDT — cohort cleaning and Medsafe retries, before any date was linked

1. **Nine cohort entries excluded as not new active substances.** All surfaced through failed Medsafe searches.
   - Six FDA "X and hyaluronidase" products: subcutaneous co-formulations of antibodies already approved
     (atezolizumab, daratumumab, efgartigimod alfa, ocrelizumab, pertuzumab–trastuzumab, trastuzumab). FDA writes
     them as one ingredient string with "AND", so cohort.py's semicolon split kept them whole.
   - "hydrogen", a salt-stripping artefact of potassium hydrogen carbonate (Sibnayal).
   - "air polymer a" (ExEm Foam, ultrasound contrast) and "brilliant blue g" (TissueBlue, surgical stain), diagnostic
     and surgical agents the name filter missed.

   The cohort is now **722**. `code/cohort.py` lists each exclusion with its reason.
2. **Medsafe Application searches that timed out** (popular ingredients with many applications) are retried with a
   60 s poll instead of 20 s. NexoBrid's normalised name ("concentrate of proteolytic enzymes enriched in bromelain")
   is searched as "bromelain", where the generic fallback word "concentrate" had returned huge result sets.

## D6 — 2026-10-17 22:13 NZDT — after the linking validation, before any lag was computed

1. **Validation outcome (plan section 4).** 150 substances were adjudicated by the agent against the saved evidence.
   - **Precision:** T1 0.985 (131/133), T2 0.966 (143/148), T3 0.979 (139/142), all above the 0.90 threshold.
   - **Among present dates only:** T2 0.95 (38/40), T3 0.94 (17/18).
   - **Absences.** Those scored "correctly absent" were also checked against the independent Medsafe register and
     PHARMAC text, with a loose substring match on the first seven letters.
   - **Recall.** In 50 random new PHARMAC chemicals (community from 2011, HML from 2014), all 10 that are new active
     substances of 2010–2024 are in the cohort, with T3 equal to that listing.
   - **Result:** the T1–T3 linking stands without the plan's revision.
2. **What validation did not cover: T0 and duplicates.** The plan validated T1–T3 only. The evidence showed two kinds
   of T0 error, and an audit of every EMA-first substance for an earlier FDA approval (by first word or brand,
   `data/validation/t0_audit_candidates.csv`) confirmed both:
   - **The same drug twice, under FDA and EMA name variants:** salts and esters, moiety versus prodrug, combination
     strings, and one EMA typo ("ledispavir"). Sixteen variants are merged into their canonical substances, with the
     earliest approval as T0 (`cohort.py` ALIAS).
   - **FDA approvals under a proper or brand name** the INN match cannot see: Adynovate (rurioctocog alfa pegol, FDA
     2015-11-13) and Velphoro (sucroferric oxyhydroxide, FDA 2013-11-27). These become T0 overrides.
   - **Not new:** gemtuzumab ozogamicin was first approved by the FDA in 2000 and re-approved in 2017. It is excluded.

   The cohort is now **705**. This is a pre-analysis correction of the cohort definition, not a revision of the
   validated T1–T3 linking. FDA biologics approved under a different brand and proper name than in the EU remain
   undetectable by rule: 1 of 150 sampled. Their T0 is late, and their lags are understated.
3. **Alias-aware matching, and a first-word rule** (`link.py` patterns). Each substance matches its canonical name
   or any alias, and Medsafe rows from every alias's search are pooled. A multi-word name also matches its first word
   alone when that word has at least 7 letters and no substance first approved before 2010 starts with it. Medsafe
   lists conjugates and prodrugs by the first word only ("Polatuzumab", "Ceftaroline", "Mirvetuximab"); the condition
   keeps "aripiprazole lauroxil" and "gabapentin enacarbil" from matching the older drugs. This changes the linking
   after validation, so a **fresh 100-substance validation** (seed 20261023) is run on the result before any lag.
4. **Provisional consent.** Medsafe's product approval date appears to be the latest consent. Where a provisional
   consent was converted to full, the first consent is not recorded (seen in 2 of 150: Paxlovid, glofitamab), and T2
   is late. The report quantifies how many substances have a "provisional" application or status.

## D7 — 2026-10-17 22:41 NZDT — fresh-sample re-validation after D6, before any lag was computed

100 new substances (seed 20261023, excluding the first 150) were adjudicated against the D6 linking.
- **Precision:** T1 1.000 (97/97), T2 0.990 (99/100), T3 1.000 (98/98).
- **Among present dates:** T2 27/28, T3 12/12.

The first-word rule's error found during D6 checks was fixed before this sample was drawn: tezacaftor had matched
"ivacaftor" through an alias. The rule now applies to canonical names only, never to a word that is another cohort
substance, and not to a stoplist of generic words.

**Residual cohort impurity.** Across both samples, about 2% of entries (4 of 250) are old substance concepts under a
new EU name: pancreas powder (pancreatin), para-aminosalicylic acid, "human coagulation factor viii" and
alpha1-proteinase inhibitor. They inflate the unfunded and unconsented counts. They are reported, and a sensitivity
drops EMA-first substances whose name is a generic class description.
