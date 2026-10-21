"""Bluebook-style abbreviations in cited case names, and a tolerant token match (D6, tuned on the pilots only).

The in-window pilot showed most remaining candidates were real cases whose citations abbreviate the parties the
way the Bluebook prescribes ("Mo. Pac. R.R. v. R.R. Comm'n of Tex.") while the corpus spells them out ("Missouri
Pacific Railroad v. Railroad Commission of Texas"), or misspell them ("Hotzclaw" for Holtzclaw). A cited token
matches a corpus token if they are equal, if the table below expands one to the other, if the cited token (four
letters or more) is a prefix of the corpus token, or if both have at least five letters and are near-identical
(rapidfuzz ratio >= 85). Every rule makes the screen more willing to say "this case exists", never less, so the
phantom count stays a lower bound.

Tokens are those of namenorm.norm_name, so "Comm'n" arrives as "comm" + "n" and "Gov't" as "gov" + "t".
"""
# abbreviation (as normalised) -> full words it may stand for
ABBREV = {
    "pac": ["pacific"], "tex": ["texas"], "rr": ["railroad"], "ry": ["railway"], "cnty": ["county"],
    "cty": ["county", "city"], "ctr": ["center", "centre"], "ctrs": ["centers"], "envtl": ["environmental"],
    "bd": ["board"], "emps": ["employees"], "emp": ["employees", "employee", "employment"],
    "elecs": ["electronics"], "natl": ["national"], "nat": ["national", "natural"], "mfg": ["manufacturing"],
    "prods": ["products"], "servs": ["services"], "serv": ["service", "services"], "mgmt": ["management"],
    "govt": ["government"], "assocs": ["associates"], "bros": ["brothers"], "cmty": ["community"],
    "cmtys": ["communities"], "cal": ["california"], "fla": ["florida"], "ill": ["illinois"], "mich": ["michigan"],
    "wis": ["wisconsin"], "minn": ["minnesota"], "penn": ["pennsylvania"], "pa": ["pennsylvania"],
    "mass": ["massachusetts"], "conn": ["connecticut"], "md": ["maryland"], "va": ["virginia"],
    "wash": ["washington"], "ariz": ["arizona"], "colo": ["colorado"], "okla": ["oklahoma"], "ga": ["georgia"],
    "ala": ["alabama"], "ky": ["kentucky"], "tenn": ["tennessee"], "ind": ["indiana"], "nev": ["nevada"],
    "neb": ["nebraska"], "kan": ["kansas"], "ark": ["arkansas"], "miss": ["mississippi"], "la": ["louisiana"],
    "ny": ["new york"], "nj": ["new jersey"], "sf": ["san francisco"], "dc": ["district of columbia"],
    "us": ["united states"], "usa": ["united states", "america"], "am": ["american", "america"],
    "fed": ["federal", "federation"], "int": ["international"], "intl": ["international"],
    "ass": ["association"], "assn": ["association"], "commn": ["commission"], "comm": ["commission", "committee"],
    "commr": ["commissioner"], "commrs": ["commissioners"], "dept": ["department"], "dep": ["department"],
    "sec": ["securities", "secretary", "security"], "secy": ["secretary"], "litig": ["litigation"],
    "corp": ["corporation"], "co": ["company"], "inc": ["incorporated"], "ltd": ["limited"], "ins": ["insurance"],
    "mut": ["mutual"], "cas": ["casualty"], "sur": ["surety"], "fin": ["financial", "finance"],
    "gen": ["general"], "elec": ["electric", "electrical"], "exp": ["export", "express", "exploration"],
    "imp": ["import"], "lab": ["labor", "laboratories"], "labs": ["laboratories"], "hosp": ["hospital"],
    "hous": ["housing"], "urb": ["urban"], "dev": ["development"], "educ": ["education"], "sch": ["school"],
    "schs": ["schools"], "dist": ["district"], "univ": ["university"], "inst": ["institute", "institution"],
    "enter": ["enterprise", "enterprises"], "enters": ["enterprises"], "tr": ["trust", "trustees", "trustee"],
    "transp": ["transportation"], "tel": ["telephone"], "telecomm": ["telecommunications"],
    "tech": ["technology", "technologies"], "sys": ["systems", "system"], "info": ["information"],
    "invs": ["investments"], "inv": ["investment"], "prop": ["property"], "props": ["properties"],
    "res": ["resources", "research"], "admin": ["administration"], "adm": ["administration"],
    "agric": ["agriculture", "agricultural"], "auth": ["authority"], "comp": ["compensation"],
    "constr": ["construction"], "corr": ["corrections", "correctional"], "def": ["defense"],
    "dir": ["director"], "div": ["division"], "econ": ["economic"], "equal": ["equality"], "equip": ["equipment"],
    "exch": ["exchange"], "fid": ["fidelity"], "grp": ["group"], "guar": ["guaranty"], "hum": ["human"],
    "indus": ["industries", "industrial"], "inds": ["industries"], "mach": ["machine", "machinery"],
    "med": ["medical"], "mktg": ["marketing"], "mun": ["municipal"], "pharm": ["pharmaceutical"],
    "pharms": ["pharmaceuticals"], "pub": ["public"], "regl": ["regional"], "reg": ["regional"],
    "ret": ["retirement"], "sav": ["savings"], "soc": ["social", "society"], "st": ["state", "saint", "street"],
    "sw": ["southwestern"], "ne": ["northeastern"], "nw": ["northwestern"], "se": ["southeastern"],
    "so": ["southern"], "n": ["north", "northern"], "s": ["south", "southern"], "w": ["west", "western"],
    "e": ["east", "eastern"], "twp": ["township"], "util": ["utility", "utilities"], "vill": ["village"],
    "bldg": ["building"], "bros.": ["brothers"], "chem": ["chemical"], "contr": ["contractors"],
    "distrib": ["distribution", "distributors"], "entm": ["entertainment"], "entmt": ["entertainment"],
    "gov": ["government", "governor"], "hldgs": ["holdings"], "inv.": ["investment"], "ltd.": ["limited"],
    "metro": ["metropolitan"], "prof": ["professional"], "rehab": ["rehabilitation"], "sci": ["science"],
}

