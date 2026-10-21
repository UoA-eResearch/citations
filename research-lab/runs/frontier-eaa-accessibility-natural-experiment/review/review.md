# Independent review: frontier-eaa-accessibility-natural-experiment (draft 0c44d7a)

Reviewer: independent adversarial subagent, 2026-10-21. Everything below was computed from files on disk under the
run directory; nothing was fetched from web.archive.org or Common Crawl. Scripts and their outputs are in
`review/reviewer_checks/` (`c1`–`c10`, each with a `*_output.txt`; caches under `cache/`).

## Verdict: **fix first**

The preregistered specification reproduces exactly, the design checks hold (flat pre-trends, in-time placebo at zero,
randomisation-inference p = 0.002, no Wayback or bot-wall artefact behind the effect), and the sign of the EU
in-scope relative change is robust. What is not robust is the headline the report leads with: that the change is
"−15% or larger" and that "violation density fell 17%". The point estimate (−17.3%) clears the preregistered bar by
2.3 points; about half of the reasonable variants I ran land on the other side of it, and every mean-based estimator
gives −8% to −13%. The report has to carry that fragility in its verdict line, and it must fix two classification
defects before the numbers are final: 56 EU control sites (7% of the control group) were labelled "out of scope"
from a stub page with under 200 characters of text, among them obvious in-scope firms (a telecom operator, a bank, a
ferry line, two Skyscanner domains, a pharmacy chain), and a fresh blind re-adjudication puts in-scope precision at
0.77, below the plan's own 0.80 bar. Neither fix is a re-do; both are a few lines of code, a re-run of `did.py`, and a
rewritten summary.

## What holds

- **Reproduction.** H1, H2, S1, S2, S5 and all nine event-study coefficients reproduce to four decimals from an
  independent Frisch–Waugh implementation (`c6_did_recompute.py`, section A). `did.py` is byte-identical to the
  preregistered commit 5a95d1e.
- **Design checks** (c6 A–C). Joint Wald test of the three pre-period coefficients: p = 0.39; with the two
  anticipation quarters, p = 0.59. Linear in-scope pre-trend 2024-01 to 2025-04: −0.6%/quarter (SE 1.6%). In-time
  placebo (2024-01/04 vs 2024-07/10): −2.3% [−11.1%, +7.4%]. Randomisation inference, in-scope label permuted
  across 1,023 EU sites 2,000 times: two-sided p = 0.002. Balanced panel (sites seen in all 7 quarters): −17.5%.
- **Measurement.** axe 4.10.2 / jsdom 25.0.1 as declared; a re-run of `axe_run.js` on 50 random snapshots matches
  `metrics.jsonl` exactly (50/50); all 19 rules execute (the three that never appear in `by_rule` return passes or
  "incomplete", not violations) (`c4`).
- **Store.** 16,666 files, no duplicates in `metrics.jsonl`, sha256 matches the fetch log on 200 sampled files,
  fetch timestamps equal the CDX picks, eligibility recomputes to exactly the 1,741 sites in `eligible.jsonl` (`c1`).
- **Not artefacts.** Wayback replay markers (`web.archive.org`, wombat, `__wm`) appear in 18–20 of 16,666 files
  (0.1%), with no period pattern. Dropping bot-wall-flagged snapshots or sites leaves H1 at −15.7% / −15.4%. The
  20 in-scope sites that newly reached zero violations after the Act serve full pages: 19 of 20 have as many or more
  links and as much body text as their own pre-period snapshots; only biobike.es (284 elements, 8 links) looks like a
  shell (`c3`, `c9`). The improvement is real markup change.
- **Ordering.** First HTML file written 2026-10-18 03:29:31, after D5 (2026-10-17 18:55). D6 and D7 precede
  `did.log` (2026-10-20 09:44). Analysis code unchanged since preregistration; `sector.py` changed only at D2.
- **Report arithmetic.** Every number in `report.md` that I could trace matches `primary.json`, and `report.html`
  carries the same numbers.

## Findings

Severity: **High** = changes a headline claim or verdict wording; **Medium** = must be fixed or disclosed before
publication; **Low** = disclose or tidy.

### 1. (High) The "−15% or larger" magnitude is not robust; the sign is

Evidence (`c6_output.txt`, `c7_output.txt`, `c9_output.txt`):

