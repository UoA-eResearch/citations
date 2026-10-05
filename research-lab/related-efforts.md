# Who else is doing autonomous AI research, and what can we learn?

A survey of comparable efforts, as of 5 October 2026, written for the research lab in this directory. Sources are
listed at the end. Numbers quoted from papers are as reported by their authors and were not re-checked by us.

## In plain terms

Several groups now build "AI scientists": systems that pick a question, analyse data, and write up a result with
little human help.

- **The best known are company products**, mainly in biology, machine learning or materials. Edison Scientific's Kosmos
  and Google's co-scientist are examples.
- **A few open projects cover many fields at once, as we do.** Denario and Agon are the closest.
- **There is also a fast-growing literature on how these systems go wrong.** They overclaim. They report weak null
  results as if they were findings. They pick the analysis that happens to look best. Their AI reviewers can be fooled.
  And different AI agents given the same data reach different conclusions.

**Where we stand.** No other system we found combines the lab's key safeguards:

- a public plan committed before results are seen;
- answers sealed away from the analysis;
- an independent reviewer who re-runs the numbers;
- a public log of every departure from the plan;
- publishing null and negative results as readily as positive ones.

**Where we can improve.** The field's lessons point to six changes:

- publish full working logs and reviews, not just results;
- require a power calculation in every plan, since half our verdicts are "inconclusive";
- automatically check every number in a report against the results files;
- have a second, blind analyst agent re-derive each headline result;
- track how well our lead scores predicted what actually happened;
- state plainly in each report which decisions a human made.

## 1. The closest comparable efforts

| Effort | Who | Domains | What it does | Validation reported |
|---|---|---|---|---|
| **Kosmos** | Edison Scientific (FutureHouse spin-out), Nov 2025 | Metabolomics, materials, neuroscience, statistical genetics, more | 12-hour runs of up to about 200 agent rollouts sharing a "structured world model"; about 42,000 lines of code and 1,500 papers read per run; every statement cites code or literature | Independent scientists judged 79.4% of statements accurate: 85.5% of data-analysis statements, 82.1% of literature statements, but only **57.9% of synthesis/interpretation statements**. Seven discoveries, three of which reproduced unpublished human findings |
| **Denario** | AstroPilot-AI collaboration, Oct 2025 (open code) | 10+ fields: astrophysics, biology, chemistry, materials, medicine, neuroscience, planetary science, etc. | Modular multi-agent pipeline from idea to literature check, plan, code, plots and paper | Domain experts scored the generated papers |
| **Agon** | Sun, Ren, ... Yang, Jun 2026 | "Omnidisciplinary", 10+ domains | 444 "Prompt Economy" loops and 1,000+ scientist-coder-auditor iterations; no human-written experiment code; topics come from humans or an optional "topic radar" | A failure taxonomy rather than a success rate (section 3) |
| **data-to-paper** | Kishony lab (Technion), NEJM AI | Biomedical, public data | Open data to a paper in which every number is programmatically traced back to code output ("data-chaining") | Recapitulated peer-reviewed findings without major errors in 80-90% of simple cases; needed human co-piloting as goals got harder |
| **AutoDiscovery** (formerly AutoDS) and **CodeScientist** | Allen Institute for AI (Asta) | Any tabular dataset; agents and virtual environments | Open-ended search driven by "Bayesian surprise" (Monte Carlo tree search); CodeScientist runs code-based experiments | CodeScientist: 19 candidate discoveries, 6 judged sound and novel by human experts |
| **The AI Scientist v1/v2** | Sakana AI, with UBC, Vector and Oxford; Nature, March 2026 | Machine learning only | Idea, experiments, paper, automated review | 1 of 3 fully AI-written papers passed workshop review at ICLR 2025 (score 6.33); it was voluntarily withdrawn |
| **ScientistTwo** | Google Cloud AI Research, Sep 2026 | Machine learning subfields | Starts from an accepted paper and tries to beat its method | Beat the original in 86 of 107 papers, but was **judged by AI review agents** |
| **AI co-scientist**; **Robin** | Google; FutureHouse | Biomedicine | Hypothesis tournaments; a lab-in-the-loop drug-repurposing cycle | Wet-lab validation, including liver-fibrosis organoids and an AML drug repurposing (co-scientist), and ripasudil for dry AMD (Robin) |

