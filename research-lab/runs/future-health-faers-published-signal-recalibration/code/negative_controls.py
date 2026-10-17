"""Negative-control drug-event pairs (plan section 4): the OHDSI MethodEvaluation negative-control set, every target and
comparator drug with its outcome, each outcome mapped to one MedDRA Preferred Term by the fixed table below (written
before any control was computed). Outcomes with no clear PT equivalent map to None and are dropped; a mapped PT absent
from FAERS is dropped when the pairs are computed. Writes data/negative_controls.csv (drug, pt, source_outcome)."""
from pathlib import Path

import pandas as pd
import pyreadr

RUN = Path(__file__).resolve().parents[1]
PT = {"Acute pancreatitis": "Pancreatitis acute", "GI bleeding": "Gastrointestinal haemorrhage", "Stroke": "Cerebrovascular accident",
      "Inflammatory Bowel Disease": "Inflammatory bowel disease", "Human papilloma virus infection": "Papilloma viral infection",
      "Verruca vulgaris": "Skin papilloma", "Alcohol abuse": "Alcohol abuse", "Croup": "Croup infectious",
      "Fibrocystic disease of breast": "Fibrocystic breast disease", "Ingrowing nail": "Ingrowing nail",
      "Neoplasm of uncertain behavior of skin": None, "Seborrheic keratosis": "Seborrhoeic keratosis",
      "Candida infection of genital region": "Genital candidiasis", "Carcinoma in situ of breast": None,
      "Developmental speech disorder": "Speech disorder developmental", "Exostosis": "Exostosis", "Non-toxic uninodular goiter": "Goitre",
      "Presbyopia": "Presbyopia", "Social phobia": "Social phobia", "Tinea pedis": "Tinea pedis",
      "Obsessive-compulsive disorder": "Obsessive-compulsive disorder", "Peripheral venous insufficiency": "Venous insufficiency",
      "Acute bronchitis": "Bronchitis", "Benign neoplasm of skin": "Benign neoplasm of skin", "Chronic sinusitis": "Chronic sinusitis",
      "Primary malignant neoplasm of respiratory tract": None, "Diaphragmatic hernia": "Diaphragmatic hernia",
      "Acute stress disorder": "Acute stress disorder", "Adjustment disorder": "Adjustment disorder", "Atelectasis": "Atelectasis",
      "Chalazion": "Chalazion", "Condyloma acuminatum": "Anogenital warts", "Diabetic oculopathy": None,
      "Molluscum contagiosum infection": "Molluscum contagiosum", "Polycystic ovaries": "Polycystic ovaries",
      "Vitamin D deficiency": "Vitamin D deficiency", "Lyme disease": "Lyme disease", "Endometriosis": "Endometriosis",
      "Dysplasia of cervix": "Cervical dysplasia", "Migraine with aura": "Migraine with aura", "Obesity": "Obesity", "Sciatica": "Sciatica",
      "Sleep apnea": "Sleep apnoea syndrome", "Astigmatism": "Astigmatism", "Non-toxic nodular goiter": "Goitre",
      "Intracranial injury": None, "Curvature of spine": "Scoliosis", "Cutis laxa": "Cutis laxa",
      "Alcohol withdrawal syndrome": "Alcohol withdrawal syndrome", "Allergic rhinitis due to pollen": "Seasonal allergy",
      "Atopic dermatitis": "Dermatitis atopic", "Attention deficit hyperactivity disorder": "Attention deficit hyperactivity disorder",
      "Bipolar disorder": "Bipolar disorder", "Contact dermatitis": "Dermatitis contact", "Crohn's disease": "Crohn's disease",
      "Cyst of ovary": "Ovarian cyst", "Dysmenorrhea": "Dysmenorrhoea", "Myopia": "Myopia", "Otalgia": "Ear pain",
      "Otitis media": "Otitis media", "Allergic rhinitis": "Rhinitis allergic", "Arthropathy of knee joint": None,
      "Enthesopathy": "Enthesopathy", "Human immunodeficiency virus infection": "HIV infection", "Hydronephrosis": "Hydronephrosis",
      "Infection of skin AND/OR subcutaneous tissue": "Skin infection", "Intestinal infectious disease": "Gastrointestinal infection",
      "Iron deficiency anemia": "Iron deficiency anaemia", "Multiple sclerosis": "Multiple sclerosis", "Proteinuria": "Proteinuria",
      "Seborrheic dermatitis": "Seborrhoeic dermatitis"}


def main():
    df = list(pyreadr.read_r(str(RUN / "data" / "raw" / "ohdsiNegativeControls.rds")).values())[0]
    rows = []
    for r in df.itertuples():
        pt = PT.get(r.outcomeName, "__unmapped__")
        assert pt != "__unmapped__", r.outcomeName
        if pt is None:
            continue
        for drug in (r.targetName, r.comparatorName):
            rows.append(dict(drug=str(drug).strip().lower(), pt=pt, source_outcome=r.outcomeName))
    out = pd.DataFrame(rows).drop_duplicates(["drug", "pt"])
    out.to_csv(RUN / "data" / "negative_controls.csv", index=False)
    print(len(out), "negative-control drug-PT pairs;", out.drug.nunique(), "drugs;", out.pt.nunique(), "PTs")


if __name__ == "__main__":
    main()
