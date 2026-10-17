import sys, re, pymupdf
for f in sys.argv[1:]:
    doc = pymupdf.open(f); out = f + ".txt"
    txt = "\n".join(f"<<page {i+1}>>\n" + p.get_text() for i, p in enumerate(doc))
    open(out, "w").write(txt); print(f, len(doc), "pages,", len(txt), "chars")
