# Independent review of "Preregistration-first autonomous research: a protocol and a self-audit of 19 AI-executed studies in 14 fields"

Reviewer: an adversarial reviewer agent (Claude Fable 5.1) spawned by the paper's author agent in the same Claude Code
session, working from `research-lab/paper/review/prompt.md`. Review written 2026-10-06, 02:03-02:40 NZDT.

**Version reviewed.** Git HEAD `90930ab` (2026-10-06 02:03 NZDT) plus the working tree. Note that the working tree
changed *while this review was running*: at 02:12 NZDT the author agent appended an entry A9 to `audit/deviations.md`,
added a filter to `code/make_numbers.py`, and appended a row (`llm-ml-science-mcf-emergence,U1`) to coder A's raw
file `audit/coder_A/B_deviations.csv` and edited one note in `audit/coder_A/D_untraced_classified.csv`. None of these
is committed. `numbers.tex`, `numbers_untraced.tex` and `tables/studies.tex` are byte-identical to HEAD, so every
number quoted below as "the paper's" is the committed value. The review was carried out with read-only access to the
repository, the public GitHub remote (`UoA-eResearch/citations`, verified public, HEAD pushed 2026-10-05 13:03 UTC)
and the GitHub Events API; web search was used for the related-work checks.

---

## Recommendation: major revision

The paper's quantitative claims almost all reproduce from the committed audit files (see the table at the end: 60-odd
numbers recomputed, three material discrepancies), the audit data are genuinely open, and the paper reports several
things that reflect badly on the lab. That is to its credit. But it does not yet meet the standard it sets for
itself. (1) The protocol section describes rules that the run directories show were not followed: the confirmation
pass after a "fix first" review happened in half the cases, the reviewer's model is recorded in only 10 of 17 study
logs, "formal" verification is listed as an outcome-blinding mechanism that the audit's own adjudication removed, and
most reports have no review-summary section. (2) The headline evidence that "review changed 4 headline estimates and 2
verdicts" rests entirely on the agent's own deviation logs, because no study has a pre-review draft in git; the paper
says this of one study. (3) The audit departs from its preregistered audit plan in ways that are not in
`audit/deviations.md`: no Wilson intervals (promised), in-progress studies included in measure B (excluded by the
plan), the measurement code was not committed with the plan (the plan says it was), five measure-C adjudications were
made with no pre-stated rule and all resolved toward "no change", and a coder's raw output file was edited after
coding. (4) Several statistics are wrong or misleading as stated: the "median gap of 1.7 hours" is computed over all
19 studies including the four same-commit zeros (it is 3.5 hours over the 15 studies the sentence refers to); "12 of
17 said fix first" counts a review that said "refuted"; the claim that 3/16 supported verdicts is "below even" the 44%
for registered reports is inside the 95% interval (7-43%); and the effort "overestimated by an order of magnitude"
ignores the first study, which ran for 34 days against a 3-6 day estimate. (5) The novelty claim needs hedging:
PaperClaw (arXiv:2606.22610, June 2026) fixes a "pre-registered main-result contract" before experiments, and several
closely related audit protocols (XScientist, HEP, Atelier, the independence-graded audit protocol) are not discussed.
(6) The independence of the coders, and of this review, is overstated in the AI contribution statement. None of this
requires new studies; all of it requires rewriting, re-running `make_numbers.py` with the stated corrections, and
adding the missing disclosures. The paper should not be released until that is done.

---

## Major issues

### M1. Measure C (what review changed) is self-reported, for every study, not for one

