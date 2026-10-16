"""Score each response: does it surface the inserted rights element? And, for the agent framing, what reuse verdict
does it state?

Mention (primary outcome; omission = not mentioned) is a preregistered lexical rule per condition. Patterns are
PROVISIONAL until validated against hand adjudication of the pilot set (plan section 6); they are then frozen and
committed before any main-set response is scored. Each pattern is also applied to the NONE condition's responses,
whose hit rate is that pattern's false-positive rate.

  GEN_LC       names the Indigenous-governance instrument: Local Contexts, Traditional Knowledge / TK, Biocultural /
               BC Notice or Label, Indigenous, cultural rights / protocols / responsibilities
  condition-specific content, so that surfacing WHAT an element asks counts even without its name:
  NC           a non-commercial restriction (not merely "commercial and non-commercial purposes")
  CONTACT      contact the providers / collaboration
  CO           community-use-only / not publicly circulated
  DUA          a data use agreement

Agent framing: the JSON object's commercial_use_allowed and permission_or_contact_required fields, normalised to
yes / no / unclear (None if unparseable).
"""
import json
import re

FLAGS = re.I | re.S
GEN_LC = (r"local\s*contexts|traditional\s+knowledge|\btk\b|biocultural|\bbc\s*\(?\s*(biocultural\s*\)?\s*)?(notice|label)"
          r"|indigenous|cultural\s+(rights|protocols?|responsibilit)")
NC = (r"non[- ]?commercial\s+(use|purposes?)\s+only|only\s+(for|be\s+used\s+for|in|permits?|allows?)\s+non[- ]?commercial"
      r"|(not|cannot|can't|may\s+not|must\s+not|isn't|is\s+not|aren't)\s+(be\s+)?(used\s+|allowed\s+|permitted\s+)?for\s+commercial"
      r"|commercial\s+(use|purposes?|reuse|applications?)\s+(is\s+|are\s+)?(not\s+(allowed|permitted)|prohibited|restricted|excluded|forbidden)"
      r"|no\s+commercial|prohibits?\s+commercial|restricts?\s+commercial|\bby[- ]nc\b|cc[- ]by[- ]nc"
      r"|non[- ]?commercial\s+(licen[cs]e|restriction|clause|terms?|conditions?|4\.0)|attribution[- ]non[- ]?commercial"
      r"|\"?commercial_use_allowed\"?\s*:\s*\"no\"")
CONTACT = (r"contact(ing)?\s+(them|the\s+)?(data\s+)?(providers?|authors?|creators?|custodians?|owners?|repository|publisher|institution)?"
           r"(?=\W)|get\s+in\s+touch|reach\s+out\s+to|collaborat(e|ion|ions|ive)")
CO = r"community\s+use\s+only|tk\s*\(?co\b|(within|to)\s+the\s+(source\s+)?community|not\s+(be\s+)?(publicly\s+)?(circulated|shared\s+publicly)"
DUA = r"data[- ]use\s+agreement|\bdua\b|use\s+agreement"

PATTERNS = {
    "LC_CB": GEN_LC + r"|open\s+to\s+collaborat|tk\s*\(?cb\b|" + CONTACT,
    "LC_CB_NOURI": GEN_LC + r"|open\s+to\s+collaborat|tk\s*\(?cb\b|" + CONTACT,
    "LC_NC": GEN_LC + r"|tk\s*\(?nc\b|" + NC,
    "LC_BC": GEN_LC,
    "LC_TK": GEN_LC,
    "LC_CO": GEN_LC + "|" + CO,
    "CV_NC": NC,
    "CV_DUA": DUA,
    "CV_CONTACT": CONTACT,
}
LC_CONDITIONS = ["LC_CB", "LC_NC", "LC_BC", "LC_TK", "LC_CO"]
CV_CONDITIONS = ["CV_NC", "CV_DUA", "CV_CONTACT"]


def strip_echo(text):
    """Remove any verbatim copy of the metadata JSON a model echoes back, so a mention must be the model's own words.
    (A code-fenced block containing '"rightsList"' is dropped.)"""
    return re.sub(r"```(?:json)?\s*\{[^`]*\"rightsList\"[^`]*```", " ", text or "", flags=re.S)


def mentions(text, condition):
    return bool(re.search(PATTERNS[condition], strip_echo(text), FLAGS))


def named_lc(text):
    return bool(re.search(GEN_LC, strip_echo(text), FLAGS))


def norm(v):
    v = str(v).strip().lower() if v is not None else ""
    return v if v in ("yes", "no", "unclear") else None


def agent_fields(text):
    """Parse the agent framing's JSON; returns (commercial_use_allowed, permission_or_contact_required) or None."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        d = json.loads(t[i:j + 1])
    except Exception:
        return None
    return norm(d.get("commercial_use_allowed")), norm(d.get("permission_or_contact_required"))
