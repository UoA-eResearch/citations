"""Reviewer check 1: my adjudication of the fresh random sample (20 papers, 70 eligible signals; draw_fresh_sample.py)
and of the screen-targeted papers, against the abstracts in data/raw/epmc/records.jsonl. Rules as the study's: correct
when the database is FAERS, the estimate/CI are the ROR the abstract gives for that drug and event, the estimate
belongs to that drug alone (not a combination/regimen/factor contrast), and the window matches. Mapping errors
(RxNorm ingredient wrong) and comparison-label errors are recorded separately. No abstract text is copied here."""
from pathlib import Path
import pandas as pd
OUT = Path(__file__).resolve().parent
RUN = OUT.parents[1]
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
# random fresh sample: paper -> {k: (correct, error, mapping_ok, comparison_ok, note)}; signals not listed are correct with no flag
R = {
 "41560737": {}, "37536976": {}, "41118058": {}, "37130046": {}, "40936323": {}, "38783948": {}, "38027003": {}, "38041205": {}, "40828435": {},
 "35491805": {}, "40329904": {}, "38034088": {},
 "37996645": {5: (1, "", 1, 1, "probable class estimate (tetracyclines) attributed to the ingredient tetracycline; faithful to the abstract")},
 "39840315": {4: (1, "", 0, 0, "TAC is tacrolimus, mapped to triamcinolone; analysis restricted to paediatric nephrotic-syndrome reports (subgroup)"),
              5: (1, "", 0, 0, "as k=4"), 0: (1, "", 1, 0, "subgroup, labelled all drugs"), 1: (1, "", 1, 0, "subgroup"), 2: (1, "", 1, 0, "subgroup")},
 "37240654": {k: (0, "misattributed drug", 1, 0, "daptomycin + statin combination estimate attributed to the statin alone; an interaction analysis") for k in range(5)},
 "37154187": {k: (1, "", 1, 0, "restricted to COVID-19 reports (subgroup), labelled all drugs") for k in (0, 2, 8, 10, 12)},
 "39135789": {0: (1, "", 1, 0, "children under 8 (subgroup), labelled all drugs")},
 "39472591": {7: (1, "", 1, 0, "within HNSCC-treatment reports (comparator), labelled all drugs; n_cases is the total hypertension count")},
 "40095047": {1: (1, "", 1, 1, "RG2 is a comparator (other MM drugs), labelled subgroup; not all drugs either way")},
 "40552159": {12: (0, "non-FAERS database", 1, 1, "JADER-specific signal labelled FAERS"), 16: (0, "non-FAERS database", 1, 1, "JADER-specific signal labelled FAERS")},
}
# targeted (not random): anomaly abstracts and the abstract screen
T = {
 "40567936": {k: (0, "non-FAERS database", 1, 1, "the whole study is JADER (propensity-adjusted ROR)") for k in (0, 1, 3, 5, 11)},
 "36697083": {0: (0, "not a drug-event disproportionality", 1, 0, "aROR of dose per body weight within olaparib users (round-1 error type, still present)")},
 "38936945": {0: (0, "non-FAERS database", 1, 1, "JADER (round-1 error type, still present)"), 1: (0, "non-FAERS database", 1, 1, "JADER; adjusted ROR")},
 "40115262": {1: (1, "", 0, 0, "CD is carbidopa, mapped to pyrimethamine; background restricted to oral PD drugs (comparator)")},
 "39842538": {0: (1, "", 1, 0, "vs other antiarrhythmics, adults (comparator/subgroup), labelled all drugs"), 1: (1, "", 1, 0, "as k=0, older adults"),
              2: (1, "", 1, 0, "as k=0"), 3: (1, "", 1, 0, "as k=0"), 6: (1, "", 1, 1, "")},
 "38100054": {0: (1, "", 0, 1, "trastuzumab deruxtecan mapped to trastuzumab: exposure conflates all trastuzumab products"),
              2: (1, "", 0, 1, "trastuzumab emtansine mapped to trastuzumab")},
 "40166653": {0: (1, "", 0, 1, "trastuzumab deruxtecan mapped to trastuzumab")},
 "40620108": {0: (1, "", 0, 1, "trastuzumab deruxtecan mapped to trastuzumab"), 1: (1, "", 0, 1, "trastuzumab emtansine mapped to trastuzumab"),
              3: (1, "", 1, 1, "plain trastuzumab; its b includes the ADCs")},
 "40770257": {0: (1, "", 0, 1, "T-DM1 mapped to trastuzumab"), 1: (1, "", 1, 1, "")},
 "40888754": {0: (1, "", 0, 1, "trastuzumab deruxtecan mapped to trastuzumab")}, "41398841": {0: (1, "", 0, 1, "trastuzumab deruxtecan mapped to trastuzumab")},
 "38878281": {}, "39431859": {}, "39906745": {}, "36909171": {}, "39635439": {}, "40133436": {}, "40383360": {}, "40814133": {}, "36778017": {}, "37507539": {},
 "37608525": {}, "38179676": {}, "38860168": {}, "38902469": {}, "39419623": {}, "39759530": {}, "41087308": {},
}
rows = []
for kind, adj in (("random", R), ("targeted", T)):
    for p, d in adj.items():
        sub = e[e.paper == p]
        assert len(sub), p
        for s in sub.itertuples():
            ok, err, mp, cmp_, note = d.get(s.k, (1, "", 1, 1, ""))
            rows.append(dict(sample_kind=kind, paper=p, k=s.k, drug=s.drug, ingredient=s.ingredient, event=s.event, estimate=s.estimate, comparison=s.comparison,
                             extraction_correct=ok, error=err, mapping_ok=mp, comparison_label_ok=cmp_, note=note))
