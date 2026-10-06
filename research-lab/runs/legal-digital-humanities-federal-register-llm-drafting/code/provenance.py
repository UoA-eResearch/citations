"""Provenance for two descriptive numbers in report.md (confirmation-pass item N1): the share of documents whose own
raw alpha exceeds 0.25, by group and period, and the number of paragraphs containing a curly quote (U+201C or U+201D)
or an ordinary no-break space (U+00A0). Writes results/tables/provenance.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
from mle import alpha_mle  # noqa: E402
from validate import build_estimator  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    out = {}
    n = curly = nbsp = 0
    for f in ("paragraphs_raw.parquet", "paragraphs_sealed.parquet"):
        t = pd.read_parquet(RUN / "data" / f, columns=["text"]).text
        n += len(t); curly += int(t.str.contains("[“”]", regex=True).sum()); nbsp += int(t.str.contains(" ", regex=False).sum())
    out.update(paragraphs=n, paragraphs_with_curly_quote=curly, paragraphs_with_u00a0=nbsp)
    est, _, _ = build_estimator(n_cal=10)
    p, _ = A.dedup(A.load_paragraphs())
    meta = p.drop_duplicates("document_number").set_index("document_number")[["publication_date", "group"]]
    for g in ("DOT", "other_cabinet"):
        for per, (a, b) in (("pre", A_PRE), ("post", A_POST)):
            docs = meta[(meta.group == g) & (meta.publication_date >= a) & (meta.publication_date <= b)].index
            dm = A.doc_d(A.doc_sents(p[p.document_number.isin(docs)]), est)
            r = np.array([alpha_mle(v) for v in dm.values()])
            out[f"{g}_{per}_share_docs_raw_alpha_gt_0.25"] = float((r > 0.25).mean())
            out[f"{g}_{per}_n_docs"] = int(len(r))
    json.dump(out, open(RUN / "results" / "tables" / "provenance.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


A_PRE, A_POST = ("2024-01-01", "2025-12-31"), ("2026-02-01", "2026-09-30")

if __name__ == "__main__":
    main()
