"""Local re-checks and tags applied to every candidate work and award.

OpenAlex's title/abstract search finds candidates; these matchers decide. They work on folded text
(lower case, diacritics and ʻokina removed) and drop the known false friends:
  - "Asia-Pacific ..." / "Asian and Pacific Islander" (a generic or lumped category)
  - "Western Pacific Region" (the WHO region, mostly East Asia)
  - "Canada-France-Hawaii (Telescope)"
"""

import re
import unicodedata

# ---------------------------------------------------------------- text folding

_OKINA = dict.fromkeys(map(ord, "ʻʼ‘’'`´"), None)
_DASH = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")


def fold(s):
    s = str(s or "").translate(_OKINA).translate(_DASH)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower())


def abstract_text(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


# ---------------------------------------------------------------- places (P lens)
# code -> (label, regex on folded text, lat, lng). Regions have lat/lng None.
PLACES = {
    "AS": ("American Sāmoa", r"\bamerican samoa(?:n|ns)?\b", -14.28, -170.70),
    "WS": ("Sāmoa", r"(?<!american )\bsamoa(?:n|ns)?\b", -13.76, -172.10),
    "TO": ("Tonga", r"\btonga(?:n|ns)?\b", -21.18, -175.20),
    "FJ": ("Fiji", r"\bfiji(?:an|ans)?\b|\bi-?taukei\b", -17.71, 178.07),
    "CK": ("Cook Islands", r"\bcook islands?\b|\bkuki airani\b|\brarotonga(?:n)?\b|\baitutaki\b", -21.24, -159.78),
    "NU": ("Niue", r"\bniue(?:an|ans)?\b", -19.05, -169.87),
    "TK": ("Tokelau", r"\btokelau(?:an|ans)?\b", -9.20, -171.85),
    "TV": ("Tuvalu", r"\btuvalu(?:an|ans)?\b", -8.52, 179.20),
    "KI": ("Kiribati", r"\b(?:i-)?kiribati\b", 1.42, 173.03),
    "VU": ("Vanuatu", r"\b(?:ni-)?vanuatu\b", -15.38, 166.96),
    "SB": ("Solomon Islands", r"\bsolomon islands?\b", -9.43, 159.95),
    "PG": ("Papua New Guinea", r"\bpapua new guinea(?:n|ns)?\b|\bbougainville\b", -6.31, 143.96),
    "HI": ("Hawaiʻi", r"(?<!canada-france-)\bhawaii(?:an|ans)?\b", 20.80, -156.33),
    "MH": ("Marshall Islands", r"\bmarshall islands?\b|\bmarshallese\b", 7.13, 171.18),
    "PW": ("Palau", r"\bpalau(?:an|ans)?\b", 7.51, 134.58),
    "NR": ("Nauru", r"\bnauru(?:an|ans)?\b", -0.52, 166.93),
    "GU": ("Guam", r"\bguam\b|\bchamorros?\b|\bchamoru\b", 13.44, 144.79),
    "FM": ("Federated States of Micronesia", r"\bfederated states of micronesia\b", 6.92, 158.16),
    "NC": ("New Caledonia", r"\bnew caledonia(?:n|ns)?\b|\bkanaks?\b", -21.26, 165.62),
    "PF": ("French Polynesia", r"\bfrench polynesia(?:n|ns)?\b|\btahiti(?:an|ans)?\b", -17.65, -149.43),
    "RN": ("Rapa Nui", r"\brapa nui\b|\beaster island\b", -27.11, -109.35),
    "WF": ("Wallis and Futuna", r"\bwallis and futuna\b", -13.77, -177.16),
    "PN": ("Pitcairn", r"\bpitcairn\b", -25.07, -130.10),
    # regions and peoples, not single places
    "POLY": ("Polynesia (region)", r"\bpolynesia(?:n|ns)?\b", None, None),
    "MELA": ("Melanesia (region)", r"\bmelanesia(?:n|ns)?\b", None, None),
    "MICR": ("Micronesia (region)", r"(?<!federated states of )\bmicronesia(?:n|ns)?\b", None, None),
    "OCEA": ("Oceania (region)", r"\boceania\b", None, None),
    "PREG": ("Pacific Islands / region", r"\bpacific (?:islands?|island countries|island nations|island states|region|nations|countries)\b", None, None),
    # Pacific concepts and research methodologies: strong evidence of Pacific research.
    "PCON": ("Pacific concepts & methodologies", r"\btalanoa\b|\bteu le va\b|\btauhi va\b|\bva[- ]relational\b|"
             r"\brelational va\b|\bva[- ]centred\b|\bkakala\b|\bfonofale\b|\bfaafaletui\b|\btok stori\b|\btivaevae\b|"
             r"\bvanua\b|\bfonua\b", None, None),
    # Any other "Pacific ..." (Pacific peoples, communities, values, research, health, Pasifika, ...).
    "PPPL": ("Pacific peoples & communities", r"\bpasifika\b|\bpacific\b", None, None),
}
GENERIC = {"PPPL", "OCEA"}  # weak on their own: "Pacific" as an ethnic group, "Oceania" as a reporting region
REGIONS = {"POLY", "MELA", "MICR", "PREG"}  # regions: specific only when named more than once
_PLACE_RX = {k: re.compile(v[1]) for k, v in PLACES.items()}

# "Pacific" in these contexts is not Pacific research: generic or lumped regions, the WHO region,
# species names, a sequencing company, or ocean/climate phrases (those belong to the O lens).
_PAC_EXCLUDE_BEFORE = re.compile(r"(?:asia|asian|indo|trans|non)[\s\-/&,]*(?:and the |and |& )?$")
_PAC_EXCLUDE_AFTER = re.compile(
    r"^[\s\-]*(?:northwest|biosciences|oysters?|salmon|cod|herring|halibut|sardines?|saury|bluefin|white shrimp|"
    r"hake|mackerel|geoducks?|ocean|basin|plate|rim|coast|decadal|islands?|island countries|island nations|"
    r"island states|region)\b")
_OCEAN_BEFORE = re.compile(r"(?:south|southwest|south-west|southwestern|south-western|western|tropical|equatorial|"
                           r"north|northern|eastern|central|southern|abyssal|pan)[\s\-]$")
# A generic "Pacific" next to other population groups (incl. Māori): results reported for several groups.
_ETHNIC_LIST = re.compile(r"\basian\b|\beuropean\b|\bpakeha\b|\bethnic|\bmelaa\b|\bmiddle eastern\b|\bmaori\b")


def place_hits(text):
    """({code: count}, n_generic_in_ethnicity_list) for Pacific place/people mentions in folded text."""
    out, ethnic = {}, 0
    for code, rx in _PLACE_RX.items():
        n = 0
        for m in rx.finditer(text):
            before = text[max(0, m.start() - 16):m.start()]
            after = text[m.end():m.end() + 24]
            if code == "PREG" and (_PAC_EXCLUDE_BEFORE.search(before) or
                                   re.search(r"western $", before) and after.startswith(" region")):
                continue
            if code == "PPPL" and m.group(0) == "pacific":
                if _PAC_EXCLUDE_BEFORE.search(before) or _PAC_EXCLUDE_AFTER.search(after) or _OCEAN_BEFORE.search(before):
                    continue
                if _ETHNIC_LIST.search(text[max(0, m.start() - 60):m.end() + 60]):
                    ethnic += 1
            if code == "HI" and "canada-france-hawaii" in text[max(0, m.start() - 16):m.end()]:
                continue
            n += 1
        if n:
            out[code] = n
    return out, ethnic


# ---------------------------------------------------------------- O lens (ocean & climate)
_OCEAN = re.compile(
    r"\bpacific ocean\b|\b(?:south|southwest|south-west|southwestern|south-western|western|tropical|equatorial|"
    r"north|northern|eastern|central|southern|abyssal|pan)[ \-]pacific\b|\bpacific (?:basin|plate|rim|coast)\b|"
    r"\bmoana\b|\bel nino\b|\bla nina\b|"
    r"\benso\b|\bsouthern oscillation\b|\b(?:interdecadal|decadal) pacific oscillation\b|\bkermadecs?\b")


def ocean_hits(text):
    n = 0
    for m in _OCEAN.finditer(text):
        after = text[m.end():m.end() + 8]
        if m.group(0).startswith("western pacific") and after.startswith(" region"):
            continue  # the WHO Western Pacific Region
        n += 1
    return n


# ---------------------------------------------------------------- A lens (Aotearoa x Blue Pacific theme)
_A_PLACE = re.compile(r"\bnew zealand\b|\baotearoa\b|\bmaori\b|\bhauraki\b|\bwaitemata\b|\bchatham islands?\b|\btasman sea\b")
_A_THEME = re.compile(
    r"\boceans?\b|\boceanic\b|\bmarine\b|\bcoast(?:s|al|line|lines)?\b|\bseafloor\b|\bseabed\b|\bsea\b|\bseas\b|"
    r"\bestuar(?:y|ies|ine)\b|\bharbou?rs?\b|\bfisher(?:y|ies)\b|\bfishing\b|\baquaculture\b|\bmussels?\b|\bkelp\b|"
    r"\bseaweeds?\b|\breefs?\b|\bsea[- ]level\b|\btsunamis?\b|\bcyclones?\b|\bclimate change\b|\bclimate adaptation\b|"
    r"\bdroughts?\b|\bfloods?\b|\bflooding\b|\bearthquakes?\b|\bvolcan(?:o|oes|ic|ism)\b|\beruptions?\b|\berosion\b|"
    r"\bnatural hazards?\b|\bbiodiversity\b|\bblue economy\b|\bocean energy\b|\bwave energy\b|\btidal energy\b|"
    r"\boffshore wind\b|\bmatauranga\b|\bkaitiakitanga\b|\benvironmental justice\b|\bresource management\b|"
    r"\bfreshwater\b|\bwetlands?\b|\blandslides?\b|\bseismic\b|\bstorms?\b|\brainfall\b|\brivers?\b|\blakes?\b|"
    r"\bgroundwater\b|\bintertidal\b|\bdisasters?\b|\bfish(?:es)?\b")
# OpenAlex fields whose works count as environment / earth / biosphere research.
A_FIELDS = {"Environmental Science", "Earth and Planetary Sciences", "Agricultural and Biological Sciences"}


def aotearoa_theme(title, text, field):
    """A lens: an Aotearoa place anywhere, AND either an environment/earth/biology primary field or a
    Blue Pacific theme word in the TITLE (keeps health, education etc. that merely mention NZ out)."""
    return bool(_A_PLACE.search(text)) and (field in A_FIELDS or bool(_A_THEME.search(title)))


# ---------------------------------------------------------------- M lens (ocean, Earth & climate systems)
# Sub-theme -> (label, regex on folded text). A sub-theme counts when its terms are in the TITLE, or in the
# abstract/keywords of a work whose OpenAlex primary field fits it (M_FIELDS). "earthquake" etc. in health
# or psychology research (e.g. studies of earthquake survivors) never counts.
M_THEMES = {
    "eco": ("Marine & coastal ecosystems",
            r"\bmarine\b|\bplankton(?:ic)?\b|\bphytoplankton\b|\bzooplankton\b|\bwhales?\b|\bdolphins?\b|\bcetaceans?\b|"
            r"\bseabirds?\b|\bfisher(?:y|ies)\b|\baquaculture\b|\bkelp\b|\bseaweeds?\b|\bseagrass(?:es)?\b|\bmangroves?\b|"
            r"\bcorals?\b|\breefs?\b|\bestuar(?:y|ies|ine)\b|\bintertidal\b|\bsubtidal\b|\bhauraki gulf\b|\bshellfish\b|"
            r"\bsnapper\b|\bsharks?\b|\breef fish|\bfish (?:stocks?|populations?|communities)\b|\bkina\b|\bpaua\b"),
    "ocn": ("Ocean & climate processes",
            r"\boceans?\b|\boceanic\b|\boceanograph\w*|\bsea[- ]level\b|\bocean currents?\b|\bupwelling\b|"
            r"\bpal(?:a)?eoceanograph\w*|\bpal(?:a)?eoclimat\w*|\bocean acidification\b|\bmarine heatwaves?\b|"
            r"\bcoastal\b|\bshorelines?\b|\bsea surface temperatures?\b"),
    "geo": ("Seafloor, tectonics & hazards",
            r"\bseafloor\b|\bseabed\b|\bsea floor\b|\bsubmarine\b|\bcontinental (?:shelf|margin|slope)\b|\bcontourites?\b|"
            r"\bpockmarks?\b|\bsubduction\b|\bhikurangi\b|\bchatham rise\b|\bcampbell plateau\b|\bchallenger plateau\b|"
            r"\btsunamis?\b"),
    "ant": ("Antarctica & the Southern Ocean",
            r"\bantarctica\b|\bantarctic\b|\bsouthern ocean\b|\bross sea\b|\bsea ice\b|\bice shelf\b"),
    "gov": ("Ocean law, governance & blue economy",
            r"\blaw of the sea\b|\bunclos\b|\bmaritime (?:boundar\w*|security|zones?|law|domain)\b|\bdeep[- ]sea mining\b|"
            r"\bseabed mining\b|\bblue economy\b|\bocean governance\b|\bmarine protected areas?\b|\bmarine spatial planning\b|"
            r"\bexclusive economic zones?\b"),
}
_M_RX = {k: re.compile(v[1]) for k, v in M_THEMES.items()}
_SCI = {"Earth and Planetary Sciences", "Environmental Science", "Agricultural and Biological Sciences"}
M_FIELDS = {
    "eco": _SCI | {"Immunology and Microbiology", "Biochemistry, Genetics and Molecular Biology"},
    "ocn": _SCI | {"Physics and Astronomy"},
    "geo": _SCI | {"Engineering", "Social Sciences", "Physics and Astronomy"},
    "ant": None,   # any field
    "gov": {"Social Sciences", "Economics, Econometrics and Finance", "Business, Management and Accounting",
            "Arts and Humanities", "Environmental Science", "Decision Sciences"},
}
_M_NEVER = {"Medicine", "Psychology", "Nursing", "Health Professions", "Neuroscience", "Dentistry"}
# Earthquakes join "Seafloor, tectonics & hazards" as Earth science, environmental science or disaster studies.
# Earthquake engineering of buildings and infrastructure (a large UoA strength) is left out unless the work also
# concerns tsunami, subduction or the seafloor, so that structural engineering does not swamp the lens.
_QUAKE = re.compile(r"\bearthquakes?\b|\bseismic hazard|\bpaleoseismolog\w*|\bseismicity\b")
_QUAKE_FIELDS = {"Earth and Planetary Sciences", "Environmental Science", "Social Sciences"}


# Subfields that are marine by definition: one abstract mention is enough there; elsewhere an abstract-only
# match needs two or more mentions (a single "ocean" or "coastal" in passing is not marine research).
MARINE_SUBFIELDS = {"Oceanography", "Aquatic Science", "Ocean Engineering"}


def marine_themes(title, body, field, subfield=None):
    """Sub-themes of the M lens for a record (set of codes), from folded title and folded abstract+keywords."""
    out = set()
    for k, rx in _M_RX.items():
        if field in _M_NEVER and k in ("geo", "ocn"):
            continue          # e.g. mental health after earthquakes; coastal towns in health studies
        if rx.search(title):
            out.add(k)
        elif field is None or M_FIELDS[k] is None or field in M_FIELDS[k]:
            n = len(rx.findall(body))   # field None = unknown (e.g. most MBIE awards): the description decides
            if n >= 2 or (n == 1 and subfield in MARINE_SUBFIELDS):
                out.add(k)
    if "geo" not in out and field in _QUAKE_FIELDS and _QUAKE.search(title + " " + body):
        # disaster studies (Social Sciences) only in Aotearoa or the Pacific; Earth science anywhere
        text = title + " " + body
        if field != "Social Sciences" or _A_PLACE.search(text) or place_hits(text)[0]:
            out.add("geo")
    return out


# ---------------------------------------------------------------- research areas (plain-language groups)
# One area per work, for readers of the investment plan: the five ocean / Earth areas come from the M lens
# sub-themes; everything else from the OpenAlex primary field and subfield.
RESEARCH_AREAS = {
    "eco": "Marine & coastal ecosystems", "ocn": "Ocean & climate processes", "geo": "Seafloor, tectonics & hazards",
    "ant": "Antarctica & the Southern Ocean", "gov": "Ocean law, governance & blue economy",
    "env": "Environment, climate & land", "hlt": "Health & wellbeing", "soc": "Society, culture & identity",
    "edu": "Education", "hum": "History, archaeology & languages", "art": "Arts, architecture & design",
    "dev": "Economy, business & development", "law": "Law & governance", "eng": "Engineering & technology",
    "sci": "Life & physical sciences",
}
_FIELD_AREA = {
    "Medicine": "hlt", "Nursing": "hlt", "Health Professions": "hlt", "Dentistry": "hlt", "Neuroscience": "hlt",
    "Pharmacology, Toxicology and Pharmaceutics": "hlt", "Psychology": "soc",
    "Environmental Science": "env", "Earth and Planetary Sciences": "env", "Agricultural and Biological Sciences": "env",
    "Economics, Econometrics and Finance": "dev", "Business, Management and Accounting": "dev", "Decision Sciences": "dev",
    "Engineering": "eng", "Computer Science": "eng", "Materials Science": "eng", "Chemical Engineering": "eng", "Energy": "eng",
    "Biochemistry, Genetics and Molecular Biology": "sci", "Chemistry": "sci", "Physics and Astronomy": "sci",
    "Mathematics": "sci", "Immunology and Microbiology": "sci", "Veterinary": "sci", "Arts and Humanities": "hum",
    "Social Sciences": "soc",
}
_SUBFIELD_AREA = {
    "Education": "edu", "Law": "law", "Health": "hlt", "Linguistics and Language": "hum", "Language and Linguistics": "hum",
    "Archeology": "hum", "History": "hum", "Classics": "hum", "Philosophy": "hum", "Religious studies": "hum",
    "Visual Arts and Performing Arts": "art", "Music": "art", "Literature and Literary Theory": "art", "Architecture": "art",
    "Conservation": "art", "Geography, Planning and Development": "dev", "Urban Studies": "dev",
    "Management, Monitoring, Policy and Law": "env", "Political Science and International Relations": "law",
    "Public Administration": "law", "Developmental and Educational Psychology": "edu", "Clinical Psychology": "hlt",
}


def research_area(mt, field, subfield):
    if mt:
        if "ant" in mt:
            return "ant"
        if "gov" in mt and field in M_FIELDS["gov"]:
            return "gov"
        if "eco" in mt and field in M_FIELDS["eco"] | {"Environmental Science"}:
            return "eco"
        if "geo" in mt and field in {"Earth and Planetary Sciences", "Engineering", "Social Sciences"}:
            return "geo"
        if "ocn" in mt:
            return "ocn"
        for k in ("eco", "geo", "gov"):
            if k in mt:
                return k
    return _SUBFIELD_AREA.get(subfield) or _FIELD_AREA.get(field) or "soc"


# Aotearoa, ocean and polar places named as the subject of study (map and places list only; they never put a
# work in lens P). code -> (label, regex on folded text, lat, lng)
OCEAN_PLACES = {
    "HGF": ("Hauraki Gulf / Tīkapa Moana", r"\bhauraki gulf\b|\btikapa moana\b", -36.55, 175.10),
    "BOP": ("Bay of Plenty & Whakaari", r"\bbay of plenty\b|\bwhakaari\b|\bwhite island\b", -37.55, 176.95),
    "HIK": ("Hikurangi margin", r"\bhikurangi\b", -40.2, 178.6),
    "CHR": ("Chatham Rise", r"\bchatham rise\b", -43.6, 179.5),
    "CHI": ("Chatham Islands / Rēkohu", r"\bchatham islands?\b|\brekohu\b", -44.0, -176.5),
    "KER": ("Kermadec Islands & Trench", r"\bkermadecs?\b", -30.0, -178.2),
    "CAM": ("NZ subantarctic & Campbell Plateau", r"\bcampbell plateau\b|\bcampbell island\b|\bauckland islands\b|\bsubantarctic islands\b", -51.0, 169.5),
    "CPL": ("Challenger Plateau", r"\bchallenger plateau\b", -39.5, 169.5),
    "FIO": ("Fiordland", r"\bfiordland\b", -45.4, 167.2),
    "CKS": ("Cook Strait", r"\bcook strait\b", -41.3, 174.5),
    "TAS": ("Tasman Sea", r"\btasman sea\b", -37.5, 161.0),
    "ROS": ("Ross Sea & McMurdo", r"\bross sea\b|\bross ice shelf\b|\bmcmurdo\b", -76.0, 175.0),
    "ANT": ("Antarctica", r"\bantarctica\b|\bantarctic\b", -82.0, 150.0),
    "SOC": ("Southern Ocean", r"\bsouthern ocean\b", -58.0, 160.0),
}
_OCEAN_PLACE_RX = {k: re.compile(v[1]) for k, v in OCEAN_PLACES.items()}


def ocean_places(text):
    """Codes of OCEAN_PLACES named in folded text (Ross Sea also implies Antarctica only if named)."""
    return {k for k, rx in _OCEAN_PLACE_RX.items() if rx.search(text)}


# ---------------------------------------------------------------- UoA units and faculties

FACULTIES = ["Medical and Health Sciences", "Science", "Engineering and Design", "Arts and Education", "Law",
             "Business School", "Liggins Institute", "Auckland Bioengineering Institute"]

# Faculty names as they appear in affiliations (2020-2026) -> current faculty. Arts, Education and
# Social Work (and Elam, Music, Dance from Creative Arts and Industries) now form Arts and Education;
# Architecture and Planning joined Engineering and Design in January 2025.
_FACULTY_NAME = [
    (re.compile(r"faculty of medical (?:and|&)? ?health sciences?|faculty of medicine and health sciences?|faculty of medical health sciences?"), "Medical and Health Sciences"),
    (re.compile(r"faculty of science\b"), "Science"),
    (re.compile(r"faculty of engineering\b"), "Engineering and Design"),
    (re.compile(r"faculty of arts and education|faculty of arts\b|faculty of education\b"), "Arts and Education"),
    (re.compile(r"faculty of law\b|auckland law school"), "Law"),
    (re.compile(r"faculty of business|business school"), "Business School"),
    (re.compile(r"liggins institute"), "Liggins Institute"),
    (re.compile(r"(?:auckland )?bioengineering institute"), "Auckland Bioengineering Institute"),
]
# Units whose faculty is unambiguous (checked against co-occurring faculty names in the data).
_UNIT_FACULTY = [
    (r"school of population health|school of medicine\b|school of medical sciences|school of nursing|school of pharmacy|"
     r"school of optometry|department of (?:medicine|surgery|general surgery|ophthalmology|paediatrics|psychological medicine|"
     r"obstetrics|anaesthesiology|physiology|molecular medicine|general practice|epidemiology|nutrition|pacific health|"
     r"anatomy|pharmacology|oncology)|pacific health section|te kupenga hauora maori|centre for brain research",
     "Medical and Health Sciences"),
    (r"school of environment|school of biological sciences|te kura matauranga koiora|institute of marine sciences?|"
     r"leigh marine laboratory|school of chemical sciences|department of (?:physics|statistics|mathematics|exercise sciences)|"
     r"school of psychology|school of computer science|centre for biodiversity and biosecurity", "Science"),
    (r"department of (?:civil|mechanical|electrical|engineering science|chemical and materials)|"
     r"dept\.? of civil|school of architecture and planning|faculty of engineering and design", "Engineering and Design"),
    (r"school of maori studies and pacific studies|te wananga o waipapa|school of social sciences?|department of anthropology|"
     r"school of humanities|school of cultures,? languages|school of critical studies in education|"
     r"school of curriculum and pedagogy|school of learning,? development|school of counselling,? human services|"
     r"te puna wananga|elam school|school of music|dance studies|school of creative arts", "Arts and Education"),
    (r"department of property", "Business School"),
]
_UNIT_FACULTY = [(re.compile(rx), fac) for rx, fac in _UNIT_FACULTY]

_UNIT = re.compile(
    r"((?:school|department|dept\.?|institute|centre|center|section|unit|te [a-z][a-z ]+?)\b[^,;]*?)"
    r"(?=,|;|$| the university| university of auckland| waipapa taumata rau| private bag| auckland)")


def uoa_affiliation_strings(authorship, uoa_id):
    """Raw affiliation strings that OpenAlex links to UoA (never AUT)."""
    out = []
    for af in authorship.get("affiliations") or []:
        if any(i.endswith(uoa_id) for i in af.get("institution_ids") or []):
            s = af.get("raw_affiliation_string") or ""
            if not re.search(r"university of technology|\baut\b", s, re.I):
                out.append(s)
    return out


def faculty_of(raw_strings):
    """(faculty, unit) for one authorship from its UoA affiliation strings; either may be None."""
    fac, unit = None, None
    for s in raw_strings:
        f = fold(s)
        for rx, name in _FACULTY_NAME:
            if rx.search(f):
                fac = fac or name
        if "creative arts and industries" in f and not fac:
            if re.search(r"architecture|planning", f):
                fac = "Engineering and Design"
            elif re.search(r"elam|fine arts|music|dance", f):
                fac = "Arts and Education"
        for rx, name in _UNIT_FACULTY:
            if rx.search(f):
                fac = fac or name
        unit = unit or unit_of(s)
    return fac, unit


_CUT = re.compile(r"\s+(?:the )?university of auckland.*$|\s+waipapa taumata rau.*$|\s+private bag.*$|\s+auckland,? (?:new zealand|1\d{3}).*$")
_UNIT_WORD = re.compile(r"\b(?:school|department|dept|institute|centre|center|section|unit|programme|laboratory)\b")
_TE_REO_UNITS = re.compile(r"^(?:te kupenga hauora maori|te wananga o waipapa|te puna wananga|te kura matauranga koiora|"
                           r"te punaha matatini|te pare school of architecture and planning)$")
_NOT_UNIT = re.compile(r"universit|faculty|hospital|te whatu ora|health new zealand|te toka tumai|district|"
                       r"^(?:school|department|dept|section|centre|center|institute|unit)\.?$")


def unit_of(raw):
    """Most specific UoA unit named in one raw affiliation string: a whole comma-separated segment,
    returned in its original spelling (macrons kept), tidied ("Dept." -> "Department")."""
    for seg in re.split(r"[,;]", raw or ""):
        seg = re.sub(_CUT.pattern, "", seg.strip(" ."), flags=re.I).strip(" .")
        f = fold(seg)
        if not f or len(f) < 8:
            continue
        if _TE_REO_UNITS.match(f) or (_UNIT_WORD.search(f) and not _NOT_UNIT.search(f)):
            seg = re.sub(r"^(?:the\s+)", "", seg, flags=re.I)
            seg = re.sub(r"^dept\.?\s+", "Department ", seg, flags=re.I)
            return re.sub(r"\s+", " ", seg)
    return None


# ---------------------------------------------------------------- one decision for works and awards

PARTNER_MAX_AUTHORS = 20  # a Pacific Island co-author on a small team = research in the Pacific


def classify(title, abstract, keywords="", field=None, n_authors=0, partner=False, subfield=None):
    """Decide whether a record is research in or about the Pacific, and how strongly.

    Returns dict(lenses=set of "P","O","A","M", tier, places={code: n}, evidence=[...], mt=M sub-themes, op=ocean places):
      tier "focus"       Pacific named in the title; a specific place, people or Pacific concept anywhere;
                         a Pacific Island partner on a team of <= PARTNER_MAX_AUTHORS; or the Pacific Ocean
                         / Pacific climate named repeatedly
      tier "population"  generic "Pacific" / "Pasifika" only in the abstract, either repeated or beside other
                         groups (Māori, Asian, European, "ethnic"): Pacific peoples as one group in a wider
                         study, typically NZ health data reported by ethnicity. A review of 25 works that a
                         "repeated mentions" rule would have called focus found about three in four were such
                         studies, so repetition alone does not make a work Pacific-focused.
      tier "mention"     any other single passing mention
      tier None          no Pacific / Pacific Ocean evidence (may still be lens A)
    Keywords (OpenAlex-assigned) stand in for the abstract when a publisher withholds it.
    """
    t = fold(title)
    body = fold(abstract) + " " + fold(keywords)
    tp, _ = place_hits(t)
    bp, b_ethnic = place_hits(body)
    to, bo = ocean_hits(t), ocean_hits(body)
    places = dict(bp)
    for k, v in tp.items():
        places[k] = places.get(k, 0) + v
    lenses = set()
    if tp or bp or (partner and n_authors <= PARTNER_MAX_AUTHORS):
        lenses.add("P")
    if to or bo:
        lenses.add("O")
    if aotearoa_theme(t, t + " " + body, field):
        lenses.add("A")
    mt = marine_themes(t, body, field, subfield)
    if mt:
        lenses.add("M")
    evidence = []
    # A country/territory or Pacific concept is specific on one mention; a region needs two.
    specific = [k for k in places if k not in GENERIC and (k not in REGIONS or places[k] >= 2)]
    n_generic_body = sum(v for k, v in bp.items() if k in GENERIC)
    tier = None
    if tp or to:
        tier = "focus"; evidence.append("named in the title")
    elif specific:
        tier = "focus"; evidence.append("names " + ", ".join(PLACES[k][0] for k in specific))
    elif partner and n_authors <= PARTNER_MAX_AUTHORS:
        tier = "focus"; evidence.append("Pacific Island co-author")
    elif bo >= 2:
        tier = "focus"; evidence.append("Pacific Ocean / climate named repeatedly")
    elif b_ethnic > 0 or n_generic_body >= 2:
        tier = "population"; evidence.append("Pacific peoples as one group in a wider study")
    elif bp or bo:
        tier = "mention"; evidence.append("a single passing mention")
    if partner and n_authors <= PARTNER_MAX_AUTHORS and "Pacific Island co-author" not in evidence:
        evidence.append("Pacific Island co-author")
    if "A" in lenses:
        evidence.append("Aotearoa environment / hazards")
    if mt:
        evidence.append("ocean, Earth & climate: " + ", ".join(M_THEMES[k][0].lower() for k in sorted(mt)))
    nz = bool(_A_PLACE.search(t + " " + body))
    return dict(lenses=lenses, tier=tier, places=places, evidence=evidence, nz=nz, mt=mt,
                op=ocean_places(t + " " + body))