**Open tooling** follows the same pattern:

- Claude Code/Codex "research skill" packs, such as Orchestra's AI-Research-SKILLs, open-scholar-skill and Claude
  Scholar;
- AutoResearchClaw, which adds citation verification;
- ClaudeR, which audits analyses against a preregistration;
- Clarus, which coordinates many research agents with attributable, auditable records.

**What none of them have.** None of the systems above writes a preregistration before seeing outcomes. None seals the
answer away from the analysing agent. None ranks a portfolio of leads across 20+ domains by value and cost, as our
`leads.json` and Golden Quadrant explorer do. Most start from a human-chosen topic, and Agon says so explicitly as a
design choice. Kosmos also lists as limitations that it cannot fetch public data itself, works only on datasets up to
about 5 GB, and does not converge across repeated runs.

## 2. Venues and infrastructure for AI-led research

**Agents4Science 2025** (Stanford, organised by James Zou) was the first conference with AI agents as first authors and
reviewers.

- 253 complete submissions; 79 were also read by a human expert; 48 were accepted.
- About 56% of submissions had at least one reference flagged as possibly hallucinated by an automated checker.
- Two papers contained prompt injections aimed at the AI reviewers.
- The three LLM reviewers differed greatly in leniency: Gemini 2.5 Pro averaged 4.23, Claude Sonnet 4 3.0 and GPT-5
  2.30. Gemini's mean absolute gap from human scores was 2.73, against 0.91 for GPT-5.
- Accepted papers had **more** human guidance than rejected ones. Authors reported overclaiming and hallucinated
  references.

**Other venues and infrastructure:**

- **aiXiv:** a preprint server for AI-written papers with AI review. It is small: a few dozen papers.
- **AI Agent Journal:** treats negative results and replications as first-class submissions.
- **Reproducing ICML 2026:** humans and agents post reproduction attempts to a shared logbook.
- **Replication at scale:** the Institute for Replication / IFP "Replication Engine". Xu & Yang's AI-assisted workflow
  checked 384 political-science papers and found 94.4% fully reproducible when replication packages were available.

## 3. Evidence about how AI research goes wrong (the most useful part for us)

1. **Hidden pitfalls**, Sep 2025. Tests of Agent Laboratory and The AI Scientist v2 on a synthetic task found:
   - inappropriate benchmark choice (Agent Laboratory picked the first-listed benchmark in 82.4% of runs);
   - data leakage;
   - metric misuse;
   - post-hoc selection of the best run.

   An auditor spotted these problems with 55% accuracy from the paper alone and 82% with the paper plus logs and code.
   The authors' recommendation is to publish the full traces.
2. **Shadow evaluations**, Kirgis, Narayanan, Bommasani et al., Jul 2026. Frontier agents got six days and thousands of
   dollars to answer the questions of two unpublished NeurIPS papers. They did all the engineering, but the original
   authors rejected the results. The five failure modes were:
   - poor judgment of the bar for a publishable result;
   - uncreative responses to a flawed design;
   - poor backtracking from dead ends;
   - poor resource awareness;
   - instruction drift.

   The agents "presented underpowered negative results as substantive findings".
3. **Ideation-execution gap**, Si, Hashimoto & Yang, 2025. LLM ideas that experts rated more novel than human ideas lost
   that edge once 43 experts spent 100+ hours each executing them. On several measures the ranking flipped.
