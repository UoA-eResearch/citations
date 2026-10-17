# Independent review: ancestral-tk-notice-machine-readability

Reviewer: independent adversarial review of the pre-review draft (commit 1227857), 2026-10-18. Everything I
recomputed, re-scored or probed is under `review/reviewer_checks/` (index at the end). 79 live API requests were
made, one at a time, cached under `review/reviewer_checks/cache/`.

## Recommendation: fix first (text, tables and three scorer calls; no new fetching needed)

Both preregistered verdicts survive recomputation: H1 is 1 / 48,361 (exact 95% CI 0.0001–0.012%), H2 is
7,750 / 17,762 = 43.6% (record-cluster bootstrap 43.5–43.7%), and the hand check and D4 are sound. But the report
as written should not be published, for four reasons that change what a reader would conclude:

1. **H2's threshold crossing is a property of the view list, not of the records.** Every Neotoma record (1,971 of
   1,998) shows the same pattern: exactly four of nine views drop the element, so the pooled share is 4/9 adjusted for
   203 unavailable OpenAIRE views. Remove any one of those four views and H2 is *Refuted* (36.5–37.4%); remove any of
   the other five and it is 49%. The bootstrap interval of ±0.1 points is computed over 1,998 records with 7 distinct
   patterns and says nothing about this. The report hints at it ("the loss is set by the format") but never states it.
2. **The mechanism given for the citation formats is wrong.** The report says BibTeX and CSL-JSON "drop it, as they were
   not designed to carry rights". In fact DataCite's CSL-JSON and BibTeX carry a `copyright` field, and in all 2,000
   sampled DOIs it equals the *first* `rightsList` entry. Neotoma lists its CC licence first, so the Notice is cut; the
   Gump/Tetiaroa records list the Notice first, so it survives (and the CC licence is cut instead). The loss is a
   first-entry-only crosswalk rule in DataCite's converter, which is a different and more actionable finding.
