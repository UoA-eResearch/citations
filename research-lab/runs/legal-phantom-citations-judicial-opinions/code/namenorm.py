"""One shared normalisation for case names, used by both the index builder and every lookup.

Keeping this in one place matters: an earlier version had the builder and the screen carrying different stopword
lists, so a query token the builder had deliberately omitted ("board") came back from the index as "no case name
contains this", and *Brown v. Board of Education* was reported as a nonexistent case. A token missing from the
index because it was never indexed is not evidence of anything.

The stoplist is therefore deliberately tiny -- only connectives that carry no identity. Words like "board",
"united", "states", "bank" or "county" are genuine parts of case names and stay indexed; tokens so common that
they cannot narrow a search are dropped by the MAX_POSTINGS cap in build_names.py instead, which records how
many it dropped.
"""
import re

WORD = re.compile(r"[a-z0-9]+")
STOP = {"v", "vs", "versus", "the", "of", "and", "a", "an", "et", "al", "in", "re", "ex", "rel", "no"}
MIN_TOKEN = 3


def norm_name(s):
    """Lowercase, strip punctuation, keep word order."""
    return " ".join(WORD.findall((s or "").lower()))


def tokens_of(norm):
    """The tokens that are indexed for a name, and the tokens a query may rely on. One definition for both."""
    return {w for w in norm.split() if len(w) >= MIN_TOKEN and w not in STOP}


def sides(norm):
    """Split a normalised name into (plaintiff, defendant) on the first standalone 'v'; None if it has no 'v'."""
    w = norm.split()
    if "v" in w:
        i = w.index("v")
        a, b = " ".join(w[:i]), " ".join(w[i + 1:])
        if a and b:
            return a, b
    return None


def party_score(fuzz, a, b):
    """How well a cited name `a` matches a corpus case name `b`, scored side by side.

    Scoring the whole name with token_set_ratio lets a shared defendant carry the match: "martinez v delta
    airlines inc" scores 90.9 against "doe v delta airlines inc" although the plaintiffs have nothing in common.
    So each side is scored separately and the weaker side decides, with both orderings tried since captions
    reverse on appeal.

    A corpus name with no 'v' cannot confirm two parties. token_set_ratio scores a single word as a perfect
    subset of any name containing it, so a cluster captioned just "petersen" scored 100 against "petersen v
    iran air" (D3). When the citation names two parties and the candidate names one, the candidate has to match
    each cited side, and the weaker decides. Only when the citation itself has no 'v' (In re, Ex parte) is the
    whole name compared.
    """
    sa, sb = sides(a), sides(b)
    if sa and sb:
        straight = min(fuzz.token_set_ratio(sa[0], sb[0]), fuzz.token_set_ratio(sa[1], sb[1]))
        crossed = min(fuzz.token_set_ratio(sa[0], sb[1]), fuzz.token_set_ratio(sa[1], sb[0]))
        return max(straight, crossed)
    if sa and not sb:
        return min(fuzz.token_set_ratio(sa[0], b), fuzz.token_set_ratio(sa[1], b))
    return fuzz.token_set_ratio(a, b)


# --- cleaning what eyecite extracts as party names (added after the pilot on out-of-window opinions, D3)
_BRACKET = re.compile(r"\[[^\]]*\]|\([^)]*\)")
_PAGEMARK = re.compile(r"\*\s*\d+")
_SIGNALS = {"see", "also", "cf", "accord", "but", "compare", "contra", "e", "g", "eg", "tide", "in", "the"}


def clean_party(s):
    """Strip what is not a name: bracketed years, star-page markers, digits, and leading citation signals."""
    s = _PAGEMARK.sub(" ", _BRACKET.sub(" ", s or ""))
    w = [t for t in WORD.findall(s.lower()) if not t.isdigit()]
    while w and w[0] in _SIGNALS:
        w = w[1:]
    return " ".join(w)


# Ohio-style docket tails that eyecite keeps in the defendant: "8th Dist. Cuyahoga No. 94458", "Franklin App. No."
_DOCKET_TAIL = re.compile(r"\b(\d+(st|nd|rd|th) dist\b|\w+ app no\b|case no\b).*$")


def clean_cited(plaintiff, defendant):
    p, d = clean_party(plaintiff), _DOCKET_TAIL.sub("", clean_party(defendant)).strip()
    return f"{p} v {d}" if p and d else (p or d)


def distinctive(norm, dropped):
    """Tokens that can identify a case: indexed, not too common, not numbers, at least four letters."""
    return {t for t in tokens_of(norm) - dropped if len(t) >= 4 and not t.isdigit()}
