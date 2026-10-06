"""The paper's frozen study set: the 19 run directories that existed when the audit began (audit/runs.txt) and the 17
with a report at the audit snapshot (audit/reported_snapshot.txt, = reports present at commit 90930ab). Studies or
reports added later do not change the paper's numbers."""
from pathlib import Path

AUD = Path(__file__).resolve().parents[1] / "audit"
RUNS_ALL = [x.strip() for x in (AUD / "runs.txt").read_text().split() if x.strip()]
REPORTED = [x.strip() for x in (AUD / "reported_snapshot.txt").read_text().split() if x.strip()]
