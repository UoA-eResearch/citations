"""H1 under alternative numerator/denominator decisions found in review: (a) as reported; (b) counting the two Gump
'Moorea Biocode 1.0' DOIs whose rightsList carries a BC Consent Verified Label's template text (rightsIdentifier
bc-consent / bc-label) with a live Hub project that has that Label applied (Hub API: bc_labels=[consent_verified]);
(c) adding the census false negative found by probing (10.48321/d190108951, Hub URI in relatedIdentifiers) to the
denominator. Appends to recomputed.json under 'H1_sensitivity'."""
import json
from pathlib import Path
from scipy import stats as st
HERE = Path(__file__).resolve().parent
def exact(k, n):
    return [0.0 if k == 0 else float(st.beta.ppf(0.025, k, n - k + 1)), 1.0 if k == n else float(st.beta.ppf(0.975, k + 1, n - k))]
def rule(ci):
    return "Supported" if ci[1] < 0.001 else "Refuted" if ci[0] >= 0.001 else "Inconclusive"
rows = {}
for name, k, n in [("as_reported_all", 1, 48361), ("as_reported_without_neotoma", 1, 29),
                   ("plus_biocode_label_template_all", 3, 48361), ("plus_biocode_label_template_without_neotoma", 3, 29),
                   ("plus_biocode_and_dmptool_fn_all", 3, 48362), ("plus_biocode_and_dmptool_fn_without_neotoma", 3, 30),
                   ("biocode_counted_as_one_object_without_neotoma", 2, 28)]:
    ci = exact(k, n); rows[name] = dict(k=k, n=n, share=k / n, exact_ci=ci, verdict=rule(ci))
    print(f"{name:48s} {k}/{n} = {100*k/n:.4f}%  CI {100*ci[0]:.4f}-{100*ci[1]:.3f}%  {rule(ci)}")
r = json.load(open(HERE / "recomputed.json")); r["H1_sensitivity"] = rows
json.dump(r, open(HERE / "recomputed.json", "w"), indent=1, default=str)
