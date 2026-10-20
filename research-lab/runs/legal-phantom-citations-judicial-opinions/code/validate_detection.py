"""Validate the screen against known-fabricated and known-real citations (plan section 4, step 5).

This calls parse.judge() -- the exact decision the screen makes for every citation -- rather than a second copy
of the logic. Two copies had already drifted apart once (D2), so the validator now tests the code that runs.

The six citations invented in the filings behind *Mata v. Avianca* are the field's canonical fabrications.
Writes results/tables/detection_validation.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse  # noqa: E402
from namenorm import clean_cited  # noqa: E402

T = Path(__file__).resolve().parents[1] / "results" / "tables"

# (plaintiff, defendant, volume, reporter, page) -- reporter citations where one exists, else names only
FABRICATED = [
    ("Varghese", "China Southern Airlines Co.", 925, "F.3d", 1339),
    ("Shaboon", "Egyptair", None, None, None),
    ("Petersen", "Iran Air", 905, "F. Supp. 2d", 121),
    ("Martinez", "Delta Airlines, Inc.", None, None, None),
    ("Estate of Durden", "KLM Royal Dutch Airlines", None, None, None),
    ("Miller", "United Airlines, Inc.", 174, "F.3d", 366),
]
REAL = [
    ("Mata", "Avianca, Inc.", None, None, None),
    ("Roe", "Wade", 410, "U.S.", 113),
    ("Brown", "Board of Education", 347, "U.S.", 483),
    ("Gideon", "Wainwright", 372, "U.S.", 335),
]


def main():
    T.mkdir(parents=True, exist_ok=True)
    parse.init()
    out = {"fabricated": [], "real": []}
    for group, items in (("fabricated", FABRICATED), ("real", REAL)):
        for p, d, vol, rep, page in items:
            j = parse.judge(rep, vol, page, clean_cited(p, d))
            out[group].append({"case": f"{p} v. {d}", "cite": f"{vol} {rep} {page}" if vol else None,
                               **{k: v for k, v in j.items() if k != "context"}})
    fab = out["fabricated"]
    out["summary"] = {
        "fabricated": len(fab),
        "phantom": sum(r["verdict"] == "phantom" for r in fab),
        "misattribution": sum(r["verdict"] == "misattribution" for r in fab),
        "missed": sum(r["verdict"] in ("consistent", "name-exists") for r in fab),
        "real_controls": len(REAL),
        "real_wrongly_flagged": sum(r["verdict"] in ("phantom", "misattribution") for r in out["real"]),
    }
    json.dump(out, open(T / "detection_validation.json", "w"), indent=1)
    print(json.dumps(out["summary"], indent=1))
    for g in ("fabricated", "real"):
        print(f"\n{g.upper()}")
        for r in out[g]:
            print(f"  {r['case'][:44]:<44} {r['verdict']:<15} route={r['route']}")


if __name__ == "__main__":
    main()