| specification | relative change | 95% CI | H1 rule |
|---|---|---|---|
| preregistered: log(1 + density), TWFE | −17.3% | −28.8, −3.9 | Supported |
| drop snapshots with zero violations | −14.5% | −25.9, −1.5 | Inconclusive |
| drop sites with any zero-violation snapshot (190 treated) | −14.1% | −25.6, −0.8 | Inconclusive |
| log(1 + violation nodes), unnormalised | −14.7% | −27.2, −0.1 | Inconclusive |
| drop .fi (leave-one-country-out; all 13 others Supported) | −14.9% | −26.7, −1.1 | Inconclusive |
| ratio of means, raw density | −13.1% | | |
| PPML (Poisson, offset log elements, site + period FE) | −8.1% | −24.8, +12.4 | |
| median of site-level long differences | −12.8% | | |
| drop the 5 most influential in-scope sites (of 230) | −11.3% | | |
| log(0.1 + density) | −22.1% | −38.1, −2.0 | Supported |
| winsorised 1/99, 5/95; trimmed; ≥200 elements; balanced panel; drop 2024-01; drop 2025-10; e-commerce only | −16.0% to −18.3% | | Supported |
| drop 2026-04; post includes 2025-07; drop bot-wall flags | −15.4% to −16.3% | | Supported |

The leverage is concentrated: 20 of the 226 in-scope sites with both periods carry 54% of the in-scope total change
in y, and the 20 sites that first reached zero violations after the Act carry most of the gap to the bar (without
them, −6.4%). Those pages are genuine (finding list above), so this is not an artefact, but a −15% bar passed on the
strength of a few dozen sites whose log(1 + x) fell to zero is not "the EU in-scope relative change is ≤ −15%" in any
robust sense. Mean-based estimators, which weight a fall from density 45 to 0 by the 45 rather than by log(46), say
−8% to −13%.

Fix. Keep the preregistered verdict line, but qualify it where it appears: "Supported under the preregistered
specification; the interval runs from −4% to −29%, and the −15% bar is not met under several reasonable variants
(mean-based estimators −8% to −13%). The robust finding is a relative fall of uncertain size, not a fall of at least
15%." Add the sensitivity table (or `c6_output.txt`) to the report. In plain terms, replace "fell about 17%" with
"fell by somewhere between a few percent and a quarter; our best single estimate is about a sixth".

### 2. (High) "Violation density fell 17%" is not what exp(b) − 1 estimates

exp(b) − 1 is the relative change in (1 + density), not in density. With median in-scope density 9 pre and 5 post,
the "+1" is not negligible; the preregistered threshold was set on exp(b) − 1 and is therefore met on its own terms,
but the report's sentences ("Violation density on in-scope EU homepages fell 17%", "the covered sites' error rate
fell about 17%") describe a different quantity. The mean-based figures are in finding 1.

Fix. Say "the index log(1 + violations per 1,000 elements) fell 17%" where the number is given, and report the
ratio-of-means (−13%) and PPML (−8%, n.s.) alongside as the density-scale translation.

### 3. (High) Control-group sites labelled "out of scope" from a stub page; fresh in-scope precision 0.77

`sector.py` returns `out_of_scope` whenever no marker fires, including when the earliest snapshot is empty, a
redirect stub, a language chooser or garbled bytes. 56 EU sites (7% of the 827 EU controls), 15 placebo and 4 UK
were labelled from a page with under 200 visible characters (`c10_output.txt`). The EU list includes drei.at and
vodafone.nl (telecom operators), csob.cz (a retail bank), vikingline.fi and costacruceros.es (passenger transport),
skyscanner.pt and .se, 48.ie, neonet.pl, staples.pt, apoteket.se, willys.se, swiatksiazki.pl and
shop-swimmingpool.at. These are treated units sitting in the control group. Non-differential misclassification
attenuates b, so the direction is conservative for a Supported verdict, but it is a defect in the preregistered
procedure's implementation, not a design choice, and its size is unknown until it is re-run.

Fresh blind re-adjudication (`c8`, 60 sites not in the D6 sheet, seed 20261021; my labels in
`cache/fresh_blind_labels.csv` were written before `cache/fresh_blind_key.csv` was opened): in-scope precision 23/30
= 0.77, out-of-scope 25/30 = 0.83; pooled with D6, 75/90 = 0.83 (CI 0.76–0.91) and 78/90 = 0.87. In-scope false
positives: tv2.dk (TV news; "basket" matched "Basketball"), csfd.cz (film database with a shop link), imma.ie
(museum), part-time.ie (job board), banqueducanada.ca (central bank, via the bank-domain rule), saferinternet.at
(NGO), nationalwelding.com.au (industrial). Out-of-scope false negatives: vinted.nl (major marketplace, JS-rendered
homepage), grapesc.cz (ISP; no Czech telecom marker), and three stubs (gocar.be, tsbohemia.cz, ffr.fr).

