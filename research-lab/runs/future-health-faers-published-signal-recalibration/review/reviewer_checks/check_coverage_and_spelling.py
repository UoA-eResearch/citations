"""Reviewer checks 3 and 2: (a) drugname-only matching before 2014Q3 - for the 15 most frequent signal ingredients, PS
reports per quarter 2012Q4-2016Q2 matched by the pipeline's regex on drugname alone vs on prod_ai, to see the
discontinuity at 2014Q3 when prod_ai starts; (b) how many 'event not a FAERS PT' failures a fuller US->UK spelling map
or trivial normalisation (strip parentheses, hyphens) would have rescued; (c) survival among PT-drift-affected signals."""
import re, sys
from pathlib import Path
import duckdb, numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import rxnorm
from recompute import terms_for, pattern
from eligible import uk
OUT = Path(__file__).resolve().parent
db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True); db.execute("SET threads TO 8")
e = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
# (a)
db.execute("""CREATE TEMP TABLE ps1216 AS SELECT dr.rid, dr.drugname, dr.prod_ai, d.quarter FROM drug dr JOIN demo d USING (rid)
              WHERE dr.role = 'PS' AND d.quarter >= '2012Q4' AND d.quarter <= '2016Q2'""")
top = e.ingredient.value_counts().head(15).index.tolist()
rows = []
for ing in top:
    drug = e[e.ingredient == ing].drug.iloc[0]
    p = pattern(terms_for(ing, drug)).replace("'", "''")
    r = db.execute(f"""SELECT quarter, count(DISTINCT CASE WHEN regexp_matches(coalesce(drugname,''), '{p}') THEN rid END) by_name,
                              count(DISTINCT CASE WHEN regexp_matches(coalesce(prod_ai,''), '{p}') THEN rid END) by_ai,
                              count(DISTINCT CASE WHEN regexp_matches(coalesce(drugname,''), '{p}') OR regexp_matches(coalesce(prod_ai,''), '{p}') THEN rid END) either
                       FROM ps1216 GROUP BY quarter ORDER BY quarter""").fetchall()
    for q, bn, ba, ei in r: rows.append(dict(ingredient=ing, quarter=q, by_name=bn, by_ai=ba, either=ei))
cov = pd.DataFrame(rows); cov.to_csv(OUT / "drugname_coverage_2012Q4_2016Q2.csv", index=False)
post = cov[cov.quarter >= "2014Q3"]
summ = post.groupby("ingredient").apply(lambda g: pd.Series(dict(name_only_share=g.by_name.sum() / g.either.sum(), ai_share=g.by_ai.sum() / g.either.sum(), n=g.either.sum())))
print("Share of PS reports (2014Q3-2016Q2, when both fields exist) that the drugname regex alone would catch:")
print(summ.round(3).sort_values("name_only_share").to_string())
print("weighted mean name-only share:", round((post.by_name.sum() / post.either.sum()), 3))
# (b)
a = pd.read_csv(RUN / "data" / "signals_all.csv", dtype={"paper": str})
pts = {r[0] for r in db.execute("SELECT DISTINCT pt FROM reac").fetchall()}
EXTRA = [(r"(?<![a-z])anemi", "anaemi"), (r"(?<!o)edema", "oedema"), (r"prolactinemi", "prolactinaemi"), (r"gynecomast", "gynaecomast"),
         (r"phosphatemi", "phosphataemi"), (r"calcemi", "calcaemi"), (r"magnesemi", "magnesaemi"), (r"bilirubinemi", "bilirubinaemi"),
         (r"lipidemi", "lipidaemi"), (r"cholesterolemi", "cholesterolaemi"), (r"uricemi", "uricaemi"), (r"albuminemi", "albuminaemi"),
         (r"(?<!o)esthesi", "aesthesi"), (r"hemat", "haemat"), (r"hemopt", "haemopt"), (r"hemang", "haemang"), (r"hemoph", "haemoph"),
         (r"hemodia", "haemodia"), (r"hemost", "haemost"), (r"hemoper", "haemoper"), (r"hemothor", "haemothor"), (r"hyperemi", "hyperaemi"),
         (r"(?<!o)rrhea", "rrhoea"), (r"cesarean", "caesarean"), (r"celiac", "coeliac"), (r"fetus", "foetus"), (r"ameb", "amoeb"),
         (r"volemi", "volaemi"), (r"oxemi", "oxaemi"), (r"azotemi", "azotaemi"), (r"toxemi", "toxaemi"), (r"viremi", "viraemi"),
         (r"\bthrombocythemia", "thrombocythaemia"), (r"polycythemi", "polycythaemi"), (r"gonorrhea", "gonorrhoea"), (r"leukoderma", "leucoderma"),
         (r"hemiparesis", "hemiparesis")]
def uk2(s):
    s = uk(s)
    for p, q in EXTRA: s = re.sub(p, q, s)
    return s
def norm(s):
    s = re.sub(r"\s*\([^)]*\)", "", s); s = s.replace("-", " "); return re.sub(r"\s+", " ", s).strip()
npt = a[a.reason == "event not a FAERS PT"].copy()
npt["uk2"] = npt.event.map(uk2); npt["uk2_norm"] = npt.uk2.map(norm)
npt["rescued_spelling"] = npt.uk2.str.upper().isin(pts) & ~npt.event_uk.str.upper().isin(pts)
npt["rescued_norm"] = npt.uk2_norm.str.upper().isin(pts) & ~npt.rescued_spelling & ~npt.event_uk.str.upper().isin(pts)
print(f"\n'event not a FAERS PT': {len(npt)} signals in {npt.paper.nunique()} papers")
print("rescued by a fuller spelling map:", int(npt.rescued_spelling.sum()), "|", npt[npt.rescued_spelling].uk2.value_counts().to_dict())
print("rescued by stripping parentheses/hyphens:", int(npt.rescued_norm.sum()), "|", npt[npt.rescued_norm].uk2_norm.value_counts().to_dict())
# the eligible-but-non-PT signals that are plainly PT-level with a different MedDRA name (hand list, for information)
npt[["paper", "drug", "event", "event_uk", "uk2", "rescued_spelling", "rescued_norm", "estimate", "ci_low"]].to_csv(OUT / "non_pt_events.csv", index=False)
# does the UK map misfire on any eligible event? ('color'->'colour' etc.)
mis = a[(a.reason == "event not a FAERS PT") & a.event.str.lower().str.contains("color|sulfa|fetal|behavior")]
print("map entries firing on non-medical words among non-PT failures:", len(mis), mis.event.tolist()[:10])
# (c) survival among PT-drift-affected signals
d = pd.read_csv(OUT / "pt_version_drift.csv", dtype={"paper": str})
d["affected"] = d.pt_first_after_start | d.pt_last_before_end
print("\nPT-drift affected:", int(d.affected.sum()), "survival", round(d[d.affected].primary_survive_mle.mean(), 3), "| unaffected survival", round(d[~d.affected].primary_survive_mle.mean(), 3))