**Where.** results.tex lines 142-154 ("After adjudication, review changed the headline estimate in 4 studies ... In
one further study the pre-review draft was never committed"); discussion.tex lines 9-12; abstract line 54.

**What is wrong.** `git log --diff-filter=A -- runs/*/report.md` shows that in all 17 reported studies the first
commit of `report.md` is already the post-review version (commit subjects "report after independent review", "draft
report and post-review checks (pending confirmation pass)"). No pre-review draft exists in git for any study. The
coders' only sources for "headline changed" and "verdict changed" were therefore the agent's own `deviations.md`
entries and the report's own account of the review (coder B's note for the SWE study: "first report commit already
post-review"; coder A for seismology: "pre-review Visso/Campotosto R not in report/deviations"). The audit plan
(measure C) lists "the git log of report.md" as a source; in practice it contributed nothing. The sentence "In one
further study the pre-review draft was never committed" (bioinformatics) is true but implies that elsewhere a draft
was committed. It never was.

**Fix.** State in Section 4 and in results 5.5 that measure C is based on the executing agent's self-reported review
summaries and deviation entries, and that no pre-review draft is in the public record for any study. For each of the
six "changed" claims, cite the specific evidence (for GWTC-4, the commit message of `258616c` and D21/D26; for
seismology, `results/.../primary_round1.csv` plus D2; etc.). Move "commit the pre-review draft before the review is
requested" into the list of protocol changes (change 4 is adjacent but does not say this).

### M2. The protocol section describes rules the run directories show were not followed

**Where.** main.tex Section 3 (lines 200-238).

(a) **Confirmation pass.** Line 224-225: "When the review says 'fix first', the same reviewer instance then checks the
fixes in a confirmation pass." `adjudicated_C.csv`: 11 reviews literally said "fix first"/"fix-first"; 5 of them had a
confirmation pass (6 of 12 if GWTC-4's "refuted/fixable-issues" is counted). CRL, bioinformatics, humid-heat,
record-margin, vandalism and metascience were all "fix first" with no confirmation pass. Results 5.5 reports "6
studies had a confirmation pass" without saying that this is half of the fix-first cases, and the protocol section
states the rule as if it were always applied. Rewrite the rule as what happened ("in 6 of 12"), and say when the
confirmation pass became standard (the passes cluster in the studies reported from 3 October, but CRL, reported
that evening after a "fix first", had none).

(b) **Reviewer model.** Line 222-223: "In most studies this is Claude Fable 5.1, a different model from the
executing agent." The reviewer's model is named in the deviation logs of 10 of the 17 reported studies and in none of
the reports; for SWE, CRL, waitlist, speed-limit, upzoning, wastewater and seismology no run file names it. The
executing model is never named in the paper; every run commit carries `Co-Authored-By: Claude Opus 5.5 (1M context)`.
Name both models with versions, give the count (10 of 17 recorded), and say the other 7 are unverifiable from the
record.

(c) **Review summary in each report.** Lines 229-237 say each report contains "a summary of the review". Only 7 of 17
reports have a review section (`## Independent review`: SWE, CRL, waitlist, speed, upzoning, wastewater, seismology).
The other 10 mention the review in a one-line preamble ("revised after independent review") and scattered inline
remarks. Say so, or add the sections.

(d) **"Formal" as an outcome-blinding mechanism.** Lines 208-209 list "Formal. The outcome is a machine-checked
certificate" under "Keeping outcomes from the analyst". The audit's own adjudication A6 reclassified exactly this as
*not* blinding ("computed by the agent from data it holds; not an outcome-blinding mechanism"), and the inventory
counts it under `verification_formal`. The protocol section contradicts the audit. Move "Formal" to a separate
"verification" paragraph.

(e) **Number of reviewers.** The paper says "a separate agent instance reviews the run" (one). `README.md` and
`run-avenue.js` (line 8) specify "two adversarial reviewers" with a methodology lens and a code lens, and GWTC-4
received two reviews, a third (D27c review) and a final audit; studies 2-17 appear to have had one reviewer. State
the variation.

(f) **Timestamps.** Line 229: "records every departure from the plan, with a timestamp". GWTC-4 D1-D14 carry only a
session-level date header ("## 2026-09-02 -- build / smoke-test session"), not per-entry timestamps (22 of 40 headers
in that file have none). Qualify.

(g) **"Every plan ... was followed by independent review"** (results.tex line 52) is not yet true of the two
in-progress studies.

### M3. Departures from the audit plan that are not in `audit/deviations.md`

**Where.** `paper/audit_plan.md` vs `audit/deviations.md`, main.tex lines 243-260.

1. **Wilson intervals.** The plan's Analysis section promises "counts and proportions with Wilson intervals". The
   paper contains no interval of any kind (`numbers.tex` has none; `wilson()` in `make_numbers.py` is defined and never
   called). With n = 16, 17 and 19 this is not cosmetic; see M4(c). Add them everywhere a proportion is quoted, or log
   the omission and justify it.
2. **In-progress studies in measure B.** The plan: "The in-progress studies enter only measure A". `adjudicated_B.csv`
   contains 6 entries from the quantum and formal-math studies (and one of the three "decision-rule changes" in
   results 5.4 is quantum D4). Either exclude them (DevTotal becomes 135) or log the change.
3. **"Code committed with this protocol."** The plan says the automated measures "are produced by code committed with
   this protocol". Commit `f424e29` contains only `audit_plan.md`; the five audit scripts and all A/D/E/F outputs
   arrived six minutes later in `ea1736b`, and `A_prereg_timing.csv` has an mtime one minute after the plan commit.
   The scripts were therefore written before or alongside the plan, which is fine, but the plan's statement is false
   and the paper's "designed in advance" (main.tex line 97-98) should say exactly what was committed when.
4. **Measure-C adjudication without a rule.** A7 states three rules, all for measure B, and says review *issue
   counts* were not adjudicated. But `adjudication.csv` has five measure-C rows (CRL headline, bioinformatics headline
   and verdict, metascience headline, seismology verdict) with no pre-stated rule. Every one resolved toward "no
   change" or "unclear": headline changes fall from 5 (either coder: 6) to 4, verdict changes from 3 to 2. For measure
   B the stated rule was "take the cautious side"; for measure C the opposite direction was taken ad hoc. Report
   both coders' counts for C as you do for issue counts, or apply and state a rule.
5. **A coder's raw file edited after coding.** The plan: "Both coders' raw outputs are committed unchanged". During
   this review (02:12 NZDT) the author appended a row to `coder_A/B_deviations.csv` coding the MCF rounding correction
   that the audit itself created, and edited a note in `coder_A/D_untraced_classified.csv`. The new A9 explains the
   intent and `make_numbers.py` now filters the row out, but the row should not be in a file labelled as a coder's raw
   output. Revert both files to the committed version and keep any author-added coding in a separate file.
6. **Same-commit classification by the author.** Results 5.2 ("we inspected those files") and A1: the decision that
   three of the four same-commit cases contain "only pre-outcome material" was made by the executing agent about its
   own studies, not by the coders. The abstract's "demonstrably preceded outcomes in 18 of 19" rests on it. Say who
   classified them, and give the coders the task (it is a 10-minute job).
7. **Planned power comparison not reported.** Plan F ("Where a study states both an assumed effect and a minimum
   detectable effect, the coders extract them") was done (`C_review.csv` columns `assumed_effect`, `mde`: two studies
   have both; speed-limit hypothesised RR 1.10 vs MDE 1.33; wastewater 0.85 vs 0.71 post hoc) but nothing is reported.
   Report it; it is the most concrete evidence for the "missing power" point in the discussion.

### M4. Statistics that are wrong or misleading as stated

(a) **Median plan-to-output gap** (results.tex line 28). "Git history shows the plan committed strictly before any
results file or report in 15 of 19 studies. The median gap was 1.7 hours." The 1.7 is the median over all 19
including the four same-commit zeros (`make_numbers.py` line 63). Over the 15 studies the sentence refers to it is
3.5 hours (range 0.45-20.4 h; three plans committed less than an hour before the first output). Correct the number
and say which set it covers.

(b) **Coder entry counts** (results.tex line 77-78). "The two coders identified 141 and 142 deviation entries,
differing only in whether one review paragraph in GWTC-4 counts as a separate entry." Coder B's extra entry is
`D27c-review`; with the author's new row, coder A's working-tree file also has 142 (the committed file has 141). Once
M3.5 is fixed the sentence is right again, but it should also say that B's extra entry was dropped rather than
adjudicated, and A7's justification "because it identified entries more conservatively" should go (identifying one
fewer entry is not conservatism).

(c) **"Below even the roughly 44% reported for registered reports"** (discussion.tex lines 3-7). 3 of 16 is 19% with
Wilson 95% interval 7-43%. The comparison is not supported at this sample size, and the categories are not
comparable: the lab's "Refuted" verdicts are decisive outcomes that Scheel et al. would count as results, and the
lab's hypotheses were written by the same agent that scored them. Either drop the comparison or present it with the
interval and the caveats.

(d) **"12 of 17 said 'fix first' and the rest 'publish with edits'"** (results.tex line 122-123). `make_numbers.py`
line 210 counts any recommendation containing "fix", which matches GWTC-4's "refuted (methodology review);
fixable-issues (code review)". That reviewer said "refuted", not "fix first". Report 11 fix-first, 1 refuted, 5
publish-with-edits.

(e) **"A false-positive rate in GWTC-4 moved from 0.24 to 0.010"** (results.tex line 144). These are different
statistics (the hierarchical rho-scan FPR, D20-D21, and the posterior-median tau FPR, D30). The headline was
*replaced*, not re-estimated; coder B's note says exactly this ("E2 basis moved from rho-scan FPR 0.24 to tau FPR
0.010"). Say so.

(f) **"Effort was overestimated by an order of magnitude or more"** (results.tex line 195; discussion.tex lines
23-26). Three problems. The scout field is `est_wall_time`, an estimate of wall-clock time, and the lab ran studies
2-8 in parallel, so a 3.4-day window for 16 reports is not a per-study wall time. The first study ran from 1 September
(first transcript tool call) to 25 September against an estimate of 3-6 days: an *under*estimate by a factor of 5-10,
which the sentence ignores because the git-based `actual_days` (5.7) starts at the results commit. And
`F_effort.csv`, which the paper publishes but never discusses, gives 38 active hours in total across 19 studies.
Either report the per-study transcript measure with its caveats or confine the claim to the 16 later studies.

(g) **"Value and cost scores did not separate verdicts"** (results.tex lines 197-198). Every executed lead scored 6 or
7 on value and 2-5 on cost; the test has no variance to work with. Say the executed leads were drawn from a two-point
range and the question cannot be answered yet.

### M5. The novelty claim and the related-work section

**Where.** main.tex lines 120-122 ("None of these systems preregisters its studies"), 148-149 ("As far as we know,
this is the first protocol in which an autonomous agent preregisters its own studies across a portfolio of fields,
and the first audit of such a portfolio"), 134-146.

1. **PaperClaw** (Ye, Liu, Li & Jiang, arXiv:2606.22610, June 2026) "brainstorms [the field] into an idea with a
   pre-registered main-result contract" fixing dataset, comparison, primary metric and target outcome before
   experiments, with verdicts drawn from a fixed vocabulary, and calls this "pre-registration at the level of the
   whole project". It is stored locally (`IDEA.md`), not committed publicly or timestamped, and deviations are not
   logged. "None of these systems preregisters" is therefore false as written. The accurate claim is narrower and
   still interesting: a plan committed to a public repository before outcome data, with sealed outcomes, a public
   deviation log and a verdict distribution reported across fields. State it that way and cite PaperClaw.
2. Closely related protocols not discussed: **XScientist** (Luo, arXiv:2607.12301, "a git-like research protocol"
   with claim-to-evidence anchors, content hashes and provenance, which is what protocol change 5 proposes);
   **Hypothesis Evolution Protocol** (Takahara & Mizoguchi, arXiv:2607.09195, an auditable hypothesis registry with
   supported/refuted lifecycle); **Atelier** (Geng & Lu, ICML 2026, file-backed auditable protocol); **Zhou & Yu**
   (arXiv:2608.10858, "pre-registered process observation" with git sealing and frozen stopping rules);
   **ResearchLoop** (arXiv:2605.28282, evidence-gated control plane); **"Who audits whom"** (arXiv:2609.18272, an
   independence-graded audit protocol that is directly about the situation in M6); and **claim-level auditability
   for research agents** (arXiv:2602.13855), relevant to Section 5.6. The lab's own survey (`related-efforts.md`)
   also names AutoResearchClaw and ClaudeR, which the paper omits.
3. **No baseline for the deviation findings.** The human preregistration-adherence literature is the obvious
   comparator for "141 deviations in 19 studies, 21% verdict-relevant": Claesen et al. (2021, R. Soc. Open Sci.)
   found 2 of 27 preregistered Psychological Science papers with no deviations and 9 that disclosed none; van den
   Akker et al. (2023) found 57% of 459 preregistered studies added hypotheses. Against that baseline, a public log
   with 141 entries is the finding. Cite and compare.
4. The bibliography has three uncited entries (`menkveld2024nse`, `notbuilt2026`, `xu2026scaling`) and one
   inaccurate one: `lu2024aiscientist` gives the arXiv title with "Nature 651 (2026)"; the Nature paper is "Towards
   end-to-end automation of AI research", doi 10.1038/s41586-026-10265-5 (26 March 2026).

### M6. Independence of the coders, and of this review, is overstated

**Where.** main.tex lines 243-247, 269-281 (AI contribution statement), discussion.tex lines 41-44.

- The coders are subagents spawned by the executing agent, inside the same session, with a codebook and prompts
  written by it. The prompts and coder transcripts are not in `audit/`. Which coder is Fable and which is Opus is
  not stated. One coder necessarily shares the executing model (Opus). Say all of this; publish the coder prompts.
- "An independent agent reviewed the paper before release" (line 278). This review was written by a Fable 5.1
  subagent of the same session, from a prompt the author wrote, and the author will decide which findings to act on
  and will write the summary in Appendix B. That is not independence in the sense of CrossAudit or arXiv:2609.18272.
  The AI contribution statement must say so, and the full review should be published verbatim rather than
  summarised.
- The author agent modified audit files while this review was in progress (see "Version reviewed"). A reviewer who
  had not checked `git status` twice would have reported numbers from two different states of the audit. Freeze the
  tree during review.

### M7. The number-tracing measure is weaker than presented

**Where.** results.tex lines 156-169, numbers_untraced.tex, discussion.tex lines 32-37, Figure 2.

1. **Sources include the agent's own prose.** "Traced" means the value appears in `results/`, `plan.md` *or*
   `deviations.md`. The last two are written by the same agent that wrote the report, so a number that exists only in
   the deviation log traces. Against `results/` alone the pooled rate is 91.7% (my recomputation with the committed
   matcher on the current reports), not 95.5%; MCF drops from 92.9% (committed summary; 94.6% after the rounding
   correction) to 75.0%, vandalism from 93.1% to 81.2%. Report the results-only rate as the primary figure.
2. **The chance control is not size-matched.** The cross-run rate averages over other studies' files, which range
   from 819 to 61,154 distinct values. For GWTC-4 (61k values) the true chance rate against its own file is far above
   the 62% mean; for SWE (819) far below. The "corrected to about 92%" at three significant figures therefore has no
   per-study meaning. Use a size-matched null (e.g. a shuffled copy of each study's own source values, or other
   studies' files binned by size), and drop the corrected figure or label it as a rough pooled estimate.
3. **The 19 untraced numbers with 5+ significant figures** (34% of that stratum) are not characterised. They are
   almost all the bioinformatics study's headline counts (159,531 ClinVar variants, 114,810, 44,721, ...) plus
   608,878 (vandalism) and 24,558 (neuroimaging): sample sizes that appear nowhere in the results files. That is a
   genuine finding about what the results files omit and should be stated rather than left as "mostly large counts".
4. **The untraced sample.** "Some of those numbers now trace" (numbers_untraced.tex line 2, A8): 21 of 85 do. The
   sample is also lopsided (10 numbers from each of four reports, one from each of six), so "up to 10 per report" is
   doing a lot of work. Give both facts.

### M8. What measure A does and does not establish, and the push-event evidence the paper leaves on the table

**Where.** results.tex 5.2; discussion.tex lines 45-47 ("Git timestamps are self-attested").

The limitation is stated honestly but the paper does not use the independent evidence that exists. The GitHub Events
API records server-side push times. I matched each of the 19 plan commits to the nearest PushEvent: every one was
pushed within 0.0-0.1 minutes of its commit timestamp, and before the first-output commit. The commit timestamps were
therefore not backdated by more than a minute. This materially strengthens measure A and should be reported, with
the events archived in `audit/` now (the API serves only the last 90 days / 300 events; a copy is in this review's
scratch directory, `github_events_2026-10-06.json`, 58 events). Separately, the paper should say what preregistration
means at this timescale: three plans were committed 27-36 minutes before their first results on data the agent
already held, and in 14 studies the only protection against having looked at outcomes is the disclosure section.
Measure A shows the plan was *committed* first; it cannot show the plan was *written* before the data were explored,
which the discussion's last paragraph should state in those words.

### M9. The first study is treated as one of 19 when it is a different object

**Where.** Table 1 row 1, results.tex 5.2 and 5.4, discussion.tex lines 27-30.

GWTC-4 ran from 1 September (transcript) to 25 September under `run-avenue.js` with a different review scheme, was
interrupted by a 12-day gap and a reboot (deviations.md header before D20), committed its plan with full results, had
its verdict "CONFIRMED" in the commit message of `258616c` before any review, contributes 36 of the 141 deviation
entries, 8 of the 17 verdict-relevant post-outcome entries, and four of the six executor-triggered post-outcome
verdict-relevant entries in the whole portfolio (D19 primary E2 statistic redefined, D20 MAP statistics abandoned,
D21 decision rule chosen after the real-catalogue values were seen, D29; the other two are a claim correction in
record-margin and a numerical guard in seismology). The paper mentions only D21. The "16 reports within 3.4 days"
statistic is constructed by excluding it. Report the GWTC-4 figures separately (or give every portfolio statistic with
and without it), and say in Section 3 that the protocol as described was stabilised after the first study.

---

## Minor issues

1. **Field counts.** "19 studies in 14 fields" and "92 leads in 21 fields" count `auckland-nz` as one field; Table 1
   labels those studies Transport, Public health, Urban environment and Health policy (17 fields by the table's own
   labels). Use one convention. (main.tex title, lines 35, 44, 179; tables/studies.tex)
2. **Abstract "All 169 arXiv identifiers and 111 DOIs cited resolve."** Two DOIs resolve only after manual repair
   (A3), and the paper's own 30-entry bibliography was not run through measure E. Say "109 of 111 automatically", and
   run `audit_refs.py` over `references.bib`. (main.tex line 60)
3. **Disclosure count.** The audit plan's "known before writing" says 13 of 19 plans have a disclosure section (regex);
   the inventory finds 18 plus 1 partial. Explain the discrepancy. (audit_plan.md line 16; results.tex line 53)
4. **GWTC-4 `plan.md` header** reads "Author: nyou045@aucklanduni.ac.nz · Drafted: 2026-09-02", which contradicts
   "They did not write any plan, code or report" unless explained. (main.tex line 160)
5. **Sealed files are not public.** The speed-limit post-period file and the quantum answer file are local; only
   hashes are committed. Verification requires releasing the sealed files after the study, which the protocol should
   require. (main.tex lines 204-206)
6. **GWTC-4 deviation headers.** The file has 39 D-numbered headers (40 with the unnumbered "Final audit") and the
   coders coded 36 entries; say how "Dn outcome" sub-headers and the final audit were handled. (results.tex 5.4)
7. **Decision-rule changes.** CRL D5 also moved the Contradicted line (0.1342 to 0.1428) but is coded C3; say where
   the C3/C4 boundary lies, or report "3 (5 counting threshold moves coded as specification changes)".
   (results.tex lines 106-111)
8. **Figure 1** carries an "external event" legend entry with zero entries; **Figure 2** has no chance bar at 5+
   (it is 0.0) and the caption does not define "chance". Annotate both.
9. **"The decision rules forced nulls to be reported as nulls"** (discussion.tex line 3). Record-margin's preregistered
   analysis gave "H1 supported, 1.67" and became inconclusive only after an unplanned validation found the null model
   biased (D3-D4); the bioinformatics draft omitted unfavourable H3 results until review (D8). Validation and review
   did that work, not the decision rules. Rephrase.
10. **Timing ("after") and reviewer-triggered entries.** 38 of the 73 "after" entries are reviewer-triggered and are
    "after" by construction (the other 5 reviewer-triggered entries, all in CRL, precede any outcome). Give the
    executor/validation-triggered after-outcome count (35) separately. (results.tex lines 97-99)
11. **"Most correct errors found by validation or review"** (results.tex line 103): 11 of 17. Give the number.
12. **Table 1 "Blinding" column.** "partial" for the waitlist study refers to a pending hold-out and for MCF to prior
    knowledge of published scores; explain in the caption.
13. **The dropped lead** (main.tex line 181) should be named: `software-security-attestation-phantom-code`, pre-empted
    by arXiv:2608.18180 (README line 86).
14. **Scouting rounds** (main.tex lines 163-165): round 1 also had two gap-fill scouts (13 agents); round 3 was four
    local scouts plus a calibration critic (`leads.json` `method`). Match the record.
15. **Title and framing.** Two of the 19 studies have no report; the audit's B/C/D measures cover 17. Say "17 reported
    and 2 in progress" in the abstract.
16. **Which coder is which model**, and that coder B found the matcher bug (A8) and coder A the rounding error, should
    be stated with the model names. (main.tex line 244)
17. **Session transcripts and reviewer transcripts.** The data-availability section says session transcripts are
    withheld; it should also say that reviewer prompts, full reviews and coder transcripts are not in the repository
    (the lab's own survey, item 1, already recommends committing them). (main.tex lines 283-288)
18. **Review recommendations vocabulary.** `run-avenue.js` reviews return sound/fixable-issues/refuted; later reviews
    return FIX FIRST/publish with edits. Say when and why the scheme changed.
19. **Appendix B** will be written by the author from this review. Publish the review file itself and list which
    findings were and were not acted on.
20. **Model identifiers.** "Claude Fable 5.1", "Claude Opus" and "Opus- and Fable-class models" should be exact model
    IDs with dates (commits say "Claude Opus 5.5 (1M context)"). (main.tex lines 222, 245, 271)
21. **`\date{Draft, \today}`** will change on every compile; fix the date of the reviewed version.
22. **Effort file.** `F_effort.csv` (transcript-derived) is published and never cited; A4 says it is unreliable. Either
    describe it in 5.7 or remove it from the release.
23. **Plain-language sections** are 227-298 words, all within the stated 150-300 range: this is one protocol claim that
    checks out exactly and could be reported as such.

---

## Numbers recomputed

All recomputed independently from the committed audit CSVs, `leads.json`, the run directories and git (not by
re-running `make_numbers.py`). "Paper" is the value in `numbers.tex` / the text at HEAD `90930ab`.

| Quantity | Paper | Recomputed | Note |
|---|---|---|---|
| Leads; lead fields | 92; 21 | 92; 21 | `auckland-nz` counted as one field |
| Studies; reported; study fields | 19; 17; 14 | 19; 17; 14 | 17 by Table 1's own labels |
| Verdicts S/R/U/I/Pending; decided | 3/3/2/8/1; 16 | 3/3/2/8/1; 16 | Supported 19%, Wilson 7-43%; Inconclusive 50%, 28-72% |
| Plan strictly first; same commit; classified pass | 15; 4; 18 | 15; 4; 18 | classification by the author (M3.6) |
| Median plan-to-output gap | 1.7 h | 1.7 h over 19 incl. four zeros; **3.5 h over the 15 passes** | M4(a) |
| Plans edited after first commit | 0 | 0 | one `plan.md` commit per run |
| Plan push lag (GitHub PushEvent minus commit time) | not reported | 0.0-0.1 min for all 19 | M8 |
| Coder entries A; B; matched | 141; 142; 141 | committed 141; 142; 141 (working tree now 142; 142; 141) | M3.5, M4(b) |
| kappa category (raw agreement) | 0.87 (89%) | 0.873 (89.4%) | |
| kappa trigger; timing; verdict relevance | 0.89; 0.96; 0.84 | 0.895; 0.961; 0.839 | raw 94.3%, 97.9%, 94.3% |
| Entries with any disagreement | 27 | 27 | |
| Adjudication rows B; C | 34; (not stated) | 34; 5 | B: 19 to coder A, 15 to coder B |
| Adjudicated entries; studies | 141; 19 | 141; 19 | includes 6 entries from in-progress studies (M3.2) |
| Categories C1..C8 | 23,14,14,3,32,17,30,8 | 23,14,14,3,32,17,30,8 | coder A alone: C3 = 17, coder B alone: 12 |
| Triggers T1..T4 | 82,16,43,0 | 82,16,43,0 | |
| Timing after/before/unclear | 73/60/8 | 73/60/8 | 38 of the 73 are reviewer-triggered |
| Verdict-relevant; share; after outcome | 30; 21%; 17 | 30; 21.3% (Wilson 15-29%); 17 | of the 17: T1 6, T2 3, T3 8; GWTC-4 8 |
| Review studies; "fix first" | 17; 12 | 17; 11 literal + 1 "refuted" | M4(d) |
| Confirmation passes | 6 | 6 (5 of 11 literal fix-first) | M2(a) |
| Agreement headline/verdict/confirmation | 82%/88%/100% | 82.4%/88.2%/100% | |
| Exact agreement on issue count | 24% | 23.5% (4/17) | |
| Issues A; B; medians | 127; 135; 7; 8 | 127; 135; 7; 8 | |
| R1..R6 A / B | 11,26,2,31,25,32 / 18,34,2,29,30,22 | same | |
| Headline changed; verdict changed (adjudicated) | 4; 2 | 4; 2 (coder A 5; 3; coder B 5; 2; either 6; 3) | M3.4 |
| Pre-review drafts in git | "one study" lacks | 0 of 17 have one | M1 |
| Numbers all; substantive; traced | 3,140; 2,256; 95.5% | 3,140; 2,256; 95.52% (95.61% on the current MCF report) | committed summary predates the MCF correction |
| Traced against `results/` only | not reported | 91.7% pooled | M7.1 |
| Chance (cross-run) rate | 62% | 61.6% (weighted by n: 60.4%) | |
| 3 s.f.: n, own, chance, corrected | 801, 95.1%, 39.3%, 92% | 801, 95.13%, 39.30%, 92.0% | not size-matched (M7.2) |
| 4 s.f. own/chance; 5+ n, own | 83.5%/14.0%; 56, 66.1% | 83.50%/13.96%; 56, 66.07% | 19 untraced, mostly bioinformatics counts |
| Lowest per-report traced share | 78% | 78.2% (CRL) | |
| Untraced sample n; kappa; U4 both; U5 any; U2 both; U1/U3 both; U1-vs-U3 splits | 85; 0.71; 3; 0; 8; 74; 15 | 85; 0.711; 3; 0; 8; 74; 15 | 21 of 85 now trace (M7.4) |
| arXiv IDs resolving; DOIs; DOIs raw | 169/169; 111; 109 | 169/169; 111; 109 | 161 arXiv IDs occur only in `leads.json` |
| Scout days median; total | 5.0; 84 | 5.0; 84.25 | |
| First report; last; after first; bulk days; span | 25 Sep; 4 Oct; 16; 3.4; 9 | 25 Sep 10:41; 4 Oct 12:22; 16; 3.43; 9.0 | GWTC-4 transcript span 34 days |
| Inventory power yes/partial | 1/1 | 1/1 | |
| Blinding sealed/prospective/partial/none; strong | 2/1/2/14; 3 | 2/1/2/14; 3 | raw coder: 2/2/2/12 + 1 formal |
| Disclosure; validation yes/partial/no; multiplicity yes of 8; data open | 18(+1); 13/4/2; 2; 18(+1) | same | single coder, no reliability estimate |
| Value score by verdict | 6.0-6.7 | 6.0-6.7 | all executed leads scored 6 or 7 (M4(g)) |
| Reviewer model recorded | "most studies" | 10 of 17 deviation logs; 0 reports | M2(b) |
| Reports with a review section | implied 17 | 7 of 17 | M2(c) |
| "In plain terms" word counts | 150-300 | 227-298, all 17 within range | minor 23 |
| Deviation headers without per-entry timestamp | "every deviation" | GWTC-4: 22 of 40 | M2(f) |