MIN_PREFIX = 4
FUZZ_MIN_LEN = 5
FUZZ_MIN = 85


def expand(norm):
    """All the corpus words a normalised cited name's tokens may stand for, plus the tokens themselves."""
    out = set()
    for t in norm.split():
        out.add(t)
        for full in ABBREV.get(t, []):
            out.update(full.split())
    return out


def token_match(fuzz, t, u):
    if t == u or u in ABBREV.get(t, ()) or t in ABBREV.get(u, ()):
        return True
    if len(t) >= MIN_PREFIX and len(u) > len(t) and u.startswith(t):
        return True
    return len(t) >= FUZZ_MIN_LEN and len(u) >= FUZZ_MIN_LEN and fuzz.ratio(t, u) >= FUZZ_MIN


# expansions too generic to identify a case on their own; an abbreviation standing only for these is not used
GENERIC = {"company", "corporation", "incorporated", "limited", "united", "states", "state", "america", "american",
           "north", "south", "east", "west", "northern", "southern", "eastern", "western", "saint", "street",
           "department", "government", "people", "city", "county", "new", "york", "district", "columbia"}


def cited_tokens(norm, distinctive_tokens, dropped):
    """The cited tokens the consistency test may rely on: the distinctive ones, plus abbreviations whose expansion
    is neither generic nor too common to narrow a search (the index's own `dropped` set)."""
    out = set(distinctive_tokens)
    for t in norm.split():
        full = [w for f in ABBREV.get(t, []) for w in f.split()]
        if full and any(w not in GENERIC and w not in dropped for w in full):
            out.add(t)
    return out


def shares_token(fuzz, cited_tokens, corpus_name):
    """Does any of the cited tokens match any token of the corpus name under the tolerant rule?"""
    words = [w for w in corpus_name.split() if len(w) >= 3]
    for t in cited_tokens:
        full = ABBREV.get(t)
        if full and any(f in words for fl in full for f in fl.split() if len(f) >= 4 and f not in GENERIC):
            return True
        if any(token_match(fuzz, t, u) for u in words):
            return True
    return False


def expanded_name(norm):
    """The cited name with each abbreviation replaced by its first expansion (for the whole-name fuzzy search)."""
    return " ".join(ABBREV[t][0] if t in ABBREV else t for t in norm.split())
