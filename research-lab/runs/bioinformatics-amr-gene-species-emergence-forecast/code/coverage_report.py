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
c.add_counts(ok=b["isolates_kept"], drops={
    "duplicate biosample": b["rows"] - b["unique_biosamples"],
    "no collection year, or outside 1990-2025": b["no_year_or_out_of_range"],
    "no species binomial": b["no_species"],
    "no AMR call field": b["no_amr_call_field"],
    "screened with a reference catalog older than the oldest audited one (D1)": b["isolates_dropped_older_db"]})
c.save()

c = Coverage("gene_symbols_with_a_reference_protein", path)
c.add_counts(ok=pr["genes_seen"] - pr["by_match"]["unmatched"], drops={"no protein in the catalog or FASTA": pr["by_match"]["unmatched"]})
c.save()

for nm, t in (("candidates_train_2019", tr), ("candidates_test_2022", te)):
    c = Coverage(nm, path)
    c.add_counts(ok=t["emerged_in_candidates"],
                 drops={"emerged but outside the candidate set (species under 20 isolates, or gene not yet established)":
                        t["emerged_pairs_total"] - t["emerged_in_candidates"]})
    c.save()
print(json.dumps(json.loads(path.read_text()), indent=1)[:800])