4. **Many AI analysts.** Agents given the same data and question disagree, and the disagreement has a direction.
   - Bertran, Fogliato & Wu (2026): autonomous AI analysts produced widely dispersed effect sizes and often reversed
     whether a hypothesis was "supported".
   - Gao & Xiao (2026): 150 **Claude Code** agents testing six market-quality hypotheses showed large "nonstandard
     errors". Model families had stable "styles" (Sonnet 4.6 vs Opus 4.6). AI peer review barely reduced the spread.
     Showing the agents top-rated exemplars cut it by 80-99%, but "convergence reflects imitation rather than
     understanding".
   - "The Agentic Garden of Forking Paths" (2026): priming agents with a belief, without any instruction to hack, was
     enough to give belief-aligned conclusions. Agents reproduced 72% of the ideological gap seen among 42 human teams
     analysing the same immigration data.
5. **AI reviewers can be fooled.** In BadScientist (ACL 2026), fabricated papers were accepted by multi-model LLM review
   up to 82% of the time. Reviewers often flagged integrity concerns and then gave accepting scores anyway (the
   "concern-acceptance conflict"). Defences barely beat chance.
6. **The verification-gap survey**, Aug 2026.
   - 83% of AI-scientist systems release code, but only 38% release the seeds or traces needed to re-run them, and only
     38% verify novelty.
   - No LLM-era system shows an externally validated in-loop check of its results.
   - It ranks verification from formal proof (Lean) and executable or physical tests at the top down to "model
     opinion" at the bottom, and proposes a reporting checklist: artifacts, selection disclosure, cost accounting and
     prompt logging.
7. **Agon's failure taxonomy.** Its failures fall into four classes:
   - **perception:** "anomaly blindness", and plausible but false explanations;
   - **reasoning:** treating smoke tests as finished results, and "obedient refinement", meaning accepting every reviewer
     criticism without checking it;
   - **execution:** missing controls, and CPU misallocation;
   - **motivation:** premature abandonment, and "disguising abandonment as readiness for writing".
8. **Preregistration for AI work.**
   - Vaccaro (2026) catalogues 25+ researcher degrees of freedom specific to LLM experiments and shows that one
     phenomenon flips sign across 2,430 specifications. Her remedy is to lock model IDs, verbatim prompts, seeds and
     pilot history in advance.
   - Thomas, Gligoric & Shah (2026) propose preregistering against **the next LLM to be released**, which cannot be
     tuned against. This would have blocked about 73% of p-hacks from transferring.
9. **The open-data paper-mill warning.** Suchak et al. (PLOS Biology 2025) found NHANES single-factor association papers
   rising from about 4 a year to about 190 in 2024. They were formulaic, used unexplained data subsets and had no
   false-discovery control. This is the failure mode an open-data AI lab must avoid.
10. **Critiques of autonomy.**
    - "Agentic AI Scientists Are Not Built For Autonomous Scientific Discovery" (May 2026) warns of problem selection
      driven by what is measurable (the McNamara fallacy), consensus-seeking from preference training, and benchmarks
      with no feedback from real experiments.
    - "The Calibration Turn" (2026) argues that every claim must be licensed by its evidence.

## 4. What we already do that the field asks for

| Field recommendation | Lab practice |
|---|---|
| Preregister, and disclose pilots | `plan.md` is committed before outcomes in every dive. 13 of the 19 plans have an explicit "what has been seen" disclosure; five of the six without one are among the first eight dives |
| An external check, not model opinion | Sealed answers and prospective tests: the Helios peak strings, City Rail Link 2027, forecasts scored on future releases; Lean kernel certificates (formal-math lead). These sit at the top of the survey's verification ladder |
| Report negative results | Of 16 decided verdicts: 3 Supported, 3 Refuted, 2 Unsupported, 8 Inconclusive |
| Independent review that re-runs the work | A reviewer agent of a different model before every verdict. For example, it re-derived the ETAS likelihood, and found the Norcia local optimum that moved R from 0.51 to 0.88 |
| Log deviations | `deviations.md` with `date` timestamps in every run |
| Avoid hallucinated references | **Checked today:** all 161 arXiv IDs cited in `leads.json` resolve. The flagged title mismatches we examined were correct citations (author-year style, or a renamed paper). DOIs were not checked |