3. **"Only one record anywhere" is not what was measured.** Two Gump DOIs (10.17913/100501.9190 and
   10.60950/100501.9190, "Moorea Biocode 1.0") carry a BC Label's text in `rightsList` with `rightsIdentifier`
   `bc-consent` / `bc-label` and a live Hub project on which that Label (BC Consent Verified, "Faarii", community
   Atiti'a Center) is applied. They fail the preregistered name-or-URI rule only because the text is the unfilled
   template. The report must disclose them, and the plain-language "anywhere" must go. The census also has a demonstrated
   false negative (10.48321/d190108951, Hub URI in `relatedIdentifiers`) because DataCite's free-text `localcontexts`
   query matches 2 records in the whole index (URIs are indexed as whole-domain tokens), and Zenodo's legacy JSON does
   not expose the custom rights entries that hold the Hub URIs.
4. **Care and accuracy edits**: a community is named in a list of repositories ("Dja Dja Wurrung material"); Tetiaroa
   Society is placed "on Mo'orea"; the one counted record is called a dataset (it is a thesis record); report.html's
   `<meta name="description">` describes a different study (Pythia-160M sparse autoencoders).

None of this requires re-fetching views. It requires: rewriting the H2 interpretation, fixing three scorer calls (two
OpenAIRE "preserve" and one Crosscite "degrade"; H2 unchanged), adding the view-set sensitivity table, adding the
Hub cross-check, adding a per-platform table with zeros and errors, and the text edits below.

## Numbered issues

Severity: **A** changes a conclusion or claim; **B** accuracy or completeness; **C** minor.

### Census (limb 1)

**1 (A). DataCite free-text channel cannot see URIs.** `code/census.py` line 46 runs `query=localcontexts` and nine
phrase terms. Live probe: `query=localcontexts` returns 2 records in all of DataCite; `"localcontextshub.org"` 4;
`*localcontexts* AND NOT prefix:10.21233` 14, of which 5 are not in the census raw data and one is element-bearing
(10.48321/d190108951, DMPTool "MOZEROA 2030" plan, Hub project e884d181 live, found only by
`relatedIdentifiers.relatedIdentifier:*localcontexts*`). The ADA Dataverse records with Hub URIs in descriptions were
found only because they also say "BC Notice". Records whose only element is a Hub/Notice/Label URI in a description,
relatedIdentifier, alternateIdentifier or subject, with no vocabulary name and no phrase "Local Contexts", are
invisible to the census. Fix: add field wildcard queries for `descriptions.description`,
`relatedIdentifiers.relatedIdentifier`, `identifiers.identifier`, `subjects.subject`, `rightsList.rights`, plus
`rightsList.rightsIdentifierScheme:"Local Contexts"` and the phrases `"localcontexts.org"` / `"localcontextshub.org"`
(about 10 requests), re-run `scan`, and state in the report that counts are lower bounds *for this reason*. Add the
DMPTool record (H1 denominator 48,362; 30 without Neotoma; verdicts unchanged).

**2 (B). TERMS omit two Notice names and all 30 Label names.** `detect.py` recognises "Attribution Incomplete Notice"
and "Open to Collaborate Notice", but `census.py` never searches for them, nor for any specific Label name ("BC
Provenance", "TK Attribution", ...). A record carrying only such a name is never fetched, so it cannot be detected.
Probes for `"BC Provenance"`, `"Attribution Incomplete"`, `"Open to Collaborate"` returned 29 records not in the census;
none is element-bearing (DataCite phrase search ignores punctuation: "1330-1300 BC), provenance unknown"), so no
count changes, but the gap is real. Fix: add the two Notice names and the Label names to TERMS, or say in the report
that name-only recall covers four generic names.

**3 (B). Zenodo's count is an API-visibility artefact.** The legacy JSON that `census.py` scans does not contain the
custom rights entries ("BC-Notice" with the Hub link) that DataCite holds for 10.5281/zenodo.10381316/7 and
15859523/4; the InvenioRDM serialisation (`Accept: application/vnd.inveniordm.v1+json`) does (probe z6/z7). Zenodo's
search `q=localcontexts` returns 0; `metadata.rights.title.en:"BC-Notice"` returns 2. The report's "Zenodo 1" is
therefore not comparable with the DataCite count of 6 Zenodo-hosted element-bearing DOIs. Fix: say so, and either scan
the RDM serialisation or report Zenodo as "not independently countable through its public JSON".

**4 (B). Harvard Dataverse: a structural zero, not a measured one.** The installation has 24 metadata blocks and none
for Local Contexts (probe `dv_metadatablocks`); `localcontextshub.org`, `localcontexts*`, `localcontexts` all return 0,
and `"Local Contexts"` returns 196 ordinary-language hits. The Dataverse integration is deployed elsewhere (ADA
Dataverse, whose records carry Notices in descriptions and were found via DataCite). Fix: report Harvard Dataverse as
"integration not installed; 0" and name ADA as the Dataverse instance where the element was seen.

**5 (B). GBIF machine tags were not queried as planned.** plan.md section 2 says "dataset search, and machine tags";
`census.py` `gbif()` only runs the text search and scans `machineTags` inside returned records. Probes with guessed
namespaces (`localcontexts.org`, `localcontextshub.org`) return 0, but the namespace is unknown. Fix: log as a
deviation, or query `/dataset?machineTagNamespace=` with the namespace Local Contexts documents.

**6 (B). RAiD: the public API exposes no `traditionalKnowledgeLabel` key for any of the 622 public RAiDs**, nor on
the single-record endpoint. Either none has a TK label or the field is omitted; the study cannot tell. Also
`URI_RE` would not match RAiD's schema URI form `localcontexts.org/labels/traditional-knowledge-labels/` (plural).
Fix: report "0 of 622 public RAiDs expose a TK label field" rather than a bare zero, and widen `URI_RE` to
`(label|labels|notice|notices|projects?)`.

**7 (C). re3data.** `query=` searches names, keywords and descriptions (`Neotoma` 1, `pollen` 3, `Indigenous` 10), so
0 for `localcontexts` means no indexed text mentions it, not that no repository *policy* does, which is what plan.md
promised. Say so.

**8 (C). Per-platform table missing; plan section 4 promises per-platform Wilson intervals, concentration by platform,
resource type and year, and a trend by year.** `census_by_platform.csv` lists only platforms with hits; the report
never states Dryad 0, Dataverse 0, RAiD 0, re3data 0, OSF unavailable. Fix: a nine-row table with count, status
(ok / error / unavailable), lower-bound note and Wilson interval. Also `logs/census.log` still reads "zenodo 0" and
"raid 25" from the first run; regenerate or annotate.

**9 (C). Error recording is honest.** OSF is recorded as `_unavailable` and reported as such (still 503 on
2026-10-18 across SHARE, `api.osf.io/v2/search` and `/v2/nodes`); D2 and D3 fixes are in place and the raw files
show 697 Zenodo and 622 RAiD records. Good.

### Detection and classification

**10 (A). The Biocode 1.0 records and the H1 numerator rule.** `analysis.py` line 32: `label_hub = has_label &
live Hub project`, where `has_label` needs a `/label/` URI or an exact Label name. 10.17913/100501.9190 and
10.60950/100501.9190 carry, in `rightsList`, "This Label is being used to verify that [community name or authorizing
party] have consent conditions in place..." with `rightsIdentifier` `bc-consent` / `bc-label`, scheme "Local Contexts"
and Hub project 71b32571 (live; Hub API: `bc_labels = [consent_verified "Faarii", community Atiti'a Center]`,
project created by Gump Station). This is a BC Label in DOI metadata, resolvable to a Hub project where a community
applied it. Under the preregistered rule it does not count (template text, no name, no URI); under the lead's wording
("community-authored, resolvable to a Hub project") it arguably does. Fix: keep the preregistered count as primary,
report the alternative (3 / 48,361 pooled, CI 0.0013–0.018%, still Supported; 3 / 29 = 10.3%, CI 2.2–27.4%, *Refuted*
by the rule without Neotoma), and have `detect.py` also read `rightsIdentifier` against the Label and Notice slugs.
Drop "one record anywhere" from the plain-language summary.

**11 (B). Without Neotoma, H1 is Inconclusive by the preregistered rule and the report does not say so.** 1 / 29:
exact CI 0.087–17.8% spans 0.1%. The report gives the numbers but the verdict line reads "Supported" without
qualification. Fix: state "Supported pooled; Inconclusive without Neotoma (point estimate 3.4%, 34 times the
threshold)". The pooled verdict is carried entirely by 48,332 copies of one institutional Notice.

