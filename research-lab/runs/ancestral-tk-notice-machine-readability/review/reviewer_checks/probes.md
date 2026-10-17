# Live API probes (reviewer)

Requests: 73 (first batch) + 6 (second batch) = 79; one at a time, 1 s apart; raw responses cached under cache/.

## DataCite query variants (api.datacite.org/dois)

| probe | query | total | returned | not in census raw | element-bearing among novel |
|---|---|---|---|---|---|
| d1_rightsUri_wild | `rightsList.rightsUri:*localcontexts*` | 48353 | 1 | 0 | 0 |
| d2_rightsUri_wild_notneo | `rightsList.rightsUri:*localcontexts* AND NOT prefix:10.21233` | 21 | 21 | 0 | 0 |
| d3_token_localcontexts | `localcontexts` | 2 | 1 | 0 | 0 |
| d4_phrase_hub_domain | `"localcontextshub.org"` | 4 | 4 | 0 | 0 |
| d5_phrase_lc_domain | `"localcontexts.org" AND NOT prefix:10.21233` | 4 | 4 | 4 | 0 |
| d6_any_wild_notneo | `*localcontexts* AND NOT prefix:10.21233` | 14 | 14 | 5 | 1 |
| d7_desc_wild_notneo | `descriptions.description:*localcontexts* AND NOT prefix:10.21233` | 11 | 11 | 4 | 0 |
| d8_related_wild | `relatedIdentifiers.relatedIdentifier:*localcontexts*` | 3 | 3 | 1 | 1 |
| d9a_identifiers_wild | `identifiers.identifier:*localcontexts*` | 2 | 2 | 0 | 0 |
| d9b_altid_wild | `alternateIdentifiers.alternateIdentifier:*localcontexts*` | 0 | 0 | 0 | 0 |
| d10_subjects_wild | `subjects.subject:*localcontexts*` | 0 | 0 | 0 | 0 |
| d11_rights_text_wild_notneo | `rightsList.rights:*localcontexts* AND NOT prefix:10.21233` | 10 | 10 | 0 | 0 |
| d12_scheme_LC_notneo | `rightsList.rightsIdentifierScheme:"Local Contexts" AND NOT prefix:10.21233` | 11 | 11 | 0 | 0 |
| d12b_scheme_LC_all | `rightsList.rightsIdentifierScheme:"Local Contexts"` | 48343 | 1 | 0 | 0 |
| d13_BC_Provenance | `"BC Provenance"` | 7 | 7 | 7 | 0 |
| d14_TK_Attribution | `"TK Attribution"` | 0 | 0 | 0 | 0 |
| d15_Attribution_Incomplete | `"Attribution Incomplete"` | 8 | 8 | 8 | 0 |
| d16_Open_to_Collaborate_notneo | `"Open to Collaborate" AND NOT prefix:10.21233` | 16 | 16 | 14 | 0 |
| d17_subjects_phrase_LC | `subjects.subject:"Local Contexts"` | 17 | 17 | 0 | 0 |
| d18_token_hub | `localcontextshub` | 0 | 0 | 0 | 0 |
| d19_phrase_LC_total | `"Local Contexts"` | 3600 | 1 | 0 | 0 |
| d20_BC_Notice_phrase_notneo | `"BC Notice" AND NOT prefix:10.21233` | 4 | 1 | 0 | 0 |

Novel element-bearing record: 10.48321/d190108951 (DMPTool output-management plan 'MOZEROA 2030', Hub project e884d181 in relatedIdentifiers; live, Gump institution project with three Notices). All other novel hits are false phrase matches ('1330-1300 BC), provenance unknown', 'open to collaborate with', 'Attribution Incomplete' absent as a Notice) or general references to localcontexts.org.

## The two VUW figshare DOIs in DataCite

- 10.26686/wgtn.25790481: REST /dois -> HTTP 404; query doi:"10.26686/wgtn.25790481" total 0; handle API responseCode 1 -> https://openaccess.wgtn.ac.nz/articles/thesis/Investigating_Galaxias_postvectis_... (registered in the handle system, absent from DataCite's public index: registered-but-not-findable or not DataCite-indexed).
- 10.26686/wgtn.28974539: REST /dois -> HTTP 404; query doi:"10.26686/wgtn.28974539" total 0; handle API responseCode 1 -> https://openaccess.wgtn.ac.nz/articles/thesis/Conservation_and_restoration_genom... (registered in the handle system, absent from DataCite's public index: registered-but-not-findable or not DataCite-indexed).

## Local Contexts Hub projects (api/v1/projects/<id>/)

