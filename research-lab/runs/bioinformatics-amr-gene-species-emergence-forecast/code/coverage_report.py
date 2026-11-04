"""G2 coverage: isolates and candidate pairs through each step.

  coverage_report.py -> results/tables/coverage.json
"""
import json
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

b = json.loads((T / "build.json").read_text())
pr = json.loads((T / "proteins.json").read_text())
tr = json.loads((T / "task_train.json").read_text())
te = json.loads((T / "task_test.json").read_text())
path = T / "coverage.json"
if path.exists():
    path.unlink()

c = Coverage("isolates", path)
# D3 (review finding 10): build.json counts rows failing both the year and the species rule in both categories; the
# overlap is whatever makes kept + drops exceed the rows read, and is removed from the species category.
both = (b["isolates_kept"] + (b["rows"] - b["unique_biosamples"]) + b["no_year_or_out_of_range"] + b["no_species"]
        + b["no_amr_call_field"] + b["isolates_dropped_older_db"]) - b["rows"]
c.add_counts(ok=b["isolates_kept"], drops={
    "duplicate biosample": b["rows"] - b["unique_biosamples"],
    "no collection year, or outside 1990-2025": b["no_year_or_out_of_range"],
    "no species binomial (with a valid year)": b["no_species"] - both,
    "no AMR call field": b["no_amr_call_field"],
    "screened with a reference catalog older than the oldest audited one (D1)": b["isolates_dropped_older_db"]})
c.save()

c = Coverage("gene_symbols_with_a_reference_protein", path)
c.add_counts(ok=pr["genes_seen"] - pr["by_match"]["unmatched"], drops={"no protein in the catalog or FASTA": pr["by_match"]["unmatched"]})
c.save()

c = Coverage("embedding_feature_rows_test", path)
# D3 (review finding 10): one gene with no embedding gets a zero vector in candidates.py (cosine 0)
c.add_counts(ok=472779 - 156, fallbacks={"UNPLANNED (not in the plan): gene without an embedding (dfrA51) given a zero vector, cosine 0; 2 positives": 156})
c.save()

for nm, t in (("candidates_train_2019", tr), ("candidates_test_2022", te)):
    c = Coverage(nm, path)
    c.add_counts(ok=t["emerged_in_candidates"],
                 drops={"emerged but outside the candidate set (species under 20 isolates, or gene not yet established)":
                        t["emerged_pairs_total"] - t["emerged_in_candidates"]})
    c.save()
print(json.dumps(json.loads(path.read_text()), indent=1)[:800])