**12 (B). "TK Open to Collaboration (TK CB)" is a Label name and the Neotoma mismatch is real.** Verified in every
Neotoma `rightsList`: text "TK Open to Collaboration (TK CB)" (the TK Open to Collaboration Label and its code), URI
`https://localcontexts.org/notice/open-to-collaborate/`, scheme "Local Contexts", `rightsIdentifier`
`open-to-collaborate` in 13,880 of 48,332. The report's description is accurate. Suggest adding that DataCite has a
de facto `rightsIdentifierScheme` "Local Contexts" (48,343 records), a cleaner census key than the URI wildcard.

**13 (C). `NOTICE_RES` misses hyphenated forms.** "BC-Notice" (5 DataCite records, and Zenodo's rights title) and
"BC-notice"/"tk-notice" are not matched because the Notice patterns use literal spaces while the Label patterns allow
`[ \-_]+`. `has_notice` is 23 of 29 non-Neotoma; it should be 25. No verdict effect. Fix: use `[ \-_]+` in
`NOTICE_NAMES`.

**14 (C). Re-adjudication of the 69 name-only hits: 69 / 69 agree** (`precision_readjudication.csv`). All 63 figshare
hits are University of Tasmania template fields "Traditional Knowledge Labels / Traditional Knowledge Notice /
Biocultural Notice" with empty values (checked programmatically: no UTAS record has a value); the two conference
abstracts and the journal abstract are prose; the Landcare / GBIF pair is genuine. Worth one descriptive sentence:
two institutions (UTAS, VUW) have built Local Contexts fields into figshare templates; 2 of 73 such records are filled.

### Crosswalk scoring (limb 2)

**15 (B). Three scorer calls are wrong; H2 unchanged.** An independent structural re-scorer (XML/JSON parsing of all
18,000 bodies, `rescore_views.py`) agrees with `views.py` on 17,997:
- OpenAIRE "preserve" for 10.5281/zenodo.13127018 and 13127019: the Hub URI is in `instances[].urls`, caught by the
  800-character window after `"license"` in `RIGHTS_FIELD["openaire"]`. Should be degrade. OpenAIRE then preserves in
  0 of 1,778.
- Crosscite "degrade" for 10.60950/100501.9190: the URI *is* in `rights_list[].rightsUri`, but the non-greedy regex
  `"rights_?[lL]ist"\s*:\s*\[.*?\]` stops at the `]` inside "[community name or authorizing party]". Should be
  preserve (1,992 of 1,998, matching DataCite XML).
Fix: parse JSON and walk keys rather than regex windows; re-run `analysis.py` and `figures.py`.

**16 (A). CSL-JSON and BibTeX: wrong mechanism (see summary point 2).** `copyright` equals `rightsList[0].rights` in
2,000 / 2,000 sampled DOIs. Of 17 sampled records with the Local Contexts entry first, all 17 carry it in
`copyright` (9 recognisably by name or URI; 8 as text the detector cannot recognise: 5 Attribution Incomplete Notice
text, 2 "BC-Notice", 1 Label template). Of 1,975 with it second, 0 do. Fix the text: "DataCite's CSL-JSON and BibTeX carry one rights entry, the first; the element
survives when a repository lists it first and is cut when the licence is listed first." Also note the scorer's
`RIGHTS_FIELD["csl_json"]` looks for `license|rights` and BibTeX has no rights pattern, so those 9 + 9 calls are
"degrade"; under plan section 3 ("a rights-type field, distinguishable from the licence") they are arguably
"preserve", since no licence is present at all. Either label is defensible; say which and why. No H2 effect.

**17 (B). JSON-LD "license = degrade" is fair but overstated in prose.** DataCite's JSON-LD emits
`"license": [CC URI, "https://localcontexts.org/notice/open-to-collaborate/"]`: the Notice is a bare URI in a field
whose semantics assert "licence". Degrade is the right preregistered call. But "a consumer cannot tell a governance
notice from a licence" should read "cannot tell *from the field*; only the URI's domain distinguishes them". Note that
this choice is conservative for H2 (it keeps 1,995 pairs out of the drop count); counting JSON-LD as drop would give
54.9%.

**18 (B). oai_dc preserves, but flattens.** `dc:rights` holds four untyped strings (CC text, CC URI, Label text, Notice
URI); the scheme attribute ("Local Contexts") and the pairing of text to URI are lost. "Carry it in every record" is
true; add that oai_dc loses the typing that lets a machine know it is Local Contexts, which is the same loss the report
criticises in JSON-LD, with a less misleading field name.

**19 (C). "Unavailable" is handled right.** All 220 are OpenAIRE `numFound: 0` with HTTP 200; all 1,780 found records
contain the queried DOI among their pids; a re-check of three Neotoma DOIs still returns 0, so they are not indexed
rather than transiently missing. Counting them as drop (44.3%) or as kept (43.1%) changes nothing. Note that OpenAIRE
merges versions, so 13127018 and 13127019 return the same record.

**20 (C). Hand re-score of 104 record-views** (`handcheck_rescore.csv`; all 60 non-JSON-LD degrades, both OpenAIRE
preserves, all three JSON-LD drops, 10 OpenAIRE drops, 8 JSON-LD degrades, 12 rights-view preserves, 9 citation-format
drops). Agreement with the scorer on drop vs not-drop: 104 / 104. Strict agreement: 83 / 104; the 21 differences are
issue 15 (3) and the `copyright` judgment of issue 16 (18). The study's own 100-record hand check is consistent with
this; its sampling (9 common + 2 rare per view) is sensible.

### Verdicts and candour

**21 (A). The view-set sensitivity must be in the report** (see summary point 1). Recomputed:

| H2 variant | drop / pairs | share | bootstrap 95% CI | verdict |
|---|---|---|---|---|
| as reported (D4, unavailable excluded) | 7,750 / 17,762 | 43.6% | 43.5–43.7% | Supported |
| without D4 (2,000 DOIs) | 7,754 / 17,780 | 43.6% | 43.5–43.7% | Supported |
| unavailable counted as drop | 7,970 / 17,982 | 44.3% | | Supported |
| without BibTeX | 5,761 / 15,764 | 36.5% | 36.4–36.7% | Refuted |
| without CSL-JSON | 5,762 / 15,764 | 36.5% | 36.4–36.7% | Refuted |
| without formatted citation | 5,752 / 15,764 | 36.5% | 36.3–36.6% | Refuted |
| without OpenAIRE | 5,978 / 15,984 | 37.4% | 37.3–37.5% | Refuted |
| without any one of the other five views | 7,750 / 15,764 | 49.2% | | Supported |
| only the six doi.org formats | 5,978 / 11,988 | 49.9% | | Supported |
| only views with any rights/licence field | 1,775 / 11,768 | 15.1% | | Refuted |
| Neotoma stratum | 7,681 / 17,536 | 43.8% | 43.7–43.9% | Supported |
| other publishers (27 DOIs) | 69 / 226 | 30.5% | 25.4–35.2% | Refuted |

Distinct per-record patterns across 1,998 DOIs: 7. The record-cluster bootstrap is therefore an interval over
essentially one record; the uncertainty that matters is which views count as "standard", and the preregistration
fixed that list. The report should say plainly: "the 40% threshold is crossed because four of the nine preregistered
views drop the element for every record; with eight views it would not be." The lead's phrase "≥ 40% of the standard
machine views" was made precise as record × view pairs (D1.4), which is fine, but the reader must see that the result
is the view count.

**22 (B). Neotoma's dominance is stated but not carried through.** "Dominated by one repository" appears, and the
stratum split is given; add that H1's pooled verdict and H2's pooled verdict are each Neotoma's verdict, and that
"other publishers" is Refuted for H2 (30.5%, upper bound 35.2% < 40%) and Inconclusive for H1.

**23 (B). The Hub cross-check belongs in the report.** Of the 20 Hub projects linked from element-bearing records, 17
resolve (3 are 404, as reported). At the Hub, 15 carry Notices only (Gump Station 7, Tetiaroa Society 3, Plant & Food
Research 1, four researcher-created), one carries a community-created BC Provenance Label (Te Roroa; the VUW record),
and one an institution-created project with a community-applied BC Consent Verified Label (Biocode 1.0). So the
DOI layer's Notice-heavy picture mirrors the Hub for these projects: Labels are rare at the source too. This supports
the report's "absence may be by design or newness" reading and should be cited for it. (`probes.md`, Hub table.)

### D4

**24 (C). D4 was justified and did not change the verdict.** The two excluded DOIs are a conference abstract and its
version DOI; H1 already excluded them. With them, H2 is 7,754 / 17,780 = 43.6% and "other" is 73 / 244 = 29.9%.
Ordering: handcheck_sheet.txt 05:54, handcheck.csv and deviations.md 05:56:00, primary.json 05:56:29, commits
582b476 (05:56) then e39b994 (05:57). That is consistent with "before H2 was computed", but cannot prove it: views.jsonl
was complete at 04:16 and `handcheck.py` prints the per-view result counts (needed to oversample rare calls), from
which the pooled share is one line of arithmetic. Fix: soften D4 to "before analysis.py was run; the per-view
distribution was necessarily seen when stratifying the hand check", and note that `analysis.py` was also modified in
e39b994 (the by-stratum table) in the same commit as the outputs, a small breach of code-before-outputs.

### Numbers

**25 (C). Every number in report.md matches primary.json, view_matrix.csv and view_matrix_by_stratum.csv**, and
report.html carries the same numbers (text-level comparison: no number present in one and absent from the other).
Captions match the figures. Three corrections follow from issues 10 and 15: the view table (OpenAIRE 0 / 6 / 1,772 /
220; Crosscite 1,992 / 6 / 0 / 0), the H1 alternative count, and "48,361 → 48,362" if the DMPTool record is added.

**26 (B). report.html metadata is from another study.** `code/build_report_html.py` line 102:
`<meta name="description" content="A preregistered test of whether sparse-autoencoder features of Pythia-160M ...">`.
Fix the template (the `_report_date` comment shows a similar copy-paste was already caught once).

**27 (C). F1 caption: "Zenodo and figshare hits also appear as DataCite DOIs, so platforms overlap."** The two VUW
figshare DOIs are *not* in DataCite's public index (REST `/dois/<doi>` 404, `query=doi:"..."` total 0; the handle
API resolves them). They were not deduplicated against DataCite because DataCite never returned them. Fix: "Zenodo
and GBIF hits also appear as DataCite DOIs and are counted once; the figshare DOIs are registered but not findable in
DataCite's public index." (Also interesting in itself: a DOI layer that cannot be searched.)

