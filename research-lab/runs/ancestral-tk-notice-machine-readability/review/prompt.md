You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/ancestral-tk-notice-machine-readability/ (read-only except your output in
review/).

The question: does Indigenous-governance metadata (Local Contexts Notices and TK/BC Labels) appear in the open
research-data layer, and does it survive the machine views through which DOI metadata is copied onward?
- **Limb 1** is a census of nine platforms: DataCite, Zenodo, Dryad, Harvard Dataverse, figshare, OSF, GBIF, RAiD and
  re3data.
- **Limb 2** fetches nine machine views for up to 2,000 element-bearing DataCite DOIs (six DOI content-negotiation
  formats, OAI-PMH oai_dc and oai_datacite, and the OpenAIRE Graph). Each view is scored preserve / degrade / drop /
  unavailable.
- **H1:** fewer than 0.1% of element-bearing records carry a community TK/BC Label with a live Hub project.
- **H2:** at least 40% of record × view pairs drop the element (record-cluster bootstrap).
- **H2b:** no lossy view warns.

**What to read:**
- plan.md (preregistration);
- deviations.md (D1–D4). Note D2/D3 (paging bugs fixed before scanning) and D4 (H2 excludes adjudicated false
  positives; the hand check);
- report.md and report.html (pre-review draft, commit 1227857);
- code/: detect.py, census.py, precision.py, resolve_uris.py, views.py, handcheck.py, analysis.py, figures.py;
- results/tables/:
  - primary.json, census_by_platform.csv, view_matrix.csv, view_matrix_by_stratum.csv;
  - precision.csv, handcheck.csv, vocabulary.json;
- data/:
  - census.jsonl, census_errors.json, uri_status.json, views.jsonl;
  - raw/ (every API response, and the 18,000 view bodies gzipped under raw/views/);
  - validation/ (the hand-check sheet and sample);
  - precision_sample.txt, precision_key.csv.

**Git.** Read-only git in /mnt/citations is fine. Check that the code was committed before the outputs it produced,
and that the hand check and D4 came before H2 was computed.

**Environment.** Use venv/bin/python in the run directory, and do NOT pip install into it. Your files go under
review/reviewer_checks/, with caches under review/reviewer_checks/cache. You may make a few live API calls to verify
things, gently: one request at a time, 1 s apart, at most about 200 in total.

Check at least:

1. **Census completeness.** Is each platform's query right, and would it find Local Contexts elements stored the
   way that platform stores them? Consider:
   - DataCite: rightsList, subjects, descriptions, relatedIdentifiers and alternateIdentifiers;
   - Dryad's and Dataverse's integrations, figshare custom fields, GBIF machine tags, Zenodo's custom fields, and
     RAiD.

   Probe for false negatives with a few targeted live queries, such as known Local Contexts Hub projects linked to
   DOIs. Are the platform counts honest lower bounds, and are errors recorded as errors?
2. **Detection and classification.**
   - Re-check detect.py's URI and name patterns. Is "TK Open to Collaboration (TK CB)" a Label name, and is it right
     to say Neotoma's entries name a Label while pointing to a Notice URI?
   - Re-adjudicate at least 30 of the 69 name-only hits (precision.csv).
   - Is the H1 numerator rule (a Label plus a live Hub project) faithful to the lead's "community-authored, resolvable
     to a Hub project"?
   - Check the one counted record, and look for any missed record that should count.
3. **The crosswalk scoring.**
   - Re-score at least 60 record-views yourself from the raw bodies, oversampling degrade, preserve-in-unusual-views
     and OpenAIRE.
   - Is the JSON-LD "license = degrade" rule fair?
   - Is "unavailable" handled right (220 OpenAIRE views)?
   - Do the RIGHTS_FIELD patterns misclassify anything?
4. **The verdicts.** Recompute H1 (exact CI, with and without Neotoma) and H2 (record-cluster bootstrap, per view,
   by stratum). Is the pooled H2 an artefact of which views were preregistered (four of nine views structurally lack
   a rights field)? Is the report candid about that, and about Neotoma's dominance (1,971 of 1,998 DOIs)?
5. **D4.** Was excluding two DOIs from H2 justified and done before H2 was seen? Did it change the verdict?
6. **Numbers.** Does every number in report.md, report.html and the figure captions match the results files?
7. **Framing and care.** Are counts presented as describing systems, not communities? Is "absence may be by design"
   given its due? Does anything identify or judge a community or collection inappropriately?
   - Is the naming of specific repositories and stations (Neotoma, Gump, Tetiaroa, ADA, Landcare, VUW) appropriate
     and accurate?
   - Is the plain-language summary accurate and not overstated?

Write your review to review/review.md with:
- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of recomputed numbers;
- your re-adjudication tables, kept under review/reviewer_checks/.

Do not modify anything outside review/, and do not commit.
