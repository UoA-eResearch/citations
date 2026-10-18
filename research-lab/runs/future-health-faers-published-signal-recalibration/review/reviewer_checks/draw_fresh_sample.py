"""Reviewer check 1: draw a fresh adjudication sample of eligible signals from papers in neither validation round.
Seed 20261101. Prints the signals (no abstract text is written to a committed file)."""
import json, random
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
r1 = set(json.load(open(RUN / "data" / "validation" / "extraction_sample.json")))
r2 = set(json.load(open(RUN / "data" / "validation" / "extraction_sample_round2.json")))
papers = sorted(set(e.paper) - r1 - r2)
print("eligible papers", e.paper.nunique(), "| in round 1:", len(set(e.paper) & r1), "| in round 2:", len(set(e.paper) & r2), "| fresh:", len(papers))
pick = random.Random(20261101).sample(papers, 20)
sub = e[e.paper.isin(pick)].sort_values(["paper", "k"])
print(len(pick), "papers;", len(sub), "eligible signals")
sub[["paper", "k", "drug", "ingredient", "event", "event_uk", "estimate", "ci_low", "ci_high", "n_cases", "comparison", "win"]].to_csv(OUT / "fresh_sample_signals.csv", index=False)
json.dump(pick, open(OUT / "fresh_sample_papers.json", "w"))
