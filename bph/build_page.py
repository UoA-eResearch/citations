"""Wrap app.html (the page body, as published to claude.ai artifacts) into a standalone
index.html for GitHub Pages: adds the doctype, charset and viewport, and moves the title,
font links and styles into <head>."""

from pathlib import Path

here = Path(__file__).parent
src = (here / "app.html").read_text()
cut = src.index("<header")
head, body = src[:cut], src[cut:]
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head.strip()}
</head>
<body>
{body.strip()}
</body>
</html>
"""
(here / "index.html").write_text(page)
print(f"wrote {here / 'index.html'} ({len(page) / 1000:.0f} kB)")
