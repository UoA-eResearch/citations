"""Hand adjudication of the extraction check (plan section 5), round 1: the 272 sampled papers (seed 20261019).

Each candidate signal (ROR with estimate and 95% CI, lower bound > 1, a stated window; marked CAND in
data/validation/extraction_focus.txt) was read against its abstract. A signal is correct when the database is FAERS, the
estimate and CI are the ROR the abstract gives for that drug and event, the estimate belongs to that drug alone and to that
event, and the window matches the stated period. Faithful extractions of class, combination, subgroup, comparator-restricted
or adjusted estimates are correct as extractions and carry a flag (the eligibility step drops classes and combinations).
Recall: CAND-level signals in the abstract that the extraction missed (none of them single-ingredient PT-level).
The 155 sampled papers outside the focus sheet have no numeric ROR in the abstract and no extracted ROR.
Writes results/tables/extraction_validation.csv and results/tables/extraction_validation.json."""
import json
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eligible  # noqa: E402
import rxnorm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]

# paper: {signal index: (correct, error or flag, note)}; signals not listed are CAND and correct with no flag
J = {
    "35349180": {},
    "36697083": {0: (0, "not a drug-event disproportionality", "aROR of dose per body weight >=12 mg/kg among olaparib users")},
    "36700393": {0: (1, "", "composite event as written")},
    "36830151": {1: (1, "combination", "")},
    "37332342": {0: (1, "combination", ""), 1: (1, "combination", ""), 2: (1, "class", "")},
    "37507539": {0: (1, "class", "")},
    "37615268": {},
    "38294705": {},
    "38384285": {k: (1, "class", "ADCs pooled") for k in range(8)},
    "38936945": {k: (0, "non-FAERS database", "Japanese Adverse Event Reporting Database") for k in range(4)},
    "38948476": {k: (1, "class", "ICIs pooled") for k in range(3)},
    "39031227": {0: (0, "non-FAERS database", "JADER"), 2: (0, "non-FAERS database", "JADER")},
    "39148544": {2: (0, "not a drug-event disproportionality", "males vs females within evolocumab; CI excludes the estimate as printed")},
    "39384812": {},
    "39419512": {0: (1, "combination", "HRZE regimen"), 1: (1, "combination", "BPaL regimen")},
    "39419623": {},
    "39459005": {k: (0, "non-FAERS database", "EudraVigilance, PCSK9-antagonist comparator") for k in range(3)},
    "39460482": {0: (1, "class", "PD-1 vs CTLA-4/PD-L1 inhibitors")},
    "39473255": {0: (0, "window", "stated March 2023, extracted 2023Q4")},
    "39635439": {2: (0, "non-FAERS database", "the respiratory-failure ROR is from JADER")},
    "39672542": {6: (0, "event split", "ROR belongs to the HLT ventricular arrhythmias and cardiac arrest"),
                 7: (0, "event split", "ROR belongs to the HLT ventricular arrhythmias and cardiac arrest")},
    "39738184": {1: (0, "estimate is a bound", "ROR025 copied as estimate and CI")},
    "39764463": {},
    "39767190": {4: (0, "estimate is a bound", "IC025 copied as the ROR CI")},
    "39888490": {},
    "40108669": {k: (0, "misattributed drug", "AG regimen subgroup estimate attributed to one component") for k in range(3)},
    "40140707": {},
    "40213702": {},
    "40266530": {},
    "40303631": {k: (0, "window", "stated June 2023, extracted 2023Q4") for k in range(11)},
    "40305875": {},
    "40376150": {},
    "40380893": {},
    "40465056": {},
    "40510111": {},
    "40520154": {},
    "40593869": {0: (1, "class", "bisphosphonates pooled")},
    "40637806": {},
    "40817421": {k: (1, "adjusted", "") for k in range(3)},
    "40824302": {k: (1, "adjusted", "within progestogen-contraceptive reports") for k in range(3)},
    "40920788": {},
    "41054114": {0: (0, "window", "stated March 2024, extracted 2024Q4; a metformin interaction signal for contrast media")},
    "41067279": {0: (1, "subgroup", "paediatric"), 1: (1, "subgroup", "paediatric")},
    "41471316": {k: (1, "class", "IL-1 inhibitors pooled") for k in range(5)},
}
# CAND-level signals the extraction missed: paper -> (count, single-ingredient PT-level count, note)
MISSED = {
    "36682994": (2, 0, "ICIs pooled RORs (hepatotoxicity, hepatic failure); only the ICs were extracted"),
    "40371340": (1, 0, "golimumab, infections SOC, ankylosing spondylitis stratum"),
    "40376150": (6, 0, "ATC drug-class RORs for cardiac arrest"),
    "40414255": (1, 0, "diazepam ROR 102.55 for ONH and/or SOD extracted as a PRR"),
    "41488140": (1, 0, "denosumab after zoledronic acid, CI dropped"),
}
WIN_ERR_NONCAND = ["40251175"]   # June 2024 extracted as 2024Q4; no ROR with CI in that abstract


