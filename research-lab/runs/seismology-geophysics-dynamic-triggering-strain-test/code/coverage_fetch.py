"""G2 coverage for the download (plan section 1): every pick read is kept or dropped with a reason.
-> results/tables/coverage.json stage picks_fetch"""
import csv
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

r = list(csv.DictReader(open(RUN / "data" / "picks_counts.csv")))
read = sum(int(x["picks_read"]) for x in r)
conf = sum(int(x["picks_conf_in_range"]) for x in r)
kept = sum(int(x["picks_kept"]) for x in r)
cov = Coverage("picks_fetch", RUN / "results" / "tables" / "coverage.json")
cov.add_counts(ok=kept, drops={"confidence < 0.5 or outside 2002-2025": read - conf, "exact duplicate (tid, cha, pha, peak)": conf - kept})
cov.save()
print(len(r), "partitions;", sum(int(x["files"]) for x in r), "files")