Marker leakage (`c5_output.txt`): `basket` has no word boundary and matches "Basketball" (10 in-scope sites, most
of which also have cart/checkout); the bank-domain regex `bank|...|spar` fires on bankenverband.de (association),
banqueducanada.ca, banksy.co.uk, valsparpaint.co.uk, british-business-bank.co.uk; "transport" fires on
annuaire-horaire.be (opening hours) and on idealo.at/.it (price comparison) via a flights link. 206 of the 230 EU
in-scope sites are e-commerce; banking 14, transport 6, telecom 4.

Fix. (a) Label a site from its earliest pre-period snapshot with at least ~300 visible characters, and mark sites with
no such snapshot "unclassifiable" (excluded), then re-run `did.py` and report both versions. (b) Add `\b` to
`basket`; drop `spar` from the bank-domain regex. (c) State that the in-scope group is 90% e-commerce and that H1 is
in practice an e-commerce result; the non-e-commerce estimate is −22% [−46%, +12%] on 24 sites. (d) Report the
pooled precision 0.83/0.87 and note that the fresh in-scope figure fell below the plan's 0.80 bar (which only governs
a Refuted H1, so it does not change the verdict).

### 4. (Medium) The placebo (H2) was untestable by design, and the triple difference is the real test

The H2 rule needs the 95% interval inside ±5%, i.e. SE(b) ≈ 0.025. The achieved SE is 0.135; even the full 450-site
placebo frame (before D5) would have given roughly 0.095. H2 could never have returned "Supported". The report says
the placebo is "too imprecise" and gives an MDE of "about 32%"; that MDE is for a decrease only (an increase would
need +46%). Among out-of-scope sites, EU vs placebo moves −5.4% [−19.7%, +11.4%] after the Act; among in-scope
sites, −24.5% [−41.6%, −2.3%] (`c6` G). The triple difference (−20%, [−41%, +8%]) is the evidence on "a worldwide
shift", and it is not significant.

Fix. Say that the H2 band was unattainable at this sample size and should be read as a design limitation, give both
MDE directions, and move the two EU-vs-placebo contrasts above into the report; they are the clearest statement of
what the placebo can and cannot rule out.

### 5. (Medium) The "sites without enough captures" exclusion is mostly homepages that redirect, and it removes large firms

530 of 2,700 half-sample domains (20%) returned zero Wayback captures at both `domain/` and `www.domain/`; the rate
has no Tranco-rank gradient (median rank 120k vs 125k for captured domains) and is highest on .be (37%), .at and .fi
(29%). The CDX query filters `statuscode:200` and matches the root URL exactly, so a site whose root is a 301 to
`/nl/`, `/de-de/` or a .com is "zero captures". The random sample of these domains (`c1`, console) is DNS/CDN hosts
plus firms such as allianz.at, jysk.be, hubo.be, cofidis.fr, deliveroo.be, royallepage.ca, volkswagen.es and
keukenhof.nl. I could not confirm this with an unfiltered CDX query (forbidden by the brief), so it is an inference
from the domain names and the Belgian/Finnish pattern; one unfiltered query per excluded domain would settle it.
Separately, 11 domains whose CDX query still errored after retries were dropped without mention (9 EU), and 44
page fetches failed (31 connection errors, 13 HTTP 500) and were never retried, leaving hamilton.ca and getlocal.ie
below the 2-pre/2-post rule inside the panel.

Fix. Describe the exclusion as "no 200-status capture of the root URL", not "not archived"; note that it removes
multilingual and multinational consumer firms, which are disproportionately in scope; disclose the 11 CDX errors and
44 fetch failures.

### 6. (Medium) H3's departure from the preregistered rule is right but unlogged; "not testable" needs a deviation entry

With one new adopter (domainhotelli.fi) the clustered SE (0.075) is meaningless and the plan's rule returns
"Refuted". The report's "not testable" is the correct reading, but it is a post-hoc departure from `plan.md` §7 and
belongs in `deviations.md` as D8 with the rule that would have been needed (e.g. a minimum of 10 adopters). Also,
the report's "Among EU sites the share went from about 0.5% ... to about 1%" matches all-EU snapshots (0.50% to
0.97%); `primary.json`'s `share_overlay` is in-scope sites only, so cite the right source.

### 7. (Low) D6 blinding was by instruction, not "by construction"

