"""The three lenses that define "research in or about the Pacific", as OpenAlex title/abstract searches.

P  Pacific Islands & peoples: names a Pacific Island country, territory or island group, a Pacific
   people, or the Pacific as a region or community. (Works co-authored with an institution in a
   Pacific Island country or territory also join this lens; see build_corpus.py.)
O  Pacific Ocean & climate: names the Pacific Ocean or its sub-regions, or the Pacific climate modes
   (ENSO, IPO, PDO) that shape the region.
A  Aotearoa in the Blue Pacific: names Aotearoa / New Zealand / Māori AND a Blue Pacific Horizons
   theme (ocean and coasts, fisheries and aquaculture, climate, natural hazards, environment and
   stewardship), following the SRA's own framing of Aotearoa as part of the Pacific region.

Each lens is a phrase list ORed together; A is (place) AND (theme).
"""

LENS_P = [
    '"Pacific Islands"', '"Pacific Island"', '"Pacific Islander"', '"Pacific Islanders"',
    '"Pacific peoples"', '"Pacific people"', '"Pacific communities"', '"Pacific community"',
    '"Pacific families"', '"Pacific youth"', '"Pacific women"', '"Pacific students"',
    '"Pacific health"', '"Pacific region"', '"Pacific nations"', '"Pacific countries"',
    "Pasifika", "Polynesia", "Polynesian", "Melanesia", "Melanesian", "Micronesia", "Micronesian",
    "Oceania", "Samoa", "Samoan", "Tonga", "Tongan", "Fiji", "Fijian", "iTaukei",
    '"Cook Islands"', "Niue", "Niuean", "Tokelau", "Tokelauan", "Tuvalu", "Tuvaluan",
    "Kiribati", "I-Kiribati", "Vanuatu", "ni-Vanuatu", '"Solomon Islands"', '"Papua New Guinea"',
    "Bougainville", "Hawaii", "Hawaiian", "Hawaiʻi", '"Marshall Islands"', "Marshallese", "Palau",
    "Nauru", "Guam", "Chamorro", "CHamoru", '"New Caledonia"', "Kanak", "Tahiti", '"French Polynesia"',
    '"Rapa Nui"', '"Easter Island"', '"Wallis and Futuna"', "Pitcairn",
]

LENS_O = [
    '"Pacific Ocean"', '"South Pacific"', '"Southwest Pacific"', '"South-west Pacific"',
    '"southwestern Pacific"', '"western Pacific"', '"tropical Pacific"', '"equatorial Pacific"',
    '"North Pacific"', '"eastern Pacific"', '"Pacific basin"', "Moana", '"Te Moana-nui-a-Kiwa"',
    '"El Niño"', '"El Nino"', '"La Niña"', '"La Nina"', "ENSO", '"Southern Oscillation"',
    '"Interdecadal Pacific Oscillation"', '"Pacific Decadal Oscillation"', "Kermadec",
]

A_PLACE = ['"New Zealand"', "Aotearoa", "Māori", "Maori", "Hauraki", "Waitematā", "Waitemata",
           '"Chatham Islands"', '"Tasman Sea"']
A_THEME = [
    "ocean", "oceans", "oceanic", "marine", "coastal", "coast", "coastline", "seafloor", "seabed",
    "estuary", "estuaries", "estuarine", "harbour", "harbor", "fisheries", "fishery", "fishing",
    "aquaculture", "mussel", "mussels", "kelp", "seaweed", "reef", "reefs", '"sea level"', '"sea-level"',
    "tsunami", "tsunamis", "cyclone", "cyclones", '"climate change"', '"climate adaptation"',
    "drought", "flood", "flooding", "earthquake", "earthquakes", "volcanic", "volcano", "erosion",
    '"natural hazard"', '"natural hazards"', "biodiversity", '"blue economy"', '"ocean energy"',
    '"wave energy"', '"tidal energy"', '"offshore wind"', "mātauranga", "matauranga", "kaitiakitanga",
    '"environmental justice"', '"resource management"', "freshwater", "wetland", "wetlands",
]


def ors(terms):
    return " OR ".join(terms)


def lens_filters():
    """OpenAlex filter fragments (title_and_abstract.search) per lens; A is two ANDed filters."""
    return {
        "P": ["title_and_abstract.search:" + ors(LENS_P)],
        "O": ["title_and_abstract.search:" + ors(LENS_O)],
        "A": ["title_and_abstract.search:" + ors(A_PLACE), "title_and_abstract.search:" + ors(A_THEME)],
    }
