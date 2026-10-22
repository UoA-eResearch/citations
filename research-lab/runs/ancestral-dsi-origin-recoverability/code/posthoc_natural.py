"""Post hoc (D7, after limb-2 results were read): recovery among natural samples only, i.e. with records labelled
"inapplicable" (laboratory material) removed. Not preregistered; reported as exploratory."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import ARMS, ND, TAB, wilson  # noqa: E402

d = pd.read_csv(TAB / "limb2_rows.csv", keep_default_na=False)
out = {}
for split in ("test", "all"):
    x = d if split == "all" else d[d.split == split]
    nat = x[x.label != "inapplicable"]
    det = int((nat.gold != ND).sum())
    o = {"natural_records": len(nat), "determinable": det, "ceiling": round(det / len(nat), 4),
         "ceiling_ci": wilson(det, len(nat)), "arms_any_confidence": {}}
    for a in ARMS:
        m = nat[nat[a] != ""]
        ok = int((m[a] == m.gold).sum())
        o["arms_any_confidence"][a] = {"predictions": len(m), "correct": ok,
                                       "precision": round(ok / len(m), 4) if len(m) else None,
                                       "precision_ci": wilson(ok, len(m)), "recovery": round(ok / len(nat), 4),
                                       "recall_of_determinable": round(ok / det, 4) if det else None}
    out[split] = o
(TAB / "limb2_posthoc_natural.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
