"""Which direction is good, per network (D2), adjudicated before any fit. Writes results/tables/direction.csv.

small_values = "good" means a lower outcome (arm-level) or a negative effect as given (contrast-level, entered into
netmeta as TE = treat1 vs treat2) favours the treatment with the lower value / treat1.

Arm-level networks: the catalogue's Harmful/Beneficial label, checked against the outcome description, the sheet's
own label and the arm data for every network where the two labels disagree or the sheet has none (60 binary/rate
and all 30 continuous). One catalogue label is wrong (501243, heavy bleeding, labelled Beneficial).

Contrast-level (iv) networks: the label names the outcome concept ("overall survival" is Beneficial) while the effect
is often a hazard of the event, and the sheets do not say whether effect is t1 vs t2 or t2 vs t1; both conventions
occur. Each is adjudicated from placebo-controlled contrasts (an active drug beats placebo on an efficacy outcome),
the sheet's notes, and landmark trials whose published estimates appear in the data."""
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]

ARM_OVERRIDE = {"501243": ("good", "outcome is heavy bleeding at 12 months (harmful); catalogue says Beneficial, the sheet says Harmful")}

IV = {  # record: (small_values, confidence, basis)
    "479757": ("good", "high", "OS HR, combinations as t1 vs gemcitabine; Gem+nab-paclitaxel -0.33 = log 0.72 (MPACT), so effect = t1 vs t2"),
    "479888": ("good", "high", "OS HR; FOLFIRINOX vs gemcitabine -0.56 = log 0.57 (PRODIGE 4), effect = t1 vs t2"),
    "479911": ("good", "high", "OS HR; sheet states HR (t1 vs t2); hazard of death"),
    "479914": ("good", "medium", "FVC outcome; pirfenidone and nintedanib (t1) vs placebo (t2) negative, consistent with less FVC decline"),
    "480611": ("good", "high", "radiographic erosion progression (harmful); combinations (t1) vs DMARD/GC negative"),
    "480617": ("good", "medium", "OS HR; MOPP and C(M)OPP/EBV/CAD (t1) vs ABVD positive, consistent with ABVD's known advantage over MOPP"),
    "480679": ("good", "high", "cognition (ADAS-cog type, lower better); cholinesterase inhibitors (t1) vs placebo (t2) negative"),
    "480693": ("bad", "high", "PASI 75 risk difference; actives (t1) vs placebo (t2) +0.25 to +0.65"),
    "482117": ("good", "high", "antidepressants (t1) vs placebo (t2) SMD negative on symptom change"),
    "482415": ("good", "high", "allergic rhinitis symptom scores; immunotherapies (t1) vs placebo (t2) negative"),
    "482760": ("bad", "high", "response (>=50% reduction) log OR; placebo (t1) vs active (t2) negative"),
    "501200": ("bad", "medium", "PGA clearing OR (natural scale, logged); biologics (t1) vs placebo (t2) OR 3.8-80"),
    "501211": ("good", "high", "IIEF (higher better); placebo is t1 and effect +9.7, so effect = drug vs placebo (t2 vs t1)"),
    "501216": (None, "undetermined", "psychotherapies only, no placebo or waitlist node; sign convention cannot be determined - excluded"),
    "501220": ("good", "high", "recession reduction (higher better); CAF (t1) vs CAF+CTG (t2) +0.44/+0.52, CTG known to add ~0.4 mm, so effect = t2 vs t1"),
    "501237": ("good", "high", "trough FEV1 (higher better); placebo is t1 and effect +100 to +153 mL, so effect = drug vs placebo"),
    "501244": ("bad", "high", "HR of no relapse at 1 year (already log; sheet's HR column 1.24 = exp 0.215); interferon (t1) vs placebo (t2) above 1"),
    "501274": ("good", "high", "OS HR; FIB (t1) vs FI (t2) -0.42 = log 0.66 (Hurwitz 2004), effect = t1 vs t2"),
    "501308": ("good", "high", "OS HR; McGuire +0.51 = log(1/0.60), Alberts +0.26 = log(1/0.76), Armstrong +0.29 = log(1/0.75): effect = t1 vs t2"),
    "501319": ("good", "high", "FEV1 % change (higher better); placebo is t1 and effect +6 to +24, so effect = drug vs placebo"),
    "501320": ("bad", "medium", "response log OR (sheet: effect = log(OR)); TCA (t1) vs SSRI (t2) positive, consistent with t1 vs t2"),
    "501333": ("good", "medium", "mortality HR; low-dose (t1) vs standard-dose (t2) anthracycline slightly positive, consistent with t1 vs t2"),
    "501339": ("good", "high", "OS HR; sheet states HR drug vs placebo; drugs are t1"),
    "501354": ("bad", "high", "hot flash frequency (lower better); placebo is t1 and effect mostly negative, so effect = drug vs placebo"),
    "501364": ("good", "high", "clinical response (log scale); placebo is t1 and effect positive, so effect = drug vs placebo"),
    "501378": ("bad", "medium", "responder log RR (already log: values are logs of round ratios, 1.791759 = ln 6); drugs (t1) vs placebo (t2) positive"),
    "501400": ("bad", "high", "OS HR; gemcitabine is t1 and combinations t2 with -0.2: effect = combination vs gemcitabine (t2 vs t1)"),
    "501403": ("bad", "high", "OS HR; CLL8 row (FC t1, FCR t2) -0.40 = log 0.67, the published FCR vs FC HR: effect = t2 vs t1"),
    "501410": ("good", "medium", "PPD reduction (higher better); EMD (t1) vs flap surgery (t2) -0.1 to -2.7, so effect = t2 vs t1"),
    "501426": ("good", "high", "healing log OR; placebo is t1 and effect mostly positive, so effect = drug vs placebo"),
}


def main():
    s = pd.read_csv(RUN / "data" / "std_summary.csv", dtype={"record": str})
    s = s[s.parsed & (s.measure != "other")]
    rows = []
    for r in s.itertuples():
        if r.format == "iv":
            sv, conf, basis = IV.get(r.record, (None, "not adjudicated", "not in the size/year-eligible set"))
        elif r.record in ARM_OVERRIDE:
            sv, basis = ARM_OVERRIDE[r.record]; conf = "high"
        else:
            sv = "good" if r.direction == "Harmful" else "bad"; conf = "high"; basis = "catalogue label (checked where labels disagree or the sheet has none)"
        rows.append(dict(record=r.record, format=r.format, type=r.type, catalogue=r.direction, small_values=sv, confidence=conf, basis=basis))
    pd.DataFrame(rows).to_csv(RUN / "results" / "tables" / "direction.csv", index=False)
    d = pd.DataFrame(rows)
    print(d.groupby(["format", "confidence"]).size().to_string())


if __name__ == "__main__":
    main()
