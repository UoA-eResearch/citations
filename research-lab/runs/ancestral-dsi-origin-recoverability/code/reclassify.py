"""Re-apply the classifier to the stored country field of every parsed sample (deviations D4), without re-parsing the
dump. Rewrites country_class and country_resolved in data/samples/*.parquet and logs the changes to
results/tables/reclassify_log.json.
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import countries  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    changes, total = Counter(), 0
    for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
        d = pd.read_parquet(f)
        new = d.country_raw.map(lambda v: countries.classify(v if isinstance(v, str) else None))
        cls, res = new.str[0], new.str[1]
        moved = d.country_class != cls
        for a, b in zip(d.country_class[moved], cls[moved]):
            changes[f"{a}->{b}"] += 1
        total += len(d)
        d["country_class"], d["country_resolved"] = cls, res
        d.to_parquet(f, index=False)
    out = {"samples": total, "changed": dict(changes), "changed_total": int(sum(changes.values()))}
    json.dump(out, open(RUN / "results" / "tables" / "reclassify_log.json", "w"), indent=1)
    print(out)


if __name__ == "__main__":
    main()
