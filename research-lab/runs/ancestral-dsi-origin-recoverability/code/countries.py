"""Classify a BioSample country field (plan section 1).

usable       the country part (before the first colon) is a value of the INSDC geo_loc_name vocabulary (280 entries:
             countries, territories, oceans and seas; insdc_geo_loc_names.txt, fetched 2026-10-22), exactly or through
             a short fixed list of common variants, case-insensitive
placeholder  the whole value is an INSDC missing-value term (with or without a qualifier) or a common null string
malformed    present but neither
absent       no country attribute
"""
import re
import unicodedata
from pathlib import Path

VOCAB = [l.strip() for l in open(Path(__file__).with_name("insdc_geo_loc_names.txt")) if l.strip()]
CANON = {}                                   # filled after norm() is defined
VARIANTS = {"united states": "USA", "united states of america": "USA", "us": "USA", "u.s.a.": "USA",
            "u.s.": "USA", "uk": "United Kingdom", "great britain": "United Kingdom", "england": "United Kingdom",
            "scotland": "United Kingdom", "wales": "United Kingdom", "korea": "South Korea",
            "republic of korea": "South Korea", "korea, republic of": "South Korea", "russian federation": "Russia",
            "people's republic of china": "China", "pr china": "China", "p.r. china": "China",
            "viet nam": "Viet Nam", "vietnam": "Viet Nam", "czechia": "Czechia", "czech republic": "Czechia",
            "the netherlands": "Netherlands", "holland": "Netherlands", "iran, islamic republic of": "Iran",
            "turkiye": "Turkey", "türkiye": "Turkey", "ivory coast": "Cote d'Ivoire",
            "côte d'ivoire": "Cote d'Ivoire", "brasil": "Brazil", "méxico": "Mexico"}
NULLS = {"missing", "not applicable", "not collected", "not provided", "restricted access", "unknown", "na",
         "n/a", "n.a.", "none", "null", "-", "--", "?", "not determined", "not known", "not available", "unspecified",
         "other", "nd", "n.d.", "not reported", "no data", "undetermined", "not specified", "unavailable"}
QUALIFIED = re.compile(r"^(missing|not applicable|not collected|not provided|restricted access)\s*:\s*.+$", re.I)


def norm(s):
    """Lower case, collapsed spaces, straight apostrophes, accents removed (D4: the vocabulary file has a curly
    apostrophe in "Cote d'Ivoire", so a straight one, or "Côte", had been classed malformed)."""
    s = unicodedata.normalize("NFKD", (s or "").replace("\u2019", "'").replace("\u2018", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.strip().strip(".").lower())


CANON.update({norm(v): v for v in VOCAB})


def resolve(part):
    p = norm(part)
    if p in CANON:
        return CANON[p]
    if p in VARIANTS and norm(VARIANTS[p]) in CANON:
        return CANON[norm(VARIANTS[p])]
    return None


def classify(raw):
    """-> (class, resolved vocabulary value or None)"""
    if raw is None:
        return "absent", None
    v = norm(raw)
    if not v:
        return "absent", None
    if v in NULLS or QUALIFIED.match(v):
        return "placeholder", None
    r = resolve(raw.split(":", 1)[0])
    return ("usable", r) if r else ("malformed", None)


if __name__ == "__main__":
    for t in ["USA: California", "missing", "missing: lab stock", "not collected", "Viet Nam:Hanoi",
              "United States", "Pacific Ocean", "somewhere", None, "", "Korea", "China: Yunnan, Kunming"]:
        print(repr(t), classify(t))