## 5. What we can learn: recommended changes, most valuable first

1. **Publish traces, not just results.** The pitfalls paper and the survey's checklist both call for this. Today
   `runs/*/logs/` is git-ignored, and the reviewer's prompt and full review are not saved in the run directory; only
   our summary of the review is.
   - Commit a `review/` folder holding the prompt, the full review and the confirmation pass.
   - Commit an **analysis ledger**: every script run on outcome data, with timestamp, command and output hash. This
     makes post-hoc selection auditable.
2. **Require a power calculation (minimum detectable effect, MDE) in every plan.** Half our decided verdicts (8 of 16)
   are Inconclusive. In the speed-limit dive the scout's assumed effect was well below what the data could detect, and
   Kirgis et al. show agents passing off underpowered nulls as findings.
   - Every `plan.md` must state the MDE at the preregistered sample.
   - Scouts should estimate it before a lead is ranked.
   - "Refuted" should require an equivalence-type bound, as the formal-math plan already does.
3. **Check every number in a report against the results.** Kosmos's interpretive statements were the least accurate
   (57.9%), and data-to-paper traces every number to code. A small `check_report_numbers.py` would extract every number
   from `report.md` and require it to appear, within rounding, in a results file or an explicit allowlist, before
   review. This automates an existing memory lesson ("verify every descriptive sentence").
4. **Harden the reviewer.** AI critique rarely changes conclusions (Gao & Xiao), and AI reviewers accept despite their
   own concerns (BadScientist).
   - The reviewer must (a) recompute the primary statistic from raw outputs, and (b) list every concern with its effect
     on the verdict.
   - For **Supported** verdicts, the most costly kind to get wrong, add a second independent reviewer.
   - Our reviewer is already a different model from the executor, which avoids self-preference.
5. **Run a one-agent "many analysts" check.** For each primary claim, an analyst agent that sees only the plan, the data
   and a neutrally worded question re-derives the headline statistic blind to our result, and we report the agreement.
   It costs one agent per lead. It measures the agent-to-agent spread that the nonstandard-errors and forking-paths
   studies show is large, and it counters belief-priming.
6. **Calibrate lead scoring against outcomes.** The ideation-execution gap shows LLM-scored ideas fade once executed.
   - Record for each completed lead: actual wall time against `est_wall_time`; whether the data matched the
     description; whether the assumed power held; and the verdict.
   - Review the value/cost scoring after 20 dives.
7. **Add an autonomy statement to each report**, in the style of the Agents4Science checklist. It should list which
   decisions were the lab owner's (for example "proceed without Māori/Pacific input" in the waitlist dive) and which
   were the AI's.
8. **Account for costs per lead**, as the survey's checklist asks: GPU-hours, CPU-hours, wall time and approximate
   tokens.
9. **Write down the open-data guard.** Do not admit leads that are single-predictor association hunts on survey data
   without an identification strategy and a multiplicity correction (the NHANES warning). Current leads already
   comply.
10. **Consider "preregister for the next model" designs** for AI-evaluation leads. Prospective tests are already the
    lab's strongest design.
11. **External outlets, for the lab owner to decide.** Agents4Science (if it runs again), AI Agent Journal (negative
    results welcome), the ICML reproduction logbook, and the Institute for Replication could all host our work. None
    has been contacted, and no accounts have been created.

**Our own experience matches several reported failure modes:**

- **Resource misallocation (Agon, Kirgis).** GPU jobs drifted onto the Lean worker cores on 5 Oct 2026, and GPU
  utilisation fell to 20% until they were pinned.
- **Long idle waits.** Self-matching `pgrep` waits once cost 14 h.
- **A local optimum nearly published.** Before review, the Norcia fit was a local optimum.

The safeguards that caught these are review and logging. That supports investing further in items 1, 3 and 4.

## Sources

