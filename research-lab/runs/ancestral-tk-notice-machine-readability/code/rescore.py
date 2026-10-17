"""D5: re-score every saved machine-view body with the corrected scorer and detector (no re-fetching). The first-run
scores are kept in data/views_v1.jsonl; data/views.jsonl is rewritten with the new result."""
import gzip
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from views import score  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    src = RUN / "data" / "views_v1.jsonl"
    if not src.exists():
        shutil.copy(RUN / "data" / "views.jsonl", src)
    out, changes = [], Counter()
    for l in open(src):
        v = json.loads(l)
        body = gzip.decompress((RUN / "data" / "raw" / "views" / f"{v['doi'].replace('/', '_')}__{v['view']}.gz").read_bytes()).decode("utf-8", "replace")
        new = score(v["view"], v["status"], body)
        if new != v["result"]:
            changes[(v["view"], v["result"], new)] += 1
        v["result_v1"], v["result"] = v["result"], new
        out.append(v)
    with open(RUN / "data" / "views.jsonl", "w") as fh:
        for v in out:
            fh.write(json.dumps(v) + "\n")
    print(len(out), "views re-scored; changes:", dict(changes))


if __name__ == "__main__":
    main()
