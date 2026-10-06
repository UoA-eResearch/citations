"""EXPLORATORY (written after unsealing; not preregistered): which estimator-vocabulary words drive the 2026 rise.
For each vocabulary word: sentence-occurrence rate in 2024-25 and Feb-Sep 2026 non-procedural sentences, by group,
and its estimator weight w = logit p_A - logit p_H (positive = LLM-leaning). Contribution = change in rate x w, the
first-order change in the mean log-likelihood ratio d_s. Also: alpha recomputed with deregulatory-title documents
removed. Writes results/tables/explore_word_contributions.csv and explore_no_dereg.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import DEREG, load_paragraphs  # noqa: E402
from mle import alpha_mle, occurrence, sentences  # noqa: E402
from validate import build_estimator  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def main():
    est, info, _ = build_estimator(n_cal=10)
    p = load_paragraphs()
    p = p[~p.procedural]
    per = np.where((p.publication_date >= "2024-01-01") & (p.publication_date <= "2025-12-31"), "pre",
                   np.where((p.publication_date >= "2026-02-01") & (p.publication_date <= "2026-09-30"), "post", ""))
    p = p.assign(period=per)
    p = p[p.period != ""]
    rows, out = [], {}
    for (g, per_), d in p.groupby(["group", "period"]):
        sents = [s for t in d.text for s in sentences(t)]
        X = occurrence(sents, est.index)
        rate = np.asarray(X.mean(0)).ravel()
        for w, r in zip(est.vocab, rate):
            rows.append(dict(group=g, period=per_, word=w, rate=r))
        dd = est.d(sents)
        out[f"{g}_{per_}_alpha_cal"] = float(est.cal(alpha_mle(dd)))
        nd = d[~d.title.fillna("").str.contains(DEREG)]
        out[f"{g}_{per_}_alpha_cal_no_dereg"] = float(est.cal(alpha_mle(est.d([s for t in nd.text for s in sentences(t)]))))
        out[f"{g}_{per_}_dereg_doc_share"] = float(d.drop_duplicates("document_number").title.fillna("").str.contains(DEREG).mean())
    r = pd.DataFrame(rows).pivot_table(index=["group", "word"], columns="period", values="rate").reset_index()
    r["w"] = r.word.map(dict(zip(est.vocab, est.w)))
    r["contribution"] = (r["post"] - r["pre"]) * r["w"]
    r.sort_values("contribution", ascending=False).to_csv(TAB / "explore_word_contributions.csv", index=False)
    json.dump(out, open(TAB / "explore_no_dereg.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    for g, d in r.groupby("group"):
        d = d.sort_values("contribution", ascending=False)
        print(g, "top +:", [f"{x.word}({x.pre:.3f}->{x.post:.3f}, w={x.w:.2f})" for x in d.head(20).itertuples()])
        print(g, "share of positive contribution from top 20:", round(d.head(20).contribution.sum() / d[d.contribution > 0].contribution.sum(), 3))


if __name__ == "__main__":
    main()
