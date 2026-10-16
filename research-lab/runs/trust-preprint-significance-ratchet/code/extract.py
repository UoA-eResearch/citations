"""Extract reported statistics from section text.

  p-values   "p = 0.03", "P<.001", "p-value = 1.2 x 10-5", "p ≤ 0.05", "(p = 3e-4)", "P value of 0.012"
  tuples     statcheck-style: t(df) = x, F(df1, df2) = x, r(df) = x, chi2/χ2(df[, N = n]) = x, z = x, each with its p
For each statistic: the section type, the sentence it sits in, its character offset, the comparator (=, <, >, <=, >=),
the numeric p, and the test tuple if any. A statistic's significance at 0.05:
  "=" -> sig if p < 0.05; "<"/"<=" -> sig if the bound is <= 0.05; ">"/">=" -> not sig if the bound is >= 0.05;
  anything else (e.g. "p = 0.05", "p < 0.1", "p > 0.01") -> undetermined, excluded from crossing counts.
"""
import re

NUM = r"(\d*\.\d+|\d+(?:\.\d+)?)\s*(?:(?:[x×*·]\s*10\s*(?:\^|\s)?\s*([-−–]?\s*\d+))|(?:e\s*([-−–]?\d+)))?"
CMP = r"(<=|>=|=<|=>|≤|≥|<|>|=|&lt;|&gt;)"
P_RE = re.compile(r"(?<![A-Za-z])[pP](?:\s*[-‐]?\s*values?)?\s*(?:of\s+)?" + CMP + r"\s*" + NUM, re.I)
P_OF_RE = re.compile(r"(?<![A-Za-z])[pP]\s*[-‐]?\s*values?\s+of\s+" + NUM, re.I)
TUPLE_RE = re.compile(
    r"(?P<test>\bt|\bF|\br|χ2|χ²|chi-?square[d]?|chi2|\bz)\s*"
    r"(?:\(\s*(?P<df>[\d.]+(?:\s*,\s*[\d.]+)?)(?:\s*,\s*N\s*=\s*\d+)?\s*\))?\s*=\s*(?P<stat>[-−–]?\d*\.?\d+)"
    r"\s*[,;]\s*" r"(?:[pP]\s*" + CMP + r"\s*" + NUM + r")", re.I)
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _num(m, base_i, exp_i1, exp_i2):
    v = float(m.group(base_i))
    e = m.group(exp_i1) or m.group(exp_i2)
    if e:
        v *= 10 ** int(re.sub(r"[−–\s]", lambda x: "-" if x.group() in "−–" else "", e))
    return v


def _cmp(c):
    return {"&lt;": "<", "&gt;": ">", "=<": "<=", "=>": ">=", "≤": "<=", "≥": ">="}.get(c, c)


def significance(cmp, p):
    if p is None or not (0 <= p <= 1):
        return None
    if cmp == "=":
        return None if abs(p - 0.05) < 1e-12 else p < 0.05
    if cmp in ("<", "<="):
        return True if p <= 0.05 else None
    if cmp in (">", ">="):
        return False if p >= 0.05 else None
    return None


def sentences(text):
    out, pos = [], 0
    for s in SENT.split(text):
        i = text.find(s, pos)
        out.append((i, s)); pos = i + len(s)
    return out


def extract(text, section="other"):
    stats = []
    for off, s in sentences(text or ""):
        seen = set()
        for m in TUPLE_RE.finditer(s):
            c = _cmp(m.group(4)); p = _num(m, 5, 6, 7)
            stats.append(dict(section=section, offset=off + m.start(), sentence=s, kind="tuple",
                              test=m.group("test").lower().replace("χ²", "χ2"), df=re.sub(r"\s", "", m.group("df") or ""),
                              stat=float(m.group("stat").replace("−", "-").replace("–", "-")), cmp=c, p=p,
                              sig=significance(c, p)))
            seen.add(m.end())
        for m in P_RE.finditer(s):
            if any(abs(m.end() - e) <= 1 for e in seen):
                continue                                # already captured as part of a tuple
            c = _cmp(m.group(1)); p = _num(m, 2, 3, 4)
            stats.append(dict(section=section, offset=off + m.start(), sentence=s, kind="p", test=None, df=None, stat=None,
                              cmp=c, p=p, sig=significance(c, p)))
        for m in P_OF_RE.finditer(s):
            p = _num(m, 1, 2, 3)
            stats.append(dict(section=section, offset=off + m.start(), sentence=s, kind="p", test=None, df=None, stat=None,
                              cmp="=", p=p, sig=significance("=", p)))
    return stats
