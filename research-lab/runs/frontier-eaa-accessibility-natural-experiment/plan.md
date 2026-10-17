# Did the European Accessibility Act change the web? Preregistration

Lead: `frontier-eaa-accessibility-natural-experiment`. Written 2026-10-17, before any archived page is fetched. Code in
`code/` is committed with this plan; departures from the lead are in `deviations.md` (D1).

## 1. Question and hypotheses

The European Accessibility Act (Directive (EU) 2019/882) has applied to private-sector consumer services since
28 June 2025: e-commerce, consumer banking, passenger transport, e-books and electronic communications. No study has
used its sector-by-jurisdiction boundary as a natural experiment. Searches on 2026-10-17 found vendor scans that
compare the EU with the US at one point in time (AudioEye's 2026 index) and single-time-point audits that describe
themselves as pre-deadline baselines (Slovenian e-commerce, Austrian video platforms). None found a before-after
design with a comparison group.

**H1 (EU effect).** Among sites on 14 EU country-code domains, the density of automatically detectable WCAG 2.1 A/AA
failures per 1,000 DOM elements fell by at least 15% from 2024 to the post period (2025-10 to 2026-04) in sectors the
Act covers, relative to sites the Act does not cover.

**H2 (placebo).** The same in-scope vs out-of-scope contrast on .com.au, .co.nz and .ca changes by less than 5%.

**H3 (overlay substitution, restated from the lead; D1.3).** Among EU in-scope sites, those that newly installed a
third-party overlay script between 2024 and the post period improved their markup less than in-scope sites that did
not.

## 2. Unit and outcome

The unit is a site's homepage as archived by the Internet Archive, replayed unrewritten (`id_`). The outcome is
`y = log(1 + violation nodes per 1,000 DOM elements)`. It is measured by axe-core 4.10.2 under jsdom 25.0.1 with no page
scripts executed, restricted to a frozen set of 19 rules a static DOM can evaluate: image-alt, input-image-alt, label,
select-name, button-name, link-name, html-has-lang, html-lang-valid, valid-lang, frame-title, th-has-data-cells,
td-headers-attr, aria-required-attr, aria-valid-attr-value, aria-roles, duplicate-id-aria, heading-order, list and
definition-list. Contrast, focus and keyboard rules need rendering and are not measured. A snapshot with fewer than
50 elements (bot walls, redirects, empty client-side shells) or an axe error is dropped, and drops are counted.

Because no script runs, an overlay script cannot change the measured markup. The measure is the server-delivered page,
which is what the lead calls "the underlying markup".

## 3. Sampling frame (`code/frame.py`)

- **Frame.** The Tranco list 64VVX (downloaded 2026-10-17, sha256 354b006b…), restricted to these registrable domains:
  - 14 EU country-code domains (treated): .de .fr .it .es .nl .pl .se .fi .dk .ie .be .at .pt .cz;
  - .co.uk (the UK left the EU but its firms selling into the EU are covered: partly treated, reported separately);
  - .com.au, .co.nz and .ca (placebo).
- **Exclusions.** Public-sector domains are excluded (gov, gouv, gob, bund, govt, gv, mil labels), because the Web
  Accessibility Directive has covered EU public bodies since 2018–2020.
- **Draw.** Up to 300 sites per jurisdiction, at random (seed 20261017), from rank ≤ 200,000, widened to ≤ 400,000
  where fewer than 300 exist. That gives 18 jurisdictions and about 5,400 sites. `data/frame/MANIFEST.txt` records the
  sample's sha256.

## 4. Snapshots and coverage (`code/cdx.py`, `code/fetch.py`)

Ten target months: 2024-01, 2024-04, 2024-07 and 2024-10 (pre); 2025-01 and 2025-04 (anticipation); 2025-07
(transition); 2025-10, 2026-01 and 2026-04 (post). For each target, the 200-status text/html homepage capture closest to
the 15th within that month is used (https://domain/ or https://www.domain/). A site is eligible with captures in at
least 2 of the 4 pre months and 2 of the 3 post months. Fetching is polite (4 concurrent requests, backoff on 429/5xx)
and resumable; raw HTML is kept gzipped with its sha256.

## 5. Sector (`code/sector.py`, `code/validate_sector.py`)

Sector is assigned once, from the site's earliest eligible pre-period snapshot, so it cannot respond to the Act. Fixed
multilingual marker rules are searched in visible text and in href, class and id values:
- ecommerce: cart, basket and checkout terms in 14 languages;
- banking: online-banking terms, account terms, or a bank name in the domain;
- transport: timetables, flights, train and bus tickets;
- telecom: mobile tariffs, broadband, SIM, e-books.

A site is in scope if one sector has ≥ 2 distinct markers (or a bank-name domain), out of scope if no sector has any
marker, and ambiguous (excluded) otherwise.

**Validation.** 60 rule-in-scope and 60 rule-out-of-scope sites are drawn (seed 20261019) and shown to the adjudicator
as domain, title and visible text, with the rule label hidden. The adjudicator is the agent running the study, not a
human. Precision is reported for each label. If either precision is below 0.80, a Refuted H1 is reported as
Inconclusive, because misclassification pulls the estimate toward zero. Supported verdicts are not downgraded, since
attenuation makes them conservative.

**Not modelled.** The Act exempts microenterprises providing services. They are not identifiable from a homepage;
including them also attenuates the estimate.

## 6. Overlay detection (`code/metrics.py`)

The raw HTML is searched for vendor signatures: accessiBe (acsbapp), UserWay, EqualWeb, AudioEye, Recite Me, Eye-Able,
MaxAccess, Allyable, enable.co.il and TruAbilities. A site is a *new adopter* if no pre snapshot has a signature and at
least one post snapshot does.

## 7. Analysis (`code/did.py`)

Two-way fixed effects with site and period fixed effects; standard errors are clustered by site. Anticipation and
transition months are excluded from H1–H3 and kept in the event study.

**H1**, EU sites: `y = site FE + period FE + b·InScope·Post`, with relative change `exp(b) − 1`.
- Supported if `exp(b) − 1 ≤ −15%` and the 95% interval's upper end is below 0.
- Refuted if the interval's lower end is above −15%.
- Inconclusive otherwise, subject to the sector-validation downgrade in section 5.

**H2**, placebo sites, same model.
- Supported if the 95% interval of `exp(b) − 1` lies within (−5%, +5%).
- Refuted if it lies wholly outside.
- Inconclusive otherwise.

**H3**, EU in-scope sites: `y = site FE + period FE + c·NewOverlay·Post`.
- Supported (substitution) if c's interval lies above 0.
- Refuted if it lies below 0.
- Inconclusive otherwise.

**Secondary analyses:**
- S1, the triple difference EU vs placebo;
- S2, the UK separately;
- S3, an event study (InScope × month, EU, reference 2024-10), showing pre-trends and anticipation;
- S4, overlay adoption as the outcome (linear probability DiD), EU and placebo;
- S5, the lead's literal windows (2024-01 + 2024-04 vs 2026-01 + 2026-04);
- S6, per-rule densities, descriptive.

## 8. Threats to validity

1. **Measurement scope.** 19 static rules are not WCAG conformance; rendered, interaction and contrast failures are
   missed. The outcome tracks markup quality, not usability for assistive-technology users.
2. **Client-side rendering.** Script-built pages show little markup without scripts. They mostly drop out under the
   50-element floor, and a site that moves to client rendering changes its measured page. Element counts are reported
   by group and period.
3. **Archive selection.** Wayback capture frequency depends on popularity and crawl policy, and could differ by group
   over time. Capture counts are reported.
4. **Spillovers.** Out-of-scope EU sites and placebo sites share vendors, CMS themes and global firms with treated
   sites. Platform-level fixes (a Shopify theme update, say) would reach in-scope sites everywhere, which the placebo
   and triple difference address.
5. **Concurrent events.** WCAG 2.2 (October 2023), the US DOJ Title II rule (April 2024, public sector) and national
   transpositions on different dates. The event study shows timing.
6. **Homepage only.** The Act covers whole services, but checkout and account pages are not archived reliably.

## 9. Outputs

`results/tables/primary.json`, `results/tables/per_rule_eu.csv`, sector validation tables, the frame sample and its
manifest, figures, and a report with a plain-language summary. Fetched HTML is kept on the lab's HDD, not released
(third-party content); the snapshot list (timestamps and URLs) is released so anyone can re-fetch.
