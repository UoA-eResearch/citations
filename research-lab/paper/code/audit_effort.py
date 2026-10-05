"""Effort measure (added after the protocol; git timestamps proved unusable): from the main-loop session transcripts,
the first and last timestamp of any assistant tool call whose input mentions a run directory name, plus the number of
such tool calls and the total main-loop active time on that run (gaps > 30 min between consecutive mentions excluded).
Transcripts are not published (they contain the lab owner's messages); only these derived numbers are.
Writes paper/audit/F_effort.csv."""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
TRANS = sorted((Path.home() / ".claude" / "projects" / "-mnt-citations").glob("*.jsonl"))
RUNS = sorted(p.name for p in (REPO / "research-lab" / "runs").iterdir() if p.is_dir())
OUT = REPO / "research-lab" / "paper" / "audit"


def main():
    hits = {r: [] for r in RUNS}
    for f in TRANS:
        for line in open(f, errors="ignore"):
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                continue
            if m.get("type") != "assistant":
                continue
            ts = m.get("timestamp")
            for c in (m.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    s = json.dumps(c.get("input", {}))
                    for r in RUNS:
                        if r in s:
                            hits[r].append(ts)
    rows = []
    for r, t in hits.items():
        if not t:
            rows.append(dict(run=r, n_tool_calls=0))
            continue
        t = pd.to_datetime(pd.Series(sorted(t)), utc=True)
        gaps = t.diff().dt.total_seconds().fillna(0)
        active_h = gaps[gaps <= 1800].sum() / 3600
        rows.append(dict(run=r, n_tool_calls=len(t), first=t.iloc[0].tz_convert("Pacific/Auckland").strftime("%Y-%m-%d %H:%M"),
                         last=t.iloc[-1].tz_convert("Pacific/Auckland").strftime("%Y-%m-%d %H:%M"),
                         span_days=(t.iloc[-1] - t.iloc[0]).total_seconds() / 86400, active_hours=active_h))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "F_effort.csv", index=False)
    print(d.round(2).to_string(index=False))
    print("transcripts:", [f.name for f in TRANS])


if __name__ == "__main__":
    main()