The adjudicator was a general-purpose subagent with full file access that was told not to open the key. I checked its
transcript (`~/.claude/projects/-mnt-citations/14121cdb-.../subagents/agent-a6c41efd8a33b86b0.jsonl`): 11 tool calls,
reading only `sector_sample.jsonl` in eight chunks, then writing the CSV; it never opened `sector.csv` or
`sector_key.csv`. So the labels were blind in fact. D6's "keeps the adjudicator blind to the rule by construction"
should read "by instruction, verified from the transcript". The prompt also primed the adjudicator with the rule's own
markers ("cart, basket or checkout"), which inflates agreement on the in-scope side. The sample was labelled 8 seconds
before the D6 commit (07:26:06 vs 07:26:14 NZDT); trivial, but the deviation should say "as" rather than "before".

### 8. (Low) Composition and drops: small, in the direction that favours the result, and should be shown

Drop rates (< 50 elements or axe error) are 0.8% pre vs 2.6% post for EU in-scope and 6.5% flat for out-of-scope;
the in-scope share of zero-violation snapshots rises from 4–6% to 10–13% while out-of-scope rises 19% to 25%
(`c2_output.txt`). The 79 timeouts are huge pages (median 1.15 MB); in-scope timeouts are 2 pre, 6 anticipation, 6
post, almost all marionnaud.at and marionnaud.it (7 of 10 snapshots each), which therefore contribute nothing. The
report omits 14 further axe errors (jsdom selector SyntaxErrors on ids with backslashes), 7 of them on tjareborg.fi
and 4 on thegoodguys.com.au (placebo, in scope, all post). Add a drops-by-group-and-period table and the 14 errors.

### 9. (Low) jsdom parses `<noscript>` content as elements

Under `runScripts: "outside-only"` the parser treats scripting as disabled, so `<noscript><img ...></noscript>`
tracking pixels (no alt) are counted by image-alt; 14–17% of in-scope snapshots contain one, 10–13% of out-of-scope,
both declining about 2–3 points over the panel. Not a driver (image-alt DiD −15% [−25%, −5%]; link-name −14%;
button-name −11%; every other rule within ±2%; all rules except image-alt and button-name together −12% [−24%, +1%]),
but a browser would not count them. Note it under measurement scope.

### 10. (Low) Report wording

- "It shows that the EAA boundary separated EU homepages' measured accessibility" overstates for the reasons in
  findings 1–3; "the boundary predicts a relative fall in the index" is what the data show.
- "Covered sites and uncovered sites tracked each other closely" is supported (finding list above); keep.
- "Sector rules misclassify about one site in eight": with the pooled figures it is about one in six for in-scope.
- The MDE sentence should say the study was powered for −19%, i.e. *below* the bar's resolution: a true −15% effect
  would be detected under half the time.
- "In plain terms" should state that nine in ten covered sites are online shops, and should drop "fell about 17%" for
  the hedged phrasing in finding 1.

## Required before publication

1. Re-run with stub-labelled sites excluded (and `basket`/`spar` fixed); report both estimates (finding 3).
2. Add the sensitivity table and the mean-based estimates; rewrite the verdict line and "In plain terms" to carry the
   magnitude uncertainty (findings 1–2).
3. Disclose the e-commerce composition, the redirect mechanism of the exclusion, the 11 CDX errors, 44 fetch failures
   and 14 selector errors; log H3's "not testable" as D8; correct the D6 blinding wording (findings 3–8).

## Scripts

`c1_cdx_fetch_integrity.py` (CDX, eligibility, fetch log, sha256, discarded-attempt cross-check);
`c2_metrics_integrity.py` (duplicates, errors, timeouts, drop rates by group × scope × period);
`c3_html_artefacts.py` (Wayback and bot-wall scan of all 16,666 files → `cache/html_flags.csv`);
`c4_axe_rerun.py` (50-snapshot re-run, rule coverage); `c5_sector_leakage.py` (marker contexts for all in-scope
sites → `cache/inscope_marker_hits.csv`); `c6_did_recompute.py` (independent TWFE, event study, pre-trend tests,
randomisation inference, sensitivities); `c7_zero_violation_influence.py` (site-level changes, zero-violation pages,
leave-one-site-out → `cache/loo_influence.csv`); `c8_fresh_blind_sample.py` (fresh 60-site blind draw; labels and
merge in `cache/fresh_blind_*.csv`); `c9_shell_check_and_counts.py` (full-page test for newly-zero sites, PPML,
overlay count); `c10_stub_controls.py` (stub-labelled sites by label and group).