| project | HTTP | privacy | created_by | notices | BC labels | TK labels | title |
|---|---|---|---|---|---|---|---|
| 03818172 | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | Island Sustainability Program (ISP) |
| 0aa4b8c6 | 200 | Public | institution: Tetiaroa Society | biocultural |  |  | Strawberry Hermit Crabs |
| 212bef2e | 200 | Public | institution: Plant & Food Research | biocultural |  |  | Maire tawake genome |
| 222da5aa | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | Does it poop? An exploration of bêche-de-mer/sea cucumber gut biome |
| 3f341ef3 | 200 | Public | institution: Tetiaroa Society | biocultural |  |  | ARMS for Biodiversity Baselines in Polynesie Francaise |
| 54be05d7 | 200 | Public | institution: Gump South Pacific Research Station | biocultural |  |  | Biocode 2.0 |
| 71b32571 | 200 | Public | institution: Gump South Pacific Research Station |  | consent_verified (Faarii; community=Atiti'a Center) |  | Moorea Biocode 1.0 |
| 7b9e7321 | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | Temae Scavenger Hunt - ISP 2025 |
| 8056c536 | 404 | None |  |  |  |  |  |
| 9a7785a1 | 200 | Public | institution: Tetiaroa Society | biocultural |  |  | Fish Biodiversity Survey |
| a0a7f8ab | 200 | Public | researcher: Jane Anderson | biocultural, traditional_knowledge |  |  | Recognizing Indigenous Interests: Labelling DSI with Provenance Metada |
| abc009aa | 200 | Public | researcher: Megan Wong | biocultural |  |  | Djandak Dja Kunditja (Country Healing its home) - The assessment of Bi |
| bf647797 | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | Mo’orea eDNA Project / Projet eDNA |
| c57b53f1 | 200 | Public | community: Te Roroa |  | provenance (BC Provenance (BC P); community=Te Roroa) |  | Habitat use and spawning behaviour of Galaxis postvectis, short-jaw kō |
| d06d7125 | 200 | Public | researcher: Megan Wong | biocultural |  |  | Data governance with CARE: A case study of interests under the kangaro |
| d7d74bae | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | Coastal Monitoring & Benthic Surveys (Surveillance côtière et études b |
| e260673d | 404 | None |  |  |  |  |  |
| e2e9341e | 200 | Contributor | researcher: Colan Balkwill | attribution_incomplete, biocultural |  |  | Conservation and restoration genomics of Syzygium maire, a nationally  |
| e884d181 | 200 | Public | institution: Gump South Pacific Research Station | attribution_incomplete, biocultural, traditional_knowledge |  |  | MOZEROA 2030: Innovative Mosquito Control on Huahine Island |
| f2e1acfd | 404 | None |  |  |  |  |  |
Summary: 17 of 20 linked projects resolve; 2 carry a Label at the Hub (c57b53f1 Te Roroa BC Provenance, community-created; 71b32571 Moorea Biocode 1.0 BC Consent Verified 'Faarii', community Atiti'a Center, institution-created project); the other 15 live projects carry Notices only. Project e2e9341e has privacy 'Contributor'.

## Other platforms

- Harvard Dataverse metadata blocks: 24 blocks, none for Local Contexts: geospatial, socialscience, astrophysics, biomedical, journal, customPSI, customMRA, customPSRI, customGSD, customDigaai, customCHIA, customARCS, custom_hbgdki, citation, customCIESIN, AdditionalMetadataAboutDataset, customNDR, customSAEF, computationalworkflow, customMORU, 3dobjects, customCAFEQualityChecklist, customCAFEDataSources, customCAFEDataLocation.
- Harvard Dataverse search `localcontextshub.org`: total 0.
- Harvard Dataverse search `localcontexts*`: total 0.
- Harvard Dataverse search `"Local Contexts"`: total 196.
- Harvard Dataverse search `localcontexts`: total 0.
- Harvard Dataverse search `localcontextshub`: total 0.
- Zenodo `localcontexts`: total 0 (HTTP 200).
- Zenodo `"localcontextshub.org"`: total 1 (HTTP 200).
- Zenodo `metadata.rights.link:"https://localcontextshub.org/projects/54be05d7-aa5c-4886-abd9-dc45b2fa8df4"`: total 2 (HTTP 200).
- Zenodo `metadata.rights.title.en:"BC-Notice"`: total 2 (HTTP 200).
- Zenodo `localcontexts`: total 0 (HTTP 200).
- Zenodo record 10381317, InvenioRDM serialisation: rights includes a 'BC-Notice' entry with the Hub link = True; legacy JSON (what the census scanned) contains the Hub link = False.
- Zenodo `metadata.rights.link:*localcontexts*`: HTTP 400 (wildcard rejected).
- GBIF g1_mt_ns_lc: {"status": 200, "count": 0, "titles": []}
- GBIF g2_mt_ns_hub: {"status": 200, "count": 0, "titles": []}
- GBIF g3_q_hub: {"status": 200, "count": 0, "titles": []}
- GBIF g4_q_tk_label: {"status": 200, "count": 2, "titles": ["Some Botswana Traditional Medicinal Plants held at PSUB Herbarium", "Redux Sellow: revealing Sellow\u2019s collections from the Herbier Imp\u00e9rial du Br\u00e
- RAiD single-record endpoint keys: ['access', 'contributor', 'date', 'identifier', 'metadata', 'organisation', 'subject', 'title']; traditionalKnowledgeLabel present: False; public registry totalCount 622.
- re3data `Neotoma`: 1 repositories ['Neotoma Paleoecology Database']
- re3data `pollen`: 3 repositories ['Palynological Database', 'NOAA National Centers for Environmental Information -  Paleoclimatology Data', 'Neotoma Paleoecology Database']
- re3data `Indigenous`: 10 repositories ['dharmae', 'Oceans 3.0 Data Portal', 'DataStream', 'Columbia Basin Water Hub']
- re3data `localcontexts`: 0 repositories []
- OSF o1_share: HTTP 503
- OSF o2_osf_v2_search: HTTP 503
- OSF o3_osf_nodes_desc: HTTP 503
- OpenAIRE re-check of 3 'unavailable' Neotoma DOIs: {"10.21233/gctk-by68": {"status": 200, "numFound": 0}, "10.21233/717z-b048": {"status": 200, "numFound": 0}, "10.21233/k9b1-7y11": {"status": 200, "numFound": 0}}
