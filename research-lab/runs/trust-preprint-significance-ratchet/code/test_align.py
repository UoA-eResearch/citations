"""Synthetic checks of the alignment and classification. Run before any real pair."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align as A  # noqa: E402
import extract as X  # noqa: E402

passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok; failed += not ok


pre = X.extract("Mice treated with the drug gained less weight than controls (p = 0.08). Survival was longer in the "
                "treated group, t(18) = 2.5, p = .02. Expression of gene X was unchanged (p = 0.4).", "result")
pub = X.extract("Expression of gene X was unchanged (p = 0.41). Mice treated with the drug gained less weight than "
                "controls (p = 0.03). Survival was longer in the treated group, t(18) = 2.5, p = .02. A new subgroup "
                "analysis showed a difference in females (p = 0.01).", "result")
pairs, dropped, added = A.align(pre, pub)
cls = sorted((p["pre"]["p"], p["pub"]["p"], p["cls"], p["how"]) for p in pairs)
check("three aligned, one added, none dropped", len(pairs) == 3 and len(added) == 1 and not dropped, str(cls))
check("weight result crosses up (0.08 -> 0.03)", (0.08, 0.03, "crossing_up", "similar") in cls, str(cls))
check("t-test aligned exactly, unchanged", (0.02, 0.02, "unchanged", "exact") in cls, str(cls))
check("gene X changed but not crossing", (0.4, 0.41, "changed_not_crossing", "similar") in cls, str(cls))
# unrelated sentences are not aligned
a = X.extract("Blood pressure fell after treatment (p = 0.2).", "result")
b = X.extract("Cortical thickness increased with age in all cohorts (p = 0.01).", "result")
pairs, dropped, added = A.align(a, b)
check("unrelated sentences not aligned", not pairs and len(dropped) == 1 and len(added) == 1)
# different section groups not aligned
a = X.extract("Body weight was lower in treated mice (p = 0.04).", "abstract")
b = X.extract("Body weight was lower in treated mice (p = 0.04).", "discussion")
check("section groups respected", not A.align(a, b)[0])
# undetermined significance
a = X.extract("Body weight was lower in treated mice (p = 0.05).", "result")
b = X.extract("Body weight was lower in treated mice (p = 0.03).", "result")
check("p = 0.05 -> undetermined", A.align(a, b)[0][0]["cls"] == "undetermined")
print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
