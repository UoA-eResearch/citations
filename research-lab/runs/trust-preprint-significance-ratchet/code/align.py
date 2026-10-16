"""Align statistics between a preprint and its published version, and classify each pair.

  1. tuples: same test, same df, |stat difference| <= 1% of the larger -> aligned ("exact").
  2. the rest: sentence similarity. Sentences are compared by TF-IDF cosine with every number masked (so a changed
     p-value does not reduce similarity), within the same section group (abstract / results+tables+figures / other).
     Pairs are matched one-to-one, best first, if cosine >= SIM_MIN; several statistics in one sentence are paired by
     their order within it.
  3. unmatched preprint statistics are "dropped", unmatched published ones "added".
Classification of an aligned pair whose significance is determined in both versions (extract.significance):
  unchanged, changed_not_crossing, crossing_up (non-significant -> significant), crossing_down (significant ->
  non-significant). Pairs with undetermined significance on either side are "undetermined".
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIM_MIN = 0.6
GROUP = {"abstract": "abstract", "result": "results", "table": "results", "figure": "results"}


def mask(s):
    return re.sub(r"\d+(?:\.\d+)?", " NUM ", s or "")


def group(sec):
    return GROUP.get(sec, "other")


def classify(a, b):
    if a["sig"] is None or b["sig"] is None:
        return "undetermined"
    if a["sig"] == b["sig"]:
        same = abs((a["p"] or 0) - (b["p"] or 0)) <= 1e-12 and a["cmp"] == b["cmp"]
        return "unchanged" if same else "changed_not_crossing"
    return "crossing_up" if (not a["sig"] and b["sig"]) else "crossing_down"


def align(pre, pub):
    pairs, used_a, used_b = [], set(), set()
    for i, a in enumerate(pre):
        if a["kind"] != "tuple":
            continue
        for j, b in enumerate(pub):
            if j in used_b or b["kind"] != "tuple" or a["test"] != b["test"] or a["df"] != b["df"]:
                continue
            if abs(a["stat"] - b["stat"]) <= 0.01 * max(abs(a["stat"]), abs(b["stat"]), 1e-9):
                pairs.append((i, j, "exact", 1.0)); used_a.add(i); used_b.add(j); break
    ra = [i for i in range(len(pre)) if i not in used_a]
    rb = [j for j in range(len(pub)) if j not in used_b]
    if ra and rb:
        docs = [mask(pre[i]["sentence"]) for i in ra] + [mask(pub[j]["sentence"]) for j in rb]
        try:
            X = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform(docs)
            S = cosine_similarity(X[:len(ra)], X[len(ra):])
        except ValueError:
            S = None
        if S is not None:
            cand = []
            for x, i in enumerate(ra):
                for y, j in enumerate(rb):
                    if group(pre[i]["section"]) != group(pub[j]["section"]) or S[x, y] < SIM_MIN:
                        continue
                    # within-sentence order as a tie-breaker: prefer the same rank among the sentence's statistics
                    cand.append((round(float(S[x, y]), 6), -abs(rank(pre, i) - rank(pub, j)), i, j))
            for s, _, i, j in sorted(cand, reverse=True):
                if i in used_a or j in used_b:
                    continue
                pairs.append((i, j, "similar", s)); used_a.add(i); used_b.add(j)
    out = [dict(pre=pre[i], pub=pub[j], how=how, sim=s, cls=classify(pre[i], pub[j])) for i, j, how, s in pairs]
    dropped = [pre[i] for i in range(len(pre)) if i not in used_a]
    added = [pub[j] for j in range(len(pub)) if j not in used_b]
    return out, dropped, added


def rank(stats, k):
    s = stats[k]["sentence"]
    same = [i for i, x in enumerate(stats) if x["sentence"] == s]
    return same.index(k)
