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
    """How well two normalised case names match, scored side by side.

    Scoring the whole name with token_set_ratio lets a shared defendant carry the match: "martinez v delta
    airlines inc" scores 90.9 against "doe v delta airlines inc" although the plaintiffs have nothing in common.
    The plaintiff is usually the most identifying part of a caption, so each side is scored separately and the
    weaker side decides. Both orderings are tried, since captions reverse on appeal. Names without a 'v' (In re,
    Ex parte) fall back to the whole name.
    """
    sa, sb = sides(a), sides(b)
    if not (sa and sb):
        return fuzz.token_set_ratio(a, b)
    straight = min(fuzz.token_set_ratio(sa[0], sb[0]), fuzz.token_set_ratio(sa[1], sb[1]))
    crossed = min(fuzz.token_set_ratio(sa[0], sb[1]), fuzz.token_set_ratio(sa[1], sb[0]))
    return max(straight, crossed)
