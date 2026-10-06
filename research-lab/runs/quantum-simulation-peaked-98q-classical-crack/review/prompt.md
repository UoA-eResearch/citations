You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Your job is to find
what is wrong, unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/quantum-simulation-peaked-98q-classical-crack/ (read-only, except for your
output file). Read plan.md (the preregistration, commit ff1996a), deviations.md (D1-D6), report.md (the draft
report), code/ (attack_unswap.py, attack_distill.py, attack_pauli.py, select_candidates.py, score.py, seal_answers.py,
structure.py, figures.py), results/ (all JSON and tables, final_candidates.json, score.json) and logs/ as needed.
You may run read-only git commands in /mnt/citations. The sealed answers are in data/sealed/answers.json: do not open
that file or print its contents. score.py has already read it once, and score.json records the result.

Check at least:
1. Did the blinding hold? Were the final candidates fixed and committed (with hashes) before the sealed answers were
   read? Could any attack or selection step have used the answers?
2. Was the preregistered decision rule applied as written? Are the verdict ("Refuted") and its scope stated
   correctly?
3. Are the deviations justified, disclosed and timestamped? Did any deviation favour a particular outcome?
4. Is the budget accounting correct (P11 71.0 h, P12 30.7 h), and were the attacks run as the plan specified, or as
   amended by logged deviations?
5. Does every number in report.md match the results files and logs? Recompute the key ones.
6. Is the mechanistic explanation ("Why A1 fails on P11") supported by the logs, or overstated?
7. Are the caveats complete? What would a quantum-simulation expert object to? Use web search if needed, for example
   to check whether P11 or P12 have since been cracked classically, or what is known about these circuits.

Write your review to /mnt/citations/research-lab/runs/quantum-simulation-peaked-98q-classical-crack/review/review.md:
a recommendation (publish / publish with edits / fix first), numbered issues with locations and concrete fixes, and a
table of the numbers you recomputed. Reply with the recommendation and the number of issues.
