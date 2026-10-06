"""Distributional MLE of the LLM-modified sentence fraction (plan section 3; Liang et al. 2024/2025).
Each sentence is a Bernoulli occurrence vector over an adjective/adverb vocabulary. With p_H, p_A estimated from the
human and LLM references, each sentence's log-likelihood ratio d = log P_A(s) - log P_H(s) is all that is needed:
alpha maximises sum_s log(1 - alpha + alpha * exp(d_s)). Bootstrap resamples documents."""
import re

import numpy as np
from nltk.corpus import wordnet as wn
from nltk.tokenize.punkt import PunktParameters, PunktSentenceTokenizer
from scipy import sparse
from scipy.optimize import minimize_scalar

WORD = re.compile(r"[a-z]+(?:-[a-z]+)?")


def adj_adv_words():
    """Words whose most frequent WordNet sense is an adjective (a/s) or adverb (r)."""
    out = set()
    for pos in ("a", "s", "r"):
        for syn in wn.all_synsets(pos):
            for lem in syn.lemmas():
                w = lem.name().lower()
                if "_" in w:
                    continue
                syns = wn.synsets(w)
                if syns and syns[0].pos() in ("a", "s", "r"):
                    out.add(w)
    return out


_PP = PunktParameters()
_PP.abbrev_types = set("u.s.c u.s c.f.r cfr e.g i.e no nos sec secs fed reg pub l stat et al etc v vs jan feb mar apr jun jul aug sep sept oct nov dec inc corp co mr ms dr fig app supp ed p pp para paras art ch vol ann gov dept admin assn n.w s.w n.e s.e d.c a.m p.m approx est".split())
_TOK = PunktSentenceTokenizer(_PP)


def sentences(text):
    return [s for s in _TOK.tokenize(text) if len(s.split()) >= 5]


NORM = str.maketrans({"\u2010": "-", "\u2011": "-", "\u00a0": " ", "\u202f": " "})  # D4: Unicode hyphens and no-break spaces


def tokens(s):
    return set(WORD.findall(s.translate(NORM).lower()))


def build_vocab(human_sents, llm_sents, candidates, min_h=50, min_a=20):
    from collections import Counter
    ch, ca = Counter(), Counter()
    for s in human_sents:
        ch.update(tokens(s) & candidates)
    for s in llm_sents:
        ca.update(tokens(s) & candidates)
    vocab = sorted(w for w in candidates if ch[w] >= min_h and ca[w] >= min_a)
    return vocab, ch, ca


def occurrence(sents, index):
    rows, cols = [], []
    for i, s in enumerate(sents):
        for w in tokens(s):
            j = index.get(w)
            if j is not None:
                rows.append(i)
                cols.append(j)
    return sparse.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(sents), len(index)))


class Estimator:
    """paired=(source_sents, rewrite_sents) (D5): p_A(w) = p_H(w) * r(w), where r(w) is the ratio of w's sentence
    occurrence rate in the LLM outputs to that in the source paragraphs they were generated from. The LLM reference
    then carries only the shift the generators introduce, transferred onto the human reference's topic mix, instead of
    the topics of the few documents that were rewritten (which made those documents' own human text score 11%)."""

    def __init__(self, human_sents, llm_sents, candidates, min_h=50, min_a=20, paired=None):
        self.vocab, _, _ = build_vocab(human_sents, llm_sents, candidates, min_h, min_a)
        self.index = {w: i for i, w in enumerate(self.vocab)}
        Xh, Xa = occurrence(human_sents, self.index), occurrence(llm_sents, self.index)
        ph = (np.asarray(Xh.sum(0)).ravel() + 0.5) / (Xh.shape[0] + 1.0)
        pa = (np.asarray(Xa.sum(0)).ravel() + 0.5) / (Xa.shape[0] + 1.0)
        if paired is not None:
            Xs, Xr = occurrence(paired[0], self.index), occurrence(paired[1], self.index)
            ps = (np.asarray(Xs.sum(0)).ravel() + 0.5) / (Xs.shape[0] + 1.0)
            pr = (np.asarray(Xr.sum(0)).ravel() + 0.5) / (Xr.shape[0] + 1.0)
            pa = np.clip(ph * pr / ps, 1e-6, 0.999)
        # log P(s|A) - log P(s|H) = sum_w x_w [logit pa - logit ph] + sum_w [log(1-pa) - log(1-ph)]
        self.w = (np.log(pa) - np.log1p(-pa)) - (np.log(ph) - np.log1p(-ph))
        self.c = float(np.sum(np.log1p(-pa) - np.log1p(-ph)))

    def d(self, sents):
        return occurrence(sents, self.index) @ self.w + self.c


def alpha_mle(d):
    d = np.asarray(d, dtype=float)
    if len(d) == 0:
        return np.nan
    e = np.exp(np.clip(d, -50, 50))

    def nll(a):
        return -np.sum(np.log(1 - a + a * e))
    r = minimize_scalar(nll, bounds=(0.0, 1.0), method="bounded", options={"xatol": 1e-6})
    return float(r.x)


def bootstrap_alpha(d_by_doc, B=1000, rng=None):
    """d_by_doc: list of arrays (one per document). Returns the alpha MLE and its bootstrap draws."""
    rng = rng or np.random.default_rng(0)
    full = alpha_mle(np.concatenate(d_by_doc))
    n = len(d_by_doc)
    draws = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n)
        draws[b] = alpha_mle(np.concatenate([d_by_doc[i] for i in idx]))
    return full, draws