def main():
    pick = json.load(open(RUN / "data" / "validation" / "extraction_sample.json"))
    ex = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data" / "extract" / "signals_raw.jsonl") if "out" in json.loads(l)}
    pts = {r[0] for r in duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True).execute("SELECT DISTINCT pt FROM reac").fetchall()}
    rows = []
    for pid in pick:
        o = ex[pid]["out"]; w = o.get("window")
        for k, s in enumerate(o.get("signals") or []):
            cand = (s.get("measure") == "ROR" and s.get("estimate") is not None and s.get("ci_low") is not None
                    and s.get("ci_high") is not None and s["ci_low"] > 1 and bool(w))
            if not cand:
                continue
            assert pid in J, f"unadjudicated paper {pid}"
            ok, tag, note = J[pid].get(k, (1, "", ""))
            ings = rxnorm.ingredients(s.get("drug", ""))
            single = len(ings) == 1
            pt = eligible.uk(s.get("event")).upper() in pts
            rows.append(dict(paper=pid, k=k, drug=s.get("drug"), event=s.get("event"), estimate=s.get("estimate"), ci_low=s["ci_low"],
                             ci_high=s["ci_high"], correct=ok, error=tag if not ok else "", flag=tag if ok else "", note=note,
                             single_ingredient=int(single), faers_pt=int(pt), eligible=int(single and pt)))
    rxnorm.save()
    a = pd.DataFrame(rows)
    assert set(a.paper) == set(J), set(J) ^ set(a.paper)
    a.to_csv(RUN / "results" / "tables" / "extraction_validation.csv", index=False)
    e = a[a.eligible == 1]
    out = dict(papers_sampled=len(pick), papers_with_cand=int(a.paper.nunique()),
               cand=dict(n=int(len(a)), correct=int(a.correct.sum()), precision=float(a.correct.mean())),
               eligible=dict(n=int(len(e)), correct=int(e.correct.sum()), precision=float(e.correct.mean()), papers=int(e.paper.nunique())),
               errors_cand=a[a.correct == 0].error.value_counts().to_dict(), errors_eligible=e[e.correct == 0].error.value_counts().to_dict(),
               errors_by_paper_eligible=e[e.correct == 0].paper.value_counts().to_dict(),
               missed_cand=sum(v[0] for v in MISSED.values()), missed_eligible=sum(v[1] for v in MISSED.values()),
               recall_eligible=float(len(e) / (len(e) + sum(v[1] for v in MISSED.values()))) if len(e) else None,
               window_errors_noncand=WIN_ERR_NONCAND)
    out["abort_rule"] = "pass" if out["eligible"]["precision"] >= 0.90 else "fail: revise the prompt once, re-validate on a fresh sample"
    json.dump(out, open(RUN / "results" / "tables" / "extraction_validation.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
