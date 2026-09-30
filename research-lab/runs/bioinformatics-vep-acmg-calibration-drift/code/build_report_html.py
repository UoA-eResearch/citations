#!/usr/bin/env python
"""Render report.md -> report.html (GitHub Pages), with figure captions from results/figures/*.txt.

Usage: venv/bin/python code/build_report_html.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import markdown

RUN = Path(__file__).resolve().parents[1]
REPO_BLOB = "https://github.com/UoA-eResearch/citations/blob/main/research-lab/runs/" + RUN.name
FIG = RUN / "results" / "figures"
TAB = RUN / "results" / "tables"


def caption_for(src: str) -> str:
    p = RUN / src
    cap = p.with_suffix(".txt")
    return cap.read_text().strip() if cap.exists() else ""


def tiles() -> str:
    """Key-result tiles from results/tables/tiles.json: a list of [label, value, note] written by the analysis."""
    p = TAB / "tiles.json"
    items = json.load(open(p)) if p.exists() else []
    cells = "".join(f'<div class="tile"><div class="tile-label">{html.escape(a)}</div>'
                    f'<div class="tile-value{" text" if (b[:1].isalpha() or "→" in b) else ""}">{html.escape(b)}</div>'
                    f'<div class="tile-note">{html.escape(c)}</div></div>'
                    for a, b, c in items)
    return f'<section class="tiles" aria-label="Key results">{cells}</section>'


def main():
    md = (RUN / "report.md").read_text()
    # title + subtitle handled by the template
    lines = md.splitlines()
    title = lines[0].lstrip("# ").strip()
    subtitle = lines[2].strip("* ").strip() if len(lines) > 2 else ""
    body_md = "\n".join(l for l in lines[3:] if not l.startswith("Run directory:") and not l.startswith("Every departure from it:"))
    # links to repo files that Pages would serve as raw text
    body_md = body_md.replace("](plan.md)", f"]({REPO_BLOB}/plan.md)").replace("](deviations.md)", f"]({REPO_BLOB}/deviations.md)")
    body = markdown.markdown(body_md, extensions=["tables", "fenced_code", "sane_lists"])

    # figures with captions
    def fig(m):
        alt, src = m.group(1), m.group(2)
        cap = html.escape(caption_for(src))
        return (f'<figure><a href="{src}"><img src="{src}" alt="{html.escape(alt)}"></a>'
                f'<figcaption>{cap}</figcaption></figure>')
    body = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" ?/?></p>', fig, body)
    # typographic subscripts (outside code)
    parts = re.split(r"(<code>.*?</code>|<pre>.*?</pre>)", body, flags=re.S)
    body = "".join(x if x.startswith(("<code>", "<pre>")) else x for x in parts)
    # wide tables scroll inside their own container
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    page = TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__SUBTITLE__", html.escape(subtitle)) \
                   .replace("__TILES__", tiles()).replace("__BODY__", body).replace("__BLOB__", REPO_BLOB)
    (RUN / "report.html").write_text(page)
    print("wrote", RUN / "report.html", f"({len(page) / 1024:.0f} KB)")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PP3/BP4 Calibration Drift</title>
<meta name="description" content="Do the ClinGen PP3/BP4 missense-predictor thresholds still hold on variants classified after they were set? A preregistered prospective audit on ClinVar 2021-2026.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>%E2%97%8E</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {
  --ground: #fbfbf9; --surface: #ffffff; --ink: #141413; --ink-2: #4f4e4a; --muted: #85847e;
  --rule: #e4e3dd; --accent: #2a78d6; --accent-ink: #1c5cab; --observed: #d95926; --tile: #f3f2ee;
  --code-bg: #f1f0eb; --shadow: 0 1px 2px rgba(20,20,19,.05);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #121312; --surface: #1a1b1a; --ink: #ecebe6; --ink-2: #bcbbb3; --muted: #8a8983;
    --rule: #2c2d2b; --accent: #5598e7; --accent-ink: #86b6ef; --observed: #eb6834; --tile: #1f201f;
    --code-bg: #232422; --shadow: none;
  }
}
:root[data-theme="dark"] {
  --ground: #121312; --surface: #1a1b1a; --ink: #ecebe6; --ink-2: #bcbbb3; --muted: #8a8983;
  --rule: #2c2d2b; --accent: #5598e7; --accent-ink: #86b6ef; --observed: #eb6834; --tile: #1f201f;
  --code-bg: #232422; --shadow: none;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--ground); color: var(--ink);
  font: 17px/1.62 "IBM Plex Serif", Georgia, "Times New Roman", serif; }
.page { max-width: 1040px; margin: 0 auto; padding: 40px 24px 96px; }
header.masthead { max-width: 760px; margin: 0 auto 28px; }
.eyebrow { font: 600 12px/1.4 "IBM Plex Sans", system-ui, sans-serif; letter-spacing: .09em; text-transform: uppercase;
  color: var(--accent-ink); margin-bottom: 10px; }
h1 { font: 700 38px/1.15 "IBM Plex Sans", system-ui, sans-serif; letter-spacing: -.02em; margin: 0 0 10px; text-wrap: balance; }
.subtitle { font-style: italic; color: var(--ink-2); margin: 0 0 16px; font-size: 18px; }
.meta { font: 13px/1.6 "IBM Plex Sans", system-ui, sans-serif; color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px 18px; }
.meta a { color: var(--accent-ink); text-decoration: none; } .meta a:hover { text-decoration: underline; }
.tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 26px auto 34px; max-width: 880px; }
@media (max-width: 720px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 440px) { .tiles { grid-template-columns: 1fr; } }
.tile { background: var(--tile); border-radius: 10px; padding: 14px 16px; }
.tile-label { font: 600 12.5px/1.3 "IBM Plex Sans", system-ui, sans-serif; letter-spacing: .01em; color: var(--muted); }
.tile-value { font: 600 26px/1.25 "IBM Plex Sans", system-ui, sans-serif; margin: 6px 0 4px; letter-spacing: -.01em; }
.tile-value.text { font-size: 20px; line-height: 1.3; padding-top: 3px; }
.tile-note { font: 12.5px/1.4 "IBM Plex Sans", system-ui, sans-serif; color: var(--ink-2); }
main > * { max-width: 760px; margin-left: auto; margin-right: auto; }
main h2 { font: 650 24px/1.25 "IBM Plex Sans", system-ui, sans-serif; letter-spacing: -.01em; margin: 44px auto 10px;
  padding-top: 18px; border-top: 1px solid var(--rule); text-wrap: balance; }
main h3 { font: 600 18.5px/1.3 "IBM Plex Sans", system-ui, sans-serif; margin: 30px auto 6px; text-wrap: balance; }
main p, main li { color: var(--ink); }
main p { margin-top: 0; margin-bottom: 14px; }
main strong { font-weight: 600; }
main a { color: var(--accent-ink); }
main code { font: 14px "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; background: var(--code-bg); padding: 1px 5px; border-radius: 4px; }
main pre { background: var(--code-bg); padding: 14px 16px; border-radius: 8px; overflow-x: auto; }
main pre code { background: none; padding: 0; font-size: 13.5px; }
.table-wrap { max-width: 860px; margin: 8px auto 20px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font: 14.5px/1.45 "IBM Plex Sans", system-ui, sans-serif; }
th, td { text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font-weight: 600; font-size: 13.5px; color: var(--ink-2); border-bottom: 1.5px solid var(--rule); }
td { font-variant-numeric: tabular-nums; }
figure { max-width: 1000px !important; margin: 22px auto 30px; }
figure img { display: block; max-width: 100%; width: auto; height: auto; margin: 0 auto; border-radius: 6px; background: #ffffff; box-shadow: var(--shadow); }
figure a { display: block; }
figcaption { max-width: 760px; margin: 10px auto 0; font: 13.5px/1.55 "IBM Plex Sans", system-ui, sans-serif; color: var(--ink-2); }
footer { max-width: 760px; margin: 60px auto 0; padding-top: 16px; border-top: 1px solid var(--rule);
  font: 13px/1.6 "IBM Plex Sans", system-ui, sans-serif; color: var(--muted); }
footer a { color: var(--accent-ink); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }
@media (max-width: 640px) { body { font-size: 16px; } h1 { font-size: 30px; } .tile-value { font-size: 22px; } }
</style>
</head>
<body>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Research Lab · Deep dive · Clinical variant interpretation</div>
  <h1>__TITLE__</h1>
  <p class="subtitle">__SUBTITLE__</p>
  <div class="meta">
    <span>Draft · 2026-10-01 · revised after independent review</span>
    <a href="__BLOB__/plan.md">Preregistration</a>
    <a href="__BLOB__/deviations.md">Deviations log</a>
    <a href="__BLOB__/code">Code</a>
    <a href="../../index.html">All research leads</a>
  </div>
</header>
__TILES__
<main>
__BODY__
</main>
<footer>Produced by an AI-agent research workflow (scouting, preregistration, pipeline, calibration, independent review) on one
A100 machine. Data: GWOSC / Zenodo public releases. Every departure from the preregistration is recorded in the
<a href="__BLOB__/deviations.md">deviations log</a>.</footer>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