- Kosmos: [arXiv 2511.02824](https://arxiv.org/abs/2511.02824); [Edison Scientific announcement](https://edisonscientific.com/articles/announcing-kosmos); [radiation-biology evaluation, arXiv 2511.13825](https://arxiv.org/pdf/2511.13825)
- Denario: [arXiv 2510.26887](https://arxiv.org/abs/2510.26887); [code](https://github.com/AstroPilot-AI/Denario)
- Agon: [arXiv 2606.24177](https://arxiv.org/abs/2606.24177)
- data-to-paper: [arXiv 2404.17605](https://arxiv.org/abs/2404.17605); [code](https://github.com/Technion-Kishony-lab/data-to-paper)
- Ai2: [AutoDS](https://allenai.org/blog/autods); [CodeScientist](https://allenai.org/blog/codescientist); [AutoDiscovery launch](https://siliconangle.com/2026/02/12/ai2-introduces-autodiscovery-automated-scientific-discovery-ai-system/)
- Sakana: [AI Scientist v2 paper](https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf); [Nature 2026 coverage](https://noqta.tn/en/news/sakana-ai-scientist-nature-automated-research-2026)
- ScientistTwo: [arXiv 2609.19644](https://arxiv.org/abs/2609.19644)
- Landscape overviews: [Turing Post, 12 AI co-scientists of 2026](https://www.turingpost.com/p/ai-co-scientists-in-2026); [Chalmers AI scientist](https://www.chalmers.se/en/current/news/ai-scientist-autonomously-generates-and-validates-new-biological-discoveries/)
- Clarus: [arXiv 2606.30246](https://arxiv.org/abs/2606.30246); AutoResearchClaw: [GitHub](https://github.com/aiming-lab/AutoResearchClaw); ClaudeR: [GitHub](https://github.com/imnmv/clauder); open-scholar-skill: [GitHub](https://github.com/joshzyj/open-scholar-skill)
- Agents4Science: [arXiv 2511.15534](https://arxiv.org/abs/2511.15534); [Science News](https://www.sciencenews.org/article/science-conference-test-ai-agents)
- aiXiv: [arXiv 2508.15126](https://arxiv.org/html/2508.15126v2); AI Agent Journal: [site](https://www.aiagentjournal.org/)
- Reproduction at scale: [Xu & Yang, arXiv 2602.16733](https://arxiv.org/abs/2602.16733); [IFP Replication Engine](https://ifp.org/the-replication-engine/); [ICML 2026 reproduction challenge](https://howaiworks.ai/blog/icml-2026-agent-reproduction-challenge); [Replica/Faraday, arXiv 2608.13331](https://arxiv.org/html/2608.13331)
- Hidden pitfalls: [arXiv 2509.08713](https://arxiv.org/abs/2509.08713)
- Shadow evaluations: [Kirgis et al., arXiv 2607.27191](https://arxiv.org/abs/2607.27191)
- Ideation-execution gap: [Si, Hashimoto & Yang, arXiv 2506.20803](https://arxiv.org/abs/2506.20803)
- Many analysts: [Bertran, Fogliato & Wu, arXiv 2602.18710](https://arxiv.org/abs/2602.18710); [Gao & Xiao, Nonstandard Errors in AI Agents, arXiv 2603.16744](https://arxiv.org/abs/2603.16744); [The Agentic Garden of Forking Paths, arXiv 2607.01507](https://arxiv.org/abs/2607.01507)
- BadScientist: [arXiv 2510.18003](https://arxiv.org/abs/2510.18003)
- Verification-gap survey: [arXiv 2608.05179](https://arxiv.org/html/2608.05179v1)
- Preregistration: [Vaccaro, arXiv 2606.11217](https://arxiv.org/abs/2606.11217); [Thomas, Gligoric & Shah, arXiv 2606.27687](https://arxiv.org/abs/2606.27687)
- NHANES paper mills: [Suchak et al., PLOS Biology 2025](https://ideas.repec.org/a/plo/pbio00/3003152.html)
- Critiques: [arXiv 2605.08956](https://arxiv.org/abs/2605.08956); [The Calibration Turn, arXiv 2606.31273](https://arxiv.org/abs/2606.31273)
