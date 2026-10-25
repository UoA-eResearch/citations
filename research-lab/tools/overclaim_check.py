"""G5 overclaim check (see METHODS.md): every headline-level sentence of a report must be backed by a reported number.

    python3 -I tools/overclaim_check.py RUN_DIR
        extracts from RUN_DIR/report.md: the title, the italic standfirst, the verdict line and its bullets, and every
        sentence of "## In plain terms" -> RUN_DIR/review/overclaim_check.md, a table to fill in:
        | # | where | sentence | backing (table/figure + number) | label | fix |
        labels: Supported | Partially supported | Overstated | Not addressed | Exploratory-labelled
        Existing labels in an older overclaim_check.md are carried over for unchanged sentences.
    python3 -I tools/overclaim_check.py RUN_DIR --verify
        fails (exit 1) if any row lacks a label or backing, or is labelled Overstated / Not addressed / Partially
        supported without a fix recorded
"""
import re
import sys
from pathlib import Path

LABELS = ("Supported", "Partially supported", "Overstated", "Not addressed", "Exploratory-labelled")


def sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(*])", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def extract(md):
    lines = md.split("\n")
    out = []
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
    out.append(("title", title))
    body = "\n".join(lines)
    m = re.search(r"\n\*([^*][\s\S]*?)\*\n", body)                   # italic standfirst
    if m:
        out += [("standfirst", s) for s in sentences(m.group(1))]
    v = re.search(r"\*\*Verdict:[\s\S]*?(?=\n## )", body)             # verdict block up to the first section
    if v:
        items = []                                                    # join wrapped continuation lines to their bullet
        for l in v.group(0).split("\n"):
            st = l.strip()
            if not st or st.startswith("|"):
                continue
            if re.match(r"^([-*]\s+|\*\*)", st) or not items:
                items.append(re.sub(r"^[-*]\s+", "", st))
            else:
                items[-1] += " " + st
        for it in items:
            out += [("verdict", s) for s in sentences(it)]
    p = re.search(r"\n## In plain terms\n([\s\S]*?)(?=\n## )", body)
    if p:
        out += [("plain terms", s) for s in sentences(p.group(1))]
    return out


def table_rows(path):
    rows = {}
    if not path.exists():
        return rows
    for l in path.read_text().split("\n"):
        if l.startswith("| ") and not l.startswith("| #") and not l.startswith("|---"):
            c = [x.strip() for x in l.strip("|").split("|")]
            if len(c) >= 6:
                rows[c[2]] = c
    return rows


def write(run):
    run = Path(run)
    rep = (run / "report.md").read_text()
    out = run / "review" / "overclaim_check.md"
    old = table_rows(out)
    rows = extract(rep)
    lines = ["# Overclaim check (G5)", "",
             "Fill in every row: backing = the table/figure and number that supports the sentence; label = one of "
             + ", ".join(LABELS) + ". Every Overstated / Not addressed / Partially supported row needs a fix (the "
             "rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.", "",
             "| # | where | sentence | backing | label | fix |", "|---|---|---|---|---|---|"]
    for i, (where, s) in enumerate(rows, 1):
        s = s.replace("|", "/")
        prev = old.get(s)
        b, lab, fix = (prev[3], prev[4], prev[5]) if prev else ("", "", "")
        lines.append(f"| {i} | {where} | {s} | {b} | {lab} | {fix} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(len(rows), "sentences ->", out, f"({sum(1 for _, s in rows if s.replace('|', '/') in old)} carried over)")


def verify(run):
    rows = table_rows(Path(run) / "review" / "overclaim_check.md")
    bad = []
    for s, c in rows.items():
        backing, lab, fix = c[3], c[4], c[5]
        if lab not in LABELS or not backing:
            bad.append((c[0], "missing label/backing"))
        elif lab in ("Overstated", "Not addressed", "Partially supported") and not fix:
            bad.append((c[0], f"{lab} without a fix"))
    for n, why in bad:
        print(f"row {n}: {why}")
    print("G5", "FAILED" if bad else "passed", f"({len(rows)} rows)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    (verify if "--verify" in sys.argv else write)(sys.argv[1])