### Framing and care

**28 (B). Remove the community name from the repository list.** "ADA Dataverse (Dja Dja Wurrung material)" names an
Aboriginal community in a list whose stated purpose is to describe systems. The information is public in the records,
but the report does not need it. Suggest "ADA Dataverse (three datasets from a community-led project)". The report
rightly does not name Te Roroa, whose Label is the one counted record; keep it that way, and add one sentence that the
Label is the community's own statement and is not evaluated here.

**29 (B). Geography and record type.** Tetiaroa Society is on Tetiaroa atoll, not Mo'orea: "Gump South Pacific Research
Station (Mo'orea) and Tetiaroa Society (Tetiaroa)". The counted VUW record is a Master's thesis record
(`defined_type_name: thesis`), not a dataset. Gump Station's DataCite publisher name appears as both "Gump South
Pacific Research Station" and "UC Berkeley Gump South Pacific Research Station"; fine to merge, but say so.

**30 (C). Plain-language summary.** "Only one record anywhere" → "only one record in our census under our strict
rule, and two more that carry a Label's text without its name"; "followed 2,000 of these records" → "1,998"; "The
citation formats lost it ... almost always threw it away" → the first-entry explanation; add one sentence that for the
projects we could check at the Hub, Labels are also rare at the source. The rest is accurate and well pitched.

**31 (C). "Absence may be by design" is given its due** in the verdict block, the plain summary and the discussion. Good.
The Hub cross-check (issue 23) would turn it from a caveat into evidence.

**32 (C). H2b.** The warning regex (`(rights|licen[cs]e)[^.]{0,40}(omitted|removed|not (shown|included))`) is narrow,
so "no view warns" is weakly tested; since none of these formats has a mechanism for such a warning, the descriptive
claim stands. Say "no view has a field for it, and none was found".

## Recomputed numbers

| quantity | reported | recomputed | note |
|---|---|---|---|
| element-bearing records, deduplicated | 48,361 | 48,361 | 48,362 with the DMPTool false negative |
| Neotoma share | 99.94% | 99.94% (HHI 0.9988) | |
| H1 pooled | 1 / 48,361 = 0.002% (0.00005–0.012%) | 1 / 48,361, exact CI 0.0001–0.0115% | Supported |
| H1 without Neotoma | 1 / 29 = 3.4% (0.09–17.8%) | 3.45%, CI 0.087–17.76% | **Inconclusive** by the rule |
| H1 counting Biocode 1.0 Label text | not reported | 3 / 48,361 = 0.006% (0.0013–0.018%); 3 / 29 = 10.3% (2.2–27.4%) | Supported pooled; Refuted without Neotoma |
| name-only hits genuine | 2 / 69 | 2 / 69 (69 / 69 agree) | |
| Hub projects live | 21 / 24 URIs, 3 dead | 17 / 20 projects live, 3 dead; 2 carry Labels at the Hub | |
| H2 pooled | 7,750 / 17,762 = 43.6% (43.5–43.7%) | identical | Supported; flips to Refuted without any one of the four dropping views |
| H2 Neotoma / other | 43.8% / 30.5% (25.4–35.2%) | identical | other: Refuted |
| H2 without D4 | not reported | 43.6%; other 29.9% | unchanged |
| distinct record patterns | not reported | 7 | |
| view matrix | as table | OpenAIRE preserve 2 → 0, degrade 4 → 6; Crosscite preserve 1,991 → 1,992, degrade 7 → 6 | |
| scorer vs structural re-scorer | 100 / 100 hand check | 17,997 / 18,000 agree | |
| reviewer hand re-score | | 104 / 104 on drop vs not-drop; 83 / 104 strict | |
| H2b warnings | 0 | 0 | |
| DataCite census probes | | 1 element-bearing record missed of 34 novel DOIs returned by 7 extra queries | |

## Git and process

Code for census, detection, views and analysis was committed at 19:03 before any query (146e049); D2 and D3 fixes
precede the scan commit; precision.csv (23:08) precedes the views run (04:16 next morning) and D4 (05:56) precedes
primary.json (05:56:29, committed 05:57). One small breach: `analysis.py` was modified in e39b994 together with the
outputs it wrote (the by-stratum table); the H2 code itself predates the data. The two paging bugs were caught by
the author before scanning and are logged honestly. The hand check is stratified sensibly and I agree with all 100
calls under the preregistered definitions.

## Reviewer files (`review/reviewer_checks/`)

- `probe_api.py`, `probe_api2.py`, `probe_api.log`, `probes.json`, `probes2.json`, `probes.md`, `cache/`: 79 live
  requests (DataCite query variants, DataCite records, handle API, Local Contexts Hub API for all 20 projects, Harvard
  Dataverse blocks and search, Zenodo search and both serialisations, GBIF, RAiD, re3data, OSF, OpenAIRE re-check).
- `novel_datacite_dois.json`: the 34 DataCite DOIs returned by probe queries but absent from the census, with the
  study's own `detect()` run on each.
- `rescore_views.py`, `rescore_all.csv`, `rescore_disagreements.csv`, `rescore_summary.json`: structural re-scoring of
  all 18,000 record-views with the field path of every element occurrence.
- `handcheck_rescore_sample.csv`, `handcheck_rescore_sheet.txt`, `handcheck_rescore_sheet_compact.txt`,
  `handcheck_rescore.csv`: the 104-item hand re-score.
- `readjudicate_precision.py`, `precision_readjudication.csv`: the 69 name-only hits with the JSON path of each match.
- `recompute.py`, `h1_sensitivity.py`, `recomputed.json`: H1 and H2 with all sensitivity variants above.
