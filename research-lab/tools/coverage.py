"""G2 coverage accounting: no silent fallbacks (see METHODS.md).

Every per-unit stage that can fail records what happened to each unit, and the counts go into the results.

    from coverage import Coverage                        # sys.path.insert(0, "<lab>/tools")
    cov = Coverage("rf_fit", RUN / "results" / "tables" / "coverage.json")
    for unit in units:
        cov.attempt(unit)
        try:
            value = compute(unit)
        except TimeoutError:
            cov.drop(unit, "timeout")                    # unit excluded from the analysis
            continue
        if value is None:
            value = default; cov.fallback(unit, "no parse -> default")   # value replaced; must be named in plan.md
        else:
            cov.ok(unit)
    cov.save()                                           # merges this stage into coverage.json; prints a summary

    python3 -I tools/coverage.py RUN_DIR                 # print every stage's counts (for report.md)

Fallbacks that change a value fail loudly unless the plan names them: pass allowed=("reason", ...) to Coverage and
any other fallback reason raises.
"""
import json
import sys
from collections import Counter
from pathlib import Path


class Coverage:
    def __init__(self, stage, path, allowed=None):
        self.stage, self.path = stage, Path(path)
        self.allowed = set(allowed) if allowed is not None else None
        self.attempted = 0
        self.status = {}
        self.reasons = {"fallback": Counter(), "drop": Counter()}

    def attempt(self, unit):
        self.attempted += 1
        self.status[unit] = "attempted"

    def ok(self, unit):
        self.status[unit] = "ok"

    def fallback(self, unit, reason):
        if self.allowed is not None and reason not in self.allowed:
            raise RuntimeError(f"[{self.stage}] unplanned fallback for {unit!r}: {reason}")
        self.status[unit] = "fallback"
        self.reasons["fallback"][reason] += 1

    def drop(self, unit, reason):
        self.status[unit] = "drop"
        self.reasons["drop"][reason] += 1

    def summary(self):
        c = Counter(self.status.values())
        unresolved = c.get("attempted", 0)
        return {"attempted": self.attempted, "ok": c.get("ok", 0), "fallback": c.get("fallback", 0),
                "dropped": c.get("drop", 0), "unresolved": unresolved,
                "fallback_reasons": dict(self.reasons["fallback"]), "drop_reasons": dict(self.reasons["drop"])}

    def save(self):
        s = self.summary()
        if s["unresolved"]:
            raise RuntimeError(f"[{self.stage}] {s['unresolved']} units attempted but never marked ok/fallback/drop")
        allc = json.loads(self.path.read_text()) if self.path.exists() else {}
        allc[self.stage] = s
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(allc, indent=1))
        print(f"coverage[{self.stage}]: {s['ok']}/{s['attempted']} ok, {s['fallback']} fallback, {s['dropped']} dropped",
              flush=True)
        return s


def report_line(run_dir):
    p = Path(run_dir) / "results" / "tables" / "coverage.json"
    if not p.exists():
        return "coverage.json missing (G2 not satisfied)"
    allc = json.loads(p.read_text())
    parts = []
    for st, s in allc.items():
        extra = []
        if s["fallback"]:
            extra.append(f"{s['fallback']} fallback ({', '.join(f'{k} {v}' for k, v in s['fallback_reasons'].items())})")
        if s["dropped"]:
            extra.append(f"{s['dropped']} dropped ({', '.join(f'{k} {v}' for k, v in s['drop_reasons'].items())})")
        parts.append(f"{st}: {s['ok']:,}/{s['attempted']:,} ok" + (f"; {'; '.join(extra)}" if extra else ""))
    return "Coverage — " + " · ".join(parts)


if __name__ == "__main__":
    print(report_line(sys.argv[1]))
