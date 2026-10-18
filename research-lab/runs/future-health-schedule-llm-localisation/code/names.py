"""Ingredient-name normalisation, copied unchanged from runs/future-health-nz-medicine-access-lag/code/names.py."""
import re

SALTS = """hydrochloride hcl dihydrochloride trihydrochloride sodium disodium trisodium potassium dipotassium calcium
magnesium mesylate mesilate dimesylate maleate fumarate hemifumarate tartrate bitartrate citrate sulfate sulphate
bisulfate hemisulfate phosphate diphosphate dihydrogen acetate succinate besylate besilate tosylate tosilate bromide
hydrobromide chloride nitrate lactate malate benzoate monohydrate dihydrate trihydrate sesquihydrate hemihydrate
hydrate anhydrous dimeglumine meglumine tromethamine trometamol olamine choline lysine arginine esylate edisylate
xinafoate pamoate embonate oxalate gluconate glucuronate carbonate hydroxide hyclate monosodium free base
hemipentahydrate pentahydrate hemiheptahydrate tetrahydrate decanoate palmitate""".split()
SALT_RE = re.compile(r"\b(" + "|".join(SALTS) + r")\b")
DIAG_RE = re.compile(r"vaccine|\b(f|ga|tc|in|cu|zr|i|n|rb|o)[ -]?\d{2,3}\b|fluciclovine|flortaucipir|florbetaben|"
                     r"florbetapir|flutemetamol|piflufolastat|gadopiclenol|gadoterate|gadobutrol|gadoxetate|"
                     r"tuberculin|allergen|pollen|technetium|indocyanine|hexaminolevulinate|pafolacianine|"
                     r"perflutren|sulfur hexafluoride|regadenoson|tilmanocept", re.I)


def norm(s):
    s = (s or "").lower()
    # D8: fumarate esters are the active moiety's name, not a salt; keep them whole so "dimethyl fumarate" cannot
    # collapse to "dimethyl" and match dimethyl sulfoxide
    s = re.sub(r"\b(dimethyl|diroximel|monomethyl) fumarate\b", r"\1fumarate", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = SALT_RE.sub(" ", s)
    s = re.sub(r"[^a-z0-9 \-]", " ", s)
    s = re.sub(r"-[a-z]{4}\b", "", s)            # FDA biosimilar / biologic suffixes (adalimumab-atto)
    return re.sub(r"\s+", " ", s).strip(" -")


def components(s, sep=r";|/|\+|,| and | with "):
    s = s if isinstance(s, str) else ""
    return [c for c in (norm(x) for x in re.split(sep, s, flags=re.I)) if c]
