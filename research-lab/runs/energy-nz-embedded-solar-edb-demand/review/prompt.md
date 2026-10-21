You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/energy-nz-embedded-solar-edb-demand/ (read-only except your output in
review/).

**The question.** How much grid energy has New Zealand's distributed solar displaced, and has it touched the winter
peak? 29 distributors; outcomes per ICP on solar kW per ICP, ICP-weighted, distributor and year fixed effects,
distributor-cluster pairs bootstrap.

- **H1–H3 (annual disclosures, Schedule 9e, disclosure years 2015–2025)**, all reported Inconclusive with minimum
  detectable slopes of 8, 18 and 2.8 against expected effects of about 1.2, 0.5 and 0.
- **H4 (half-hourly grid-exit offtake, 12:00–15:00, December–February, 12 summers, 24 merged units)**: −0.84 MW per
  MW (−1.01 to −0.16), reported Supported. A post hoc evening/night placebo (D3) is not clean (−0.49, −0.33); an
  exploratory midday-minus-evening contrast (D4) gives −0.35 (−0.44 to −0.26), which the report calls the best
  estimate.

**What to read:** plan.md, deviations.md (D1–D4), report.md and report.html; code/ (fetch.py, weather.py,
build_panel.py, analysis.py, figures.py); results/tables/; data/raw/ (a symlink to /mnt/data/edb-solar/raw, with
manifest.json).

**Git.** Read-only git is fine. Check that plan.md (fd5d815) preceded any outcome series and that code preceded its
outputs; note what D2–D4 changed after which results.

**Environment.** Python: /mnt/citations/research-lab/runs/energy-outage-major-event-day-ratchet/venv/bin/python
(pandas, numpy, pyarrow). Run it with -I. Do NOT pip install. Scripts and outputs under review/reviewer_checks/. You
may re-fetch public EMI or Commerce Commission files politely.

Check at least:

1. **Accounting and measures.** Is net grid supply = "electricity entering system" minus "electricity supplied from
   DG" right for these schedules? Is the self-consumption logic behind H2 right, and was moving the lead's 1.0
   GWh/MW from delivered energy to grid supply legitimate preregistration rather than goal-post moving?
2. **Exposure.** Are the participant-to-distributor map (build_panel.PARTICIPANT), the exclusion of embedded
   networks, and the segment definitions (residential + commercial behind the meter; SME overlaps) right? Does the
   industrial segment really hold the solar farms?
3. **D1 and D2.** Is the Grid_export/Grid_import direction now right (check a known load-only point such as
   HAM0331, and a known embedded generator)? Is switching to registry ICPs justified by the evidence given, and does
   it change any result (robustness.json carries the disclosure-ICP variant)?
4. **H4.** Are the merged units right (shared points of connection)? Are trading periods 25–30 really 12:00–15:00
   local in summer? Is the ICP weighting reasonable when one merged unit holds Powerco? Is EA Networks (a 48 MW farm
   on about 21,000 ICPs) driving more than the leave-one-out suggests?
5. **The placebo and the contrast.** The contrast was added after seeing the placebo. Is calling it "the best
   estimate" defensible, or should the report lead with the preregistered −0.84 and the placebo's warning? Does the
   contrast have its own confound (solar can also lower evening offtake via batteries; evening loads changed with
   electrification)?
6. **Power.** Are the minimum detectable slopes computed sensibly (2.8 × bootstrap SE)? Is "the annual tests could
   not have succeeded" fair?
7. **The report.** Every number against the tables; the plain-terms section; the verdict line.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
