"""Replace meta descriptions copied from another study (report builders were copied run to run with the description
hard-coded). For each run whose report.html description starts with another study's text, the description becomes the
report's own subtitle (the first italic line after the H1 in report.md), in report.html and in code/build_report_html.py."""
import html
import re
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"
STALE = {"A preregistered test of whether sparse-autoencoder features of Pythia-160M": "ai-evaluation-science-sae-pretraining-seed-universality",
         "Are heat records being broken by growing margins?": "climate-earth-record-margin-obs"}
META = re.compile(r'(<meta name="description" content=")([^"]*)(")')


def subtitle(md):
    lines = md.split("\n")
    for i, l in enumerate(lines):
        if l.startswith("# "):
            for m in lines[i + 1:i + 8]:
                if m.startswith("*") and not m.startswith("**"):
                    txt = m.strip()
                    j = lines.index(m) + 1
                    while not txt.endswith("*") and j < len(lines) and lines[j].strip():
                        txt += " " + lines[j].strip(); j += 1
                    return re.sub(r"[*_`]", "", txt).strip()
    return None


def main(apply=False):
    for run in sorted(RUNS.iterdir()):
        rh = run / "report.html"
        if not rh.exists():
            continue
        h = rh.read_text()
        m = META.search(h)
        if not m:
            continue
        owner = next((o for k, o in STALE.items() if m.group(2).startswith(k)), None)
        if owner is None or owner == run.name:
            continue
        sub = subtitle((run / "report.md").read_text()) if (run / "report.md").exists() else None
        if not sub:
            print("NO SUBTITLE", run.name); continue
        new = html.escape(sub[:300], quote=True)
        print(run.name, "->", new[:90])
        if apply:
            rh.write_text(META.sub(lambda x: x.group(1) + new + x.group(3), h, count=1))
            b = run / "code" / "build_report_html.py"
            if b.exists():
                bs = b.read_text()
                mb = META.search(bs)
                if mb and any(mb.group(2).startswith(k) for k in STALE):
                    b.write_text(bs.replace(mb.group(2), new.replace("\\", "\\\\"), 1))


if __name__ == "__main__":
    main(apply=len(sys.argv) > 1 and sys.argv[1] == "apply")
