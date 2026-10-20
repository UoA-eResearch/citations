# Preregistration: a systematic screen of US judicial opinions for citations to cases that do not exist

Lead: `legal-digital-humanities-phantom-citations-judicial-opinions` (Legal & Digital Humanities). Written
2026-10-21, before any opinion text had been extracted or any citation resolved.

**Examined beforehand:** the CourtListener bulk-data bucket listing (snapshot 2026-09-30: opinions 55.3 GB,
dockets 5.1 GB, opinion-clusters 2.5 GB, citations 0.13 GB, all bz2, no per-court or per-year splits since 2023);
eyecite's output on a two-sentence test string, which yields volume, reporter, page, pin cite, year, court and
the plaintiff and defendant names; and the Charlotin AI Hallucination Cases database (2,203 rows on 2026-10-21;
`Party(ies)` is `Pro Se Litigant` in 1,265, `Lawyer` in 866 and `Judge` in 26, with 32 rows naming a judge or
court, of which roughly nine are United States matters). No opinion text had been read.

**Novelty** (searches 2026-10-21). Tools exist to check citations against CourtListener — CiteProof, the
CourtListener citation-lookup API, eyecite itself — and they are aimed at screening AI-drafted *filings*.
Benchmarks (Dahl et al. 2024; Magesh et al. 2025) measure how often models hallucinate citations. The Charlotin
database and the CITP "Who Checks the Citations?" work are incident-driven: they count what somebody noticed and
published. No systematic screen of judicial opinions themselves for nonexistent authorities was found, and no
estimate of how many go undetected.

## 1. What is being measured, and what is not

The screen detects **phantom citations**: full case citations, in the text of a judicial opinion, for which no
corresponding case can be found either by its reporter-volume-page or by its case name anywhere in the corpus.

**It does not detect AI use, and the study will not claim to.** A phantom citation can come from a hallucinating
model, but also from a transcription error, a mangled parallel citation, a citation to an unpublished or sealed
disposition, or a reporter the corpus does not carry. The design's job is to drive those alternatives down far
enough that what remains is a defensible count of citations to apparently nonexistent authority; attributing any
of them to a person or a tool is outside what this evidence can support.

**Definitions.**
- **Population.** Every opinion in the 2026-09-30 CourtListener snapshot whose cluster `date_filed` falls in
  2019-01-01 to 2026-09-30, in a United States court.
- **Screened period** 2023-01-01 to 2026-09-30; **placebo period** 2019-01-01 to 2022-12-31, before general
  availability of the chat models implicated in the known incidents.
- **Complete reporter-volume.** A reporter-volume pair is *complete* if at least 98% of the page numbers that
  appear across its known cases are present in the corpus. Only citations into complete reporter-volumes can
  produce a phantom finding, so that a miss means "no such case" rather than "the corpus lacks it".
- **Reliance** versus **flag.** An opinion *relies* on a citation when it is offered as authority. An opinion
  *flags* one when the court is discussing somebody else's bad citation — a sanctions order, an order to show
  cause. Only reliance counts; flagging is the known, already-reported phenomenon and will be reported
  separately.

## 2. Hypotheses

- **H1 (undetected phantom citations are several times the publicised count).** The verified screen finds at
  least **20** distinct US judicial opinions filed 2023-01-01 to 2026-09-30 that rely on at least one phantom
  citation — at least twice the roughly nine US judge-attributed incidents in the public database.
  - **Supported** if at least 20 verified opinions; **Refuted** if fewer than 10; **Inconclusive** between 10
    and 19.
- **H2 (the placebo period is near-empty).** The same screen over 2019-2022 yields **2 or fewer** verified
  reliance-type opinions per equivalent volume of opinions screened.
  - **Supported** if the rate in 2019-2022 is at most a quarter of the 2023-2026 rate; **Refuted** if it is more
    than half; **Inconclusive** between.

Both counts are *verified* counts: every reliance-type candidate in the screened period, and every candidate in
the placebo period, is checked by hand against the corpus and against external lookup before it is counted.
Counts are reported with Wilson intervals on the per-10,000-opinion rate, and separately as recall-corrected
estimates using the calibration in §4.

## 3. Data

All from the CourtListener 2026-09-30 bulk snapshot (Free Law Project, CC0 / public records) plus one external
list:

- **opinions** (55.3 GB bz2): opinion text.
- **opinion-clusters** (2.5 GB bz2): case name, `date_filed`, docket id — the date and name authority.
- **dockets** (5.1 GB bz2): court id, for court level and jurisdiction.
- **citations** (0.13 GB bz2): the reporter-volume-page to cluster map used for resolution and for the
  completeness filter.
- **Charlotin AI Hallucination Cases** (2.1 MB): the publicised incidents, used only for recall calibration and
  for the capture-recapture estimate.

## 4. Method

1. **Extract** full case citations from each in-scope opinion with eyecite, keeping volume, reporter, page, pin
   cite, year and party names.
2. **Resolve** each against the citations map, with first-page and page-range logic.
3. **Filter** to citations landing in complete reporter-volumes (§1).
4. **Name lookup.** For every unresolved citation, search all cluster case names for the cited parties
   (normalised, rapidfuzz). Sort the result into *typo* (resolves under a small edit of volume or page),
   *misattribution* (the citation resolves but to a case with a different name), and *phantom candidate*
   (neither the citation nor the name exists anywhere).
5. **Context.** Classify each phantom candidate as reliance or flag from the surrounding text.
6. **Calibrate recall** on the Charlotin incidents whose opinions are in the corpus: what share does the screen
   recover? Report it, and use it to correct the counts.
7. **Verify by hand** every reliance-type candidate in the screened period and every candidate in the placebo
   period.
8. **Estimate** rates per 10,000 opinions by court level and year, and a two-source capture-recapture estimate of
   total US incidents from the screen and the public database.

## 5. Threats and care

1. **Corpus coverage is the main threat.** CourtListener's state-court coverage is uneven, and a citation can
   fail to resolve because the cited case is simply absent. The completeness filter exists for this, and its
   threshold is preregistered rather than tuned to the answer; the share of citations it discards will be
   reported.
2. **OCR and formatting noise** will produce false candidates. These are what the typo class and the manual
   verification step are for. If the candidate set is too large to verify exhaustively, a random sample of fixed
   size will be drawn and the counts reported as sample-based estimates, with the sampling rule fixed before the
   sample is seen.
3. **Flag-type contamination** would inflate the count with exactly the cases that are already known. The
   reliance/flag split is therefore applied before counting, and both numbers are reported.
4. **This is not an AI-detection study** (§1), and the report will not attribute any individual opinion to any
   tool or person.
5. **Reporting.** Findings are reported as counts, rates and, where a specific opinion is described, by its
   public citation only. No judge is named, and no opinion is characterised as misconduct; the factual claim is
   that a cited authority could not be found, which any reader can check.
6. **One-off bulk download.** The snapshot is pulled once, in parallel byte ranges, and cached; it is not
   re-fetched.
