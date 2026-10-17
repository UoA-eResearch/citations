"""Local Contexts element detection (plan section 2), shared by the census and the crosswalk scorer."""
import json
import re
from pathlib import Path

V = json.load(open(Path(__file__).resolve().parents[1] / "results" / "tables" / "vocabulary.json"))
# D5: plural path forms too (RAiD's schema URI uses /labels/ and /notices/)
URI_RE = re.compile(r"localcontexts(?:hub)?\.org/(labels?|notices?|projects?)/([A-Za-z0-9\-]+)", re.I)
NOTICE_NAMES = {"tk-notice": [r"TK Notice", r"Traditional Knowledge Notice"], "bc-notice": [r"BC Notice", r"Biocultural Notice"],
                "attribution-incomplete": [r"Attribution Incomplete Notice"], "open-to-collaborate": [r"Open to Collaborate Notice"]}


def _label_pat(slug):
    kind, rest = slug.split("-", 1)
    words = r"[ \-_]+".join(re.escape(w) for w in rest.split("-"))
    full = {"tk": r"(?:TK|Traditional Knowledge)", "bc": r"(?:BC|Biocultural)"}[kind]
    return re.compile(full + r"[ \-_]+" + words + r"(?:[ \-_]+Label)?\b", re.I)


LABEL_RES = {s: _label_pat(s) for s in V["labels"]}
# D5: hyphen/underscore-tolerant, as the Label patterns already are ("BC-Notice")
NOTICE_RES = {s: re.compile(r"\b(?:" + "|".join(x.replace(" ", r"[ \-_]+") for x in p) + r")\b", re.I) for s, p in NOTICE_NAMES.items()}


def detect(text):
    """-> dict(uri_labels, uri_notices, hub_projects, name_labels, name_notices)."""
    t = text or ""
    out = dict(uri_labels=set(), uri_notices=set(), hub_projects=set(), name_labels=set(), name_notices=set())
    for kind, slug in URI_RE.findall(t):
        if re.search(r"(?:^|-)(?:labels|notices)$", slug, re.I):   # D5: category pages name no element
            continue
        k = kind.lower().rstrip("s") if kind.lower() != "projects" else "projects"
        if k == "label":
            out["uri_labels"].add(slug.lower())
        elif k == "notice":
            out["uri_notices"].add(slug.lower())
        else:
            out["hub_projects"].add(slug.lower())
    for s, r in LABEL_RES.items():
        if r.search(t):
            out["name_labels"].add(s)
    for s, r in NOTICE_RES.items():
        if r.search(t):
            out["name_notices"].add(s)
    return {k: sorted(v) for k, v in out.items()}


def any_element(d):
    return any(d[k] for k in d)
