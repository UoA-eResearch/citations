"""Exploratory v2 extraction (deviations D3.2). Same tuple regex, significance rule and sentence splitter as
extract.py, with the repairs the blind validation called for:

  - text repaired with ftfy (mojibake such as "1.0Ã\\x9710â\\x88\\x925" -> "1.0×10−5", "Â±" -> "±");
  - a middle dot between digits is a decimal point ("p=0·76" -> "p=0.76");
  - a comma right after a p comparator's integer part is a decimal point ("p = 0,33" -> "p = 0.33");
  - "p" preceded by a word character or ² is not a p-value (η²p, ηp2, ω²p, pBonferroni is already excluded);
  - a mantissa followed by "×10" with no exponent ("p=1x10") is undetermined (p = None).
Each statistic also carries its rank within the sentence, the sentence's statistic count, and the matched text.
"""
import re

import ftfy

from extract import CMP, NUM, TUPLE_RE, _cmp, _num, sentences, significance

P_RE = re.compile(r"(?<![\w²³])[pP](?:\s*[-‐]?\s*values?)?\s*(?:of\s+)?" + CMP + r"\s*" + NUM, re.I)
P_OF_RE = re.compile(r"(?<![\w²³])[pP]\s*[-‐]?\s*values?\s+of\s+" + NUM, re.I)
MIDDOT = re.compile(r"(?<=\d)[·∙•](?=\d)")
PCOMMA = re.compile(r"((?<![\w²³])[pP](?:\s*[-‐]?\s*values?)?\s*(?:<=|>=|≤|≥|<|>|=)\s*\d+),(?=\d)")
LOST_EXP = re.compile(r"\s*[x×*]\s*10(?![\d.\s]*[-−–]?\d)")


def normalise(text):
    t = ftfy.fix_text(text or "")
    t = MIDDOT.sub(".", t)
    return PCOMMA.sub(r"\1.", t)


def extract(text, section="other"):
    stats = []
    for off, s in sentences(normalise(text)):
        found, seen = [], set()
        for m in TUPLE_RE.finditer(s):
            c = _cmp(m.group(4)); p = _num(m, 5, 6, 7)
            found.append(dict(section=section, offset=off + m.start(), pos=m.start(), raw=m.group(0), sentence=s,
                              kind="tuple", test=m.group("test").lower().replace("χ²", "χ2"),
                              df=re.sub(r"\s", "", m.group("df") or ""),
                              stat=float(m.group("stat").replace("−", "-").replace("–", "-")), cmp=c, p=p))
            seen.add(m.end())
        for m in P_RE.finditer(s):
            if any(abs(m.end() - e) <= 1 for e in seen):
                continue
            c = _cmp(m.group(1)); p = _num(m, 2, 3, 4)
            if not (m.group(3) or m.group(4)) and LOST_EXP.match(s, m.end()):
                p = None
            found.append(dict(section=section, offset=off + m.start(), pos=m.start(), raw=m.group(0), sentence=s,
                              kind="p", test=None, df=None, stat=None, cmp=c, p=p))
        for m in P_OF_RE.finditer(s):
            found.append(dict(section=section, offset=off + m.start(), pos=m.start(), raw=m.group(0), sentence=s,
                              kind="p", test=None, df=None, stat=None, cmp="=", p=_num(m, 1, 2, 3)))
        found.sort(key=lambda x: x["pos"])
        for k, x in enumerate(found):
            x.update(rank=k, n_in_sent=len(found), sig=significance(x["cmp"], x["p"]))
        stats += found
    return stats
