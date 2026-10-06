"""Split 2019-2021 cabinet-department, non-templated documents into human-reference (60%), generation (20%) and
validation (20%) pools by document (seed 20261006), and draw the generation sample (up to 4,000 non-procedural
paragraphs, 40-400 words). Writes data/pools/*.parquet. Uses no text from 2022 or later."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]


def main():
    p = pd.read_parquet(RUN / "data" / "paragraphs_raw.parquet")
    p = p[(p.publication_date < "2022-01-01") & (p.group != "excluded") & (~p.templated)]
    docs = np.array(sorted(p.document_number.unique()))
    rng = np.random.default_rng(20261006)
    rng.shuffle(docs)
    n = len(docs)
    pools = {"human": docs[: int(0.6 * n)], "generation": docs[int(0.6 * n): int(0.8 * n)], "validation": docs[int(0.8 * n):]}
    out = RUN / "data" / "pools"
    out.mkdir(parents=True, exist_ok=True)
    for k, v in pools.items():
        p[p.document_number.isin(v)].to_parquet(out / f"{k}.parquet")
    g = p[p.document_number.isin(pools["generation"]) & ~p.procedural & p.n_words.between(40, 400)]
    g.sample(min(4000, len(g)), random_state=20261006).to_parquet(out / "generation_pool_sample.parquet")
    print({k: len(v) for k, v in pools.items()}, "| generation sample:", min(4000, len(g)))


if __name__ == "__main__":
    main()
