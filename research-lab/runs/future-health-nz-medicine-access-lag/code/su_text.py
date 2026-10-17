"""Text of every Schedule Update PDF (for the independent T3 cross-check in validation): data/su_text/<file>.txt."""
import sys
from pathlib import Path

import pymupdf

RUN = Path(__file__).resolve().parents[1]


def main():
    out = RUN / "data" / "su_text"; out.mkdir(exist_ok=True)
    for f in sorted((RUN / "data" / "raw" / "pharmac" / "su").glob("*.pdf")):
        t = out / (f.stem + ".txt")
        if not t.exists():
            t.write_text("\n".join(p.get_text() for p in pymupdf.open(f)))
    print("su text done")


if __name__ == "__main__":
    sys.exit(main())
