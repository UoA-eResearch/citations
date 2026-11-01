"""Seed works for the Pacific Research Methodologies (PRM) corpus.

A starter list of widely cited PRM texts, grouped into strands. It is a starting point for the
literature review in the project Lisa Uperesa describes, not a canon: that review's curated
list replaces it.

Fields: key, surnames (for matching bylines), year, title, venue, form, strand, evidence (a
web page confirming a text the open graph does not surface), and broad=True for texts cited far outside Pacific scholarship, whose citing works are only kept
when they are themselves about the Pacific.
"""

STRANDS = {
    "foundations": "Oceanic & Indigenous foundations",
    "talanoa": "Talanoa",
    "va": "Vā & tā-vā",
    "frameworks": "Pacific frameworks & models",
    "paradigm": "Pacific research paradigm & guidelines",
}

SEEDS = [
    # --- Oceanic & Indigenous foundations ---
    dict(key="wendt1976", surnames=["Wendt"], year=1976, title="Towards a new Oceania", venue="Mana Review", form="article", strand="foundations", broad=True),
    dict(key="hauofa1994", surnames=["Hau'ofa", "Hauofa"], year=1994, title="Our sea of islands", venue="The Contemporary Pacific", form="article", strand="foundations", broad=True),
    dict(key="hauofa2008", surnames=["Hau'ofa", "Hauofa"], year=2008, title="We are the ocean: Selected works", venue="University of Hawai'i Press", form="book", strand="foundations", broad=True),
    dict(key="smith1999", surnames=["Smith"], year=1999, title="Decolonizing methodologies: Research and Indigenous peoples", venue="Zed Books / University of Otago Press", form="book", strand="foundations", broad=True),
    dict(key="bishop1998", surnames=["Bishop"], year=1998, title="Freeing ourselves from neo-colonial domination in research: A Maori approach to creating knowledge", venue="International Journal of Qualitative Studies in Education", form="article", strand="foundations", broad=True),
    dict(key="gegeo2001", surnames=["Gegeo", "Watson-Gegeo"], year=2001, title="How we know: Kwara'ae rural villagers doing indigenous epistemology", venue="The Contemporary Pacific", form="article", strand="foundations", broad=True),
    dict(key="meyer2001", surnames=["Meyer"], year=2001, title="Our own liberation: Reflections on Hawaiian epistemology", venue="The Contemporary Pacific", form="article", strand="foundations", broad=True),
    dict(key="thaman1993", surnames=["Thaman"], year=1993, title="Culture and the curriculum in the South Pacific", venue="Comparative Education", form="article", strand="foundations", broad=True),
    dict(key="thaman2003", surnames=["Thaman"], year=2003, title="Decolonizing Pacific studies: Indigenous perspectives, knowledge, and wisdom in higher education", venue="The Contemporary Pacific", form="article", strand="foundations", broad=False),
    dict(key="thaman2008", surnames=["Thaman"], year=2008, title="Nurturing relationships and honouring responsibilities: A Pacific perspective", venue="International Review of Education", form="article", strand="foundations", broad=False),
    dict(key="nabobobaba2006", surnames=["Nabobo-Baba", "Nabobo"], year=2006, title="Knowing and learning: An indigenous Fijian approach", venue="Institute of Pacific Studies, USP", form="book", strand="foundations", broad=False),
    dict(key="mahina2008", surnames=["Mahina", "Māhina"], year=2008, title="From vale (ignorance) to 'ilo (knowledge) to poto (skill): The Tongan theory of ako (education)", venue="AlterNative", form="article", strand="foundations", broad=False),

    # --- Talanoa ---
    dict(key="vaioleti2006", surnames=["Vaioleti"], year=2006, title="Talanoa research methodology: A developing position on Pacific research", venue="Waikato Journal of Education", form="article", strand="talanoa", broad=False),
    dict(key="vaioleti2013", surnames=["Vaioleti"], year=2013, title="Talanoa: Differentiating the talanoa research methodology from phenomenology, narrative, Kaupapa Maori and feminist methodologies", venue="Te Reo", form="article", strand="talanoa", broad=False),
    dict(key="otsuka2006", surnames=["Otsuka"], year=2006, title="Talanoa research: Culturally appropriate research design in Fiji", venue="AARE conference", form="conference", strand="talanoa", broad=False),
    dict(key="prescott2008", surnames=["Prescott"], year=2008, title="Using talanoa in Pacific business research in New Zealand: Experiences with Tongan entrepreneurs", venue="AlterNative", form="article", strand="talanoa", broad=False),
    dict(key="farrelly2014", surnames=["Farrelly", "Nabobo-Baba"], year=2014, title="Talanoa as empathic apprenticeship", venue="Asia Pacific Viewpoint", form="article", strand="talanoa", broad=False),
    dict(key="suaalii2014", surnames=["Suaalii-Sauni", "Fulu-Aiolupotea"], year=2014, title="Decolonising Pacific research, building Pacific research communities and developing Pacific research tools: The case of the talanoa and the faafaletui in Samoa", venue="Asia Pacific Viewpoint", form="article", strand="talanoa", broad=False),
    dict(key="faavae2016", surnames=["Fa'avae", "Faavae", "Jones", "Manu'atu"], year=2016, title="Talanoa'i 'a e talanoa - Talking about talanoa: Some dilemmas of a novice researcher", venue="AlterNative", form="article", strand="talanoa", broad=False),
    dict(key="vaka2016", surnames=["Vaka", "Brannelly", "Huntington"], year=2016, title="Getting to the heart of the story: Using talanoa to explore Pacific mental health", venue="Issues in Mental Health Nursing", form="article", strand="talanoa", broad=False),
    dict(key="tunufai2016", surnames=["Tunufa'i", "Tunufai"], year=2016, title="Pacific research: Rethinking the talanoa methodology", venue="New Zealand Sociology", form="article", strand="talanoa", broad=False),
    dict(key="tecun2018", surnames=["Tecun", "Hafoka", "'Ulu'ave"], year=2018, title="Talanoa: Tongan epistemology and Indigenous research method", venue="AlterNative", form="article", strand="talanoa", broad=False),
    dict(key="matapo2021", surnames=["Matapo", "Enari"], year=2021, title="Re-imagining the dialogic spaces of talanoa through Samoan onto-epistemology", venue="Waikato Journal of Education", form="article", strand="talanoa", broad=False),
    dict(key="faavae2022", surnames=["Fa'avae", "Faavae", "Faleolo", "Enari"], year=2022, title="e-talanoa as an online research method: extending vā-relations across spaces", venue="AlterNative", form="article", strand="talanoa", broad=False),

    # --- Vā & tā-vā ---
    dict(key="kaili2005", surnames=["Ka'ili", "Kaili"], year=2005, title="Tauhi vā: Nurturing Tongan sociospatial ties in Maui and beyond", venue="The Contemporary Pacific", form="article", strand="va", broad=False),
    dict(key="kaili2017", surnames=["Ka'ili", "Kaili"], year=2017, title="Marking indigeneity: The Tongan art of sociospatial relations", venue="University of Arizona Press", form="book", strand="va", broad=False),
    dict(key="mahina2010", surnames=["Mahina", "Māhina"], year=2010, title="Tā, vā, and moana: Temporality, spatiality, and indigeneity", venue="Pacific Studies", form="article", strand="va", broad=False),
    dict(key="anae2010", surnames=["Anae"], year=2010, title="Research for better Pacific schooling in New Zealand: Teu le va - a Samoan perspective", venue="MAI Review", form="article", strand="va", broad=False),
    dict(key="anae2016", surnames=["Anae"], year=2016, title="Teu le vā: Samoan relational ethics", venue="Knowledge Cultures", form="article", strand="va", broad=False),
    dict(key="airini2010", surnames=["Airini", "Anae", "Mila-Schaaf", "Coxon"], year=2010, title="Teu le va: Relationships across research and policy in Pasifika education", venue="Ministry of Education (NZ)", form="report", strand="va", broad=False),
    dict(key="lilomaiava2009", surnames=["Lilomaiava-Doktor"], year=2009, title="Beyond migration: Samoan population movement (malaga) and the geography of social space (vā)", venue="The Contemporary Pacific", form="article", strand="va", broad=False),
    dict(key="milaschaaf2006", surnames=["Mila-Schaaf", "Mila"], year=2006, title="Vā-centred social work: Possibilities for a Pacific approach to social work practice", venue="Tu Mau: Social Work Review 18(1)", form="article", strand="va", broad=False,
         evidence="https://anzswjournal.nz/anzsw/article/view/785"),
    dict(key="wendt1996", surnames=["Wendt"], year=1996, title="Tatauing the post-colonial body", venue="Span 42-43 (1996); reprinted as the afterword to Inside Out (1999)", form="article", strand="va", broad=False,
         evidence="https://www.vamoana.org/news/reading-group-02-2019"),

    # --- Pacific frameworks & models ---
    dict(key="thaman1997", surnames=["Thaman"], year=1997, title="Kakala: A Pacific concept of teaching and learning", venue="Australian College of Education national conference, Cairns", form="conference", strand="frameworks", broad=False,
         evidence="https://repository.usp.ac.fj/view/divisions/institute=5Fof=5Feducation/1997.html"),
    dict(key="johanssonfua2014", surnames=["Johansson-Fua", "Fua"], year=2014, title="Kakala research framework: A garland in celebration of a decade of rethinking education", venue="Of Waves, Winds and Wonderful Things (USP Press)", form="chapter", strand="frameworks", broad=False),
    dict(key="pulotu2001", surnames=["Pulotu-Endemann"], year=2001, title="Fonofale model of health", venue="Mental Health Commission (NZ)", form="report", strand="frameworks", broad=False,
         evidence="https://www.hauora.co.nz/assets/Fonofalemodelexplanation.pdf"),
    dict(key="tamasese2005", surnames=["Tamasese", "Peteru", "Waldegrave", "Bush"], year=2005, title="Ole Taeao Afua, the new morning: A qualitative investigation into Samoan perspectives on mental health and culturally appropriate services", venue="Australian and New Zealand Journal of Psychiatry", form="article", strand="frameworks", broad=False),
    dict(key="nabobobaba2008", surnames=["Nabobo-Baba", "Nabobo"], year=2008, title="Decolonising framings in Pacific research: Indigenous Fijian vanua research framework as an organic response", venue="AlterNative", form="article", strand="frameworks", broad=False),
    dict(key="sanga2018", surnames=["Sanga", "Reynolds", "Paulsen", "Spratt", "Maneipuri"], year=2018, title="A tok stori about tok stori: Melanesian relationality in action as research, leadership and scholarship", venue="Global Comparative Education", form="article", strand="frameworks", broad=False),
    dict(key="naepi2019", surnames=["Naepi"], year=2019, title="Masi methodology: Centring Pacific women's voices in research", venue="AlterNative", form="article", strand="frameworks", broad=False),
    dict(key="futterpuati2019", surnames=["Futter-Puati", "Maua-Hodges"], year=2019, title="Stitching tivaevae: A Cook Islands research method", venue="AlterNative", form="article", strand="frameworks", broad=False),
    dict(key="seiuli2013", surnames=["Seiuli"], year=2013, title="Uputaua: A therapeutic approach to researching Samoan communities", venue="The Australian Community Psychologist", form="article", strand="frameworks", broad=False),
    dict(key="milaschaaf2009", surnames=["Mila-Schaaf", "Hudson"], year=2009, title="The interface between cultural understandings: Negotiating new spaces for Pacific mental health", venue="Pacific Health Dialog", form="article", strand="frameworks", broad=False),

    # --- Pacific research paradigm & guidelines ---
    dict(key="anae2001", surnames=["Anae", "Coxon", "Mara", "Wendt-Samu", "Finau"], year=2001, title="Pasifika education research guidelines", venue="Ministry of Education (NZ)", form="report", strand="paradigm", broad=False,
         evidence="https://www.educationcounts.govt.nz/publications/pacific/5915"),
    dict(key="baba2004", surnames=["Baba", "Mahina", "Williams", "Nabobo-Baba"], year=2004, title="Researching the Pacific and Indigenous peoples: Issues and perspectives", venue="Centre for Pacific Studies, University of Auckland", form="book", strand="paradigm", broad=False),
    dict(key="sanga2004", surnames=["Sanga"], year=2004, title="Making philosophical sense of Indigenous Pacific research", venue="Researching the Pacific and Indigenous peoples", form="chapter", strand="paradigm", broad=False),
    dict(key="hrc2014", surnames=["Health Research Council"], year=2014, title="Pacific health research guidelines", venue="Health Research Council of New Zealand", form="report", strand="paradigm", broad=False,
         evidence="https://www.hrc.govt.nz/resources/pacific-health-research-guidelines-2014-0"),
    dict(key="mcfall2010", surnames=["McFall-McCaffery"], year=2010, title="Getting started with Pacific research: Finding resources and information on Pacific research models and methodologies", venue="MAI Review", form="article", strand="paradigm", broad=False),
    dict(key="sanga2017", surnames=["Sanga", "Reynolds"], year=2017, title="To know more of what it is and what it is not: Pacific research on the move", venue="Pacific Dynamics", form="article", strand="paradigm", broad=False),
    dict(key="ponton2018", surnames=["Ponton"], year=2018, title="Utilizing Pacific methodologies as inclusive practice", venue="SAGE Open", form="article", strand="paradigm", broad=False),
    dict(key="tualaulelei2019", surnames=["Tualaulelei", "McFall-McCaffery"], year=2019, title="The Pacific research paradigm: Opportunities and challenges", venue="MAI Journal", form="article", strand="paradigm", broad=False),
    dict(key="enari2021", surnames=["Enari"], year=2021, title="Methodology marriage: Merging Western and Pacific research design", venue="Pacific Dynamics", form="article", strand="paradigm", broad=False),
]