a = pd.DataFrame(rows); a.to_csv(OUT / "fresh_sample_adjudication.csv", index=False)
r = a[a.sample_kind == "random"]
print("RANDOM fresh sample: papers", r.paper.nunique(), "signals", len(r))
print(" extraction precision:", r.extraction_correct.sum(), "/", len(r), "=", round(r.extraction_correct.mean(), 3))
print(" errors:", r[r.extraction_correct == 0].error.value_counts().to_dict(), "| papers with an error:", r[r.extraction_correct == 0].paper.nunique())
print(" mapping wrong:", int((r.mapping_ok == 0).sum()), "| extraction and mapping both right:", int(((r.extraction_correct == 1) & (r.mapping_ok == 1)).sum()), "/", len(r))
print(" comparison label wrong:", int((r.comparison_label_ok == 0).sum()), "/", len(r), "| label accuracy", round(r.comparison_label_ok.mean(), 3))
print(" 'all drugs' labels that were restricted comparisons:", int(((r.comparison == "all drugs") & (r.comparison_label_ok == 0)).sum()), "of", int((r.comparison == "all drugs").sum()))
# paper-cluster bootstrap CI for precision
import numpy as np
rng = np.random.default_rng(3); ps = r.paper.unique(); g = {p: r[r.paper == p].extraction_correct.values for p in ps}
bs = [np.concatenate([g[p] for p in rng.choice(ps, len(ps))]).mean() for _ in range(4000)]
print(" paper-cluster bootstrap 95% CI for precision:", np.round(np.percentile(bs, [2.5, 97.5]), 3))
t = a[a.sample_kind == "targeted"]
print("\nTARGETED: signals", len(t), "| extraction wrong", int((t.extraction_correct == 0).sum()), "| mapping wrong", int((t.mapping_ok == 0).sum()), "| comparison label wrong", int((t.comparison_label_ok == 0).sum()))
allw = a[(a.extraction_correct == 0) | (a.mapping_ok == 0)].drop_duplicates(["paper", "k"])
print("known-wrong analysed signals (extraction or mapping), all samples:", len(allw), "in", allw.paper.nunique(), "papers")
