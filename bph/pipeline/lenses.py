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
    # added November 2026 (checked against SPC's 22 Pacific Island countries and territories): the Northern
    # Mariana Islands, the states of the Federated States of Micronesia, and adjective / people forms
    '"Northern Mariana Islands"', '"Mariana Islands"', "Saipan", "CNMI", "Chuuk", "Pohnpei", "Kosrae",
    "Palauan", "Nauruan", "Guamanian", "Tahitian", '"Papua New Guinean"', '"Solomon Islander"', '"Solomon Islanders"',
    '"Cook Islander"', '"Cook Islanders"', "Kanaky", "Rapanui", "Wallisian", "Futunan",
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


# M  Ocean, Earth & climate systems: Blue Pacific research framed around marine systems, earth science,
#    climate processes, Antarctica or ocean governance, whether or not it names the Pacific or Aotearoa
#    (added November 2026 after BPH's review: Hikurangi, Chatham Rise, contourites, plankton, marine
#    mammals, Hauraki Gulf, Antarctica, ocean law ...). Candidate search only; tagging.marine_themes()
#    decides membership and sub-theme with field checks.
LENS_M = [
    # marine & coastal ecosystems
    "marine", "plankton", "phytoplankton", "zooplankton", '"marine mammal"', '"marine mammals"', "whale", "whales",
    "dolphin", "dolphins", "cetacean", "cetaceans", "seabird", "seabirds", "fisheries", "fishery", "aquaculture", "kelp",
    "seaweed", "seagrass", "mangrove", "mangroves", "coral", "reef", "reefs", "estuary", "estuaries", "estuarine",
    "intertidal", "subtidal", '"Hauraki Gulf"', "shellfish", "snapper", "shark", "sharks",
    # ocean & climate processes
    "ocean", "oceans", "oceanography", "oceanographic", '"sea level"', '"sea-level"', '"ocean current"',
    '"ocean currents"', "upwelling", "paleoceanography", "palaeoceanography", "paleoclimate", "palaeoclimate",
    '"ocean acidification"', '"marine heatwave"', '"marine heatwaves"', "coastal", "shoreline", '"sea surface temperature"',
    # seafloor, tectonics & hazards
    "seafloor", "seabed", '"sea floor"', "submarine", '"continental shelf"', '"continental margin"',
    '"continental slope"', "contourite", "contourites", "pockmark", "pockmarks", "subduction", "Hikurangi",
    '"Chatham Rise"', '"Campbell Plateau"', '"Challenger Plateau"', "earthquake", "earthquakes", "tsunami", "tsunamis",
    # Antarctica & the Southern Ocean
    "Antarctica", "Antarctic", '"Southern Ocean"', '"Ross Sea"', '"sea ice"', '"ice shelf"',
    # ocean law, governance & blue economy
    '"law of the sea"', "UNCLOS", '"maritime boundaries"', '"maritime security"', '"maritime zones"', '"deep-sea mining"',
    '"deep sea mining"', '"seabed mining"', '"blue economy"', '"ocean governance"', '"marine protected area"',
    '"marine protected areas"', '"marine spatial planning"', '"exclusive economic zone"',
]


def ors(terms):
    return " OR ".join(terms)


UOA_RAW_SEARCH = 'raw_affiliation_strings.search:"University of Auckland" OR "Waipapa Taumata Rau" OR "University of Aukland"'


def lens_filters():
    """OpenAlex filter fragments (title_and_abstract.search) per lens; A is two ANDed filters."""
    return {
        "P": ["title_and_abstract.search:" + ors(LENS_P)],
        "O": ["title_and_abstract.search:" + ors(LENS_O)],
        "A": ["title_and_abstract.search:" + ors(A_PLACE), "title_and_abstract.search:" + ors(A_THEME)],
        "M": ["title_and_abstract.search:" + ors(LENS_M)],
    }
