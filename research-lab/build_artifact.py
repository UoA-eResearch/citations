#!/usr/bin/env python
"""Derive the claude.ai artifact copy of the Golden Quadrant explorer from index.html (the GitHub Pages version), so the
two stay in sync. The artifact service wraps the page in its own <!doctype>/<head>/<body> skeleton, so the document-level
tags are stripped; everything else (title, styles, embedded lead data, script) is kept unchanged. Report links resolve to
GitHub Pages at runtime (see index.html).
Usage: build_artifact.py OUT.html   (then publish OUT.html to https://claude.ai/artifact/FL86H7RkNAMkd4CbKserUx)
"""
import re
import sys
from pathlib import Path

src = (Path(__file__).resolve().parent / "index.html").read_text()
s = re.sub(r"<!doctype html>\s*", "", src, flags=re.I)
s = re.sub(r"</?html[^>]*>\s*", "", s)
s = re.sub(r"</?head>\s*", "", s)
s = re.sub(r"</?body>\s*", "", s)
drop = ('<meta charset=', '<meta name="viewport"', '<meta name="description"', '<link rel="icon"')
s = "\n".join(line for line in s.split("\n") if not line.lstrip().startswith(drop))
title = re.search(r"<title>.*?</title>\s*", s).group(0)
s = title + s.replace(title, "", 1)
Path(sys.argv[1]).write_text(s)
print("wrote", sys.argv[1], len(s), "bytes")
