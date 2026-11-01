"""Search expressions that define the corpus (OpenAlex `title_and_abstract.search` syntax)."""

# Works that name a Pacific research methodology, framework or concept. Terms in
# PRM_TERMS_NEED_PACIFIC also occur outside Pacific scholarship, so they only count when the
# work also matches PACIFIC_TERMS.
PRM_TERMS_NEED_PACIFIC = [
    '"Oceanic epistemology"',
    '"relational space"',
    '"tā vā"',
]
PRM_TERMS = [
    "talanoa",
    '"teu le va"',
    '"tauhi va"',
    "fonofale",
    "faafaletui",
    '"fa\'afaletui"',
    '"kakala research"',
    '"kakala framework"',
    '"vanua research"',
    '"vanua framework"',
    '"tok stori"',
    "tivaevae",
    '"ta va theory"',
    '"Pacific research methodology"',
    '"Pacific research methodologies"',
    '"Pacific methodologies"',
    '"Pacific methodology"',
    '"Pacific research paradigm"',
    '"Pacific research framework"',
    '"Pacific research frameworks"',
    '"Pasifika research"',
    '"Pacific Indigenous research"',
    '"Indigenous Pacific research"',
    '"Pacific epistemology"',
    '"Kaupapa Pasifika"',
    '"masi methodology"',
    '"va relational"',
]

# Concept tags for the explorer's filters: label -> lowercase phrases matched in title/abstract.
CONCEPTS = {
    "Talanoa": ["talanoa"],
    "Talanoa Dialogue (UNFCCC)": ["talanoa dialogue"],
    "Vā / teu le vā / tauhi vā": ["teu le va", "tauhi va", "the va ", "va relational", "va-centred", "va centred", "relational space", "socio-spatial", "sociospatial"],
    "Tā-vā": ["ta-va", "ta va ", "tavani", "temporality, spatiality"],
    "Fonofale": ["fonofale"],
    "Fa'afaletui": ["faafaletui", "fa'afaletui", "fa’afaletui"],
    "Kakala": ["kakala"],
    "Vanua": ["vanua"],
    "Tok stori": ["tok stori"],
    "Tivaevae": ["tivaevae", "tivaivai"],
    "Masi": ["masi methodology"],
    "Kaupapa Māori": ["kaupapa maori", "kaupapa māori"],
    "Decolonising": ["decoloni"],
    "Pacific research paradigm": ["pacific research", "pacific methodolog", "pasifika research", "pacific indigenous research", "indigenous pacific research", "pacific epistemolog"],
}

# Works about Pacific places and peoples; used to keep only Pacific-relevant citers of
# broadly cited seeds such as Decolonizing Methodologies.
PACIFIC_TERMS = (
    '"Pacific Islands" OR "Pacific Island" OR "Pacific peoples" OR "Pacific people" OR Pasifika OR '
    'Oceania OR Moana OR Samoa OR Samoan OR Tonga OR Tongan OR Fiji OR Fijian OR "Cook Islands" OR '
    'Niue OR Niuean OR Tokelau OR Tuvalu OR Kiribati OR Vanuatu OR "Solomon Islands" OR '
    '"Papua New Guinea" OR Hawaii OR Hawaiian OR "Kanaka Maoli" OR "Marshall Islands" OR '
    'Micronesia OR Melanesia OR Melanesian OR Polynesia OR Polynesian OR Chamorro OR CHamoru OR '
    'Tahiti OR "Rapa Nui" OR Kanak OR Palau OR Nauru OR "Pacific research" OR "Pacific students" OR '
    '"Pacific communities" OR "Pacific health" OR "Pacific education"'
)
