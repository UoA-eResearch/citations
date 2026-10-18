"""Reviewer check 2: the reviewer's blind screen of all 100 NZ and all 100 AU counterfactuals (judged from
sheets/screen_*.txt BEFORE opening results/tables/nz_counterfactual_screen.csv), compared with the agent's NZ screen;
H3 recomputed under each screen; break-even analysis."""
import json, math
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]; OUT = RUN / "review/reviewer_checks"
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
# ---- reviewer's labels (E = equivalent restatement; O = overlapping: implied by / narrower or broader form of an own
# criterion; B = distinct but borderline under a literal reading of 'narrower form of an own indication'; else distinct)
NZ = {"E": {"0457": "tuberous sclerosis complex* vs own 'Patient has tuberous sclerosis'", "0466": "ECOG 0-2 (score vs status)",
            "0472": "treatment-limiting intolerance/toxicity to imatinib", "0477": "'remains' vs 'is' immunocompromised",
            "0506": "differs by 'the'", "0517": "ECOG 0-2 (patient vs individual)", "0532": "differs by 'the' (last 12 months)",
            "0533": "unable to adhere to oral atypical antipsychotics", "0538": "truncated form of own renewal criterion"},
      "O": {"0464": "own adds 'endocrine' (prior systemic endocrine treatment)", "0484": "moderate-to-high risk of IFI vs own 'at risk of IFI'",
            "0490": "no combination chemo vs own 'monotherapy only'", "0505": "treatment naive vs own 'previously untreated CLL/AML'",
            "0511": "unacceptable side effects disjunct of own criterion", "0520": "remains at moderate-to-high risk of IFI vs own 'at risk of IFI'",
            "0521": "at least one prior therapy vs own 'at least one prior immunochemotherapy'", "0526": "monotherapy vs own 'not in combination with other chemotherapy'",
            "0542": "narrower form of own 'not adequately controlled with other antiepilepsy agents'", "0545": "at risk of IFI vs own 'moderate to high risk of IFI'"},
      "B": {}}
AU = {"E": {"0984": "'this PBS indication' vs 'this condition'", "0998": "'this condition' vs 'this PBS indication'",
            "1001": "WHO performance status 2 or less (ECOG wording)", "0973": "sole PBS-subsidised (systemic anti-cancer) therapy"},
      "O": {"1041": "bone or joint infection vs own 'Osteomyelitis'", "0968": "first time vs own 'Initial treatment' phase",
            "1026": "not previously received this drug vs own 'Initial treatment' phase", "1036": "sole PBS-subsidised therapy vs own 'monotherapy' (D5 case)",
            "1031": "5-year lifetime cap vs own note on 5 years", "0989": "not with chemotherapy/novel hormonal drug vs own 'monotherapy'",
            "1040": "inoperable vs own 'surgery inappropriate'/'unresectable'", "0990": "Metastatic breast cancer vs own indication 'Breast cancer'",
            "0961": "initial authority prescription vs own 'previous PBS-subsidised treatment ... first line maintenance'",
            "0966": "no disease recurrence vs own 'no disease progression while receiving treatment'"},
      "B": {"0964": "no other CDK4/6 inhibitor - implied by own 'sole PBS-subsidised therapy' but alien class", "1024": "oesophageal candidiasis under own broad indication 'Fungal infection'",
            "1034": "systemic aspergillosis under own broad indication 'Fungal or yeast infection'"}}
items = [json.loads(l) for l in open(RUN / "data/items.jsonl")]
rows = []
for jur, lab in (("NZ", NZ), ("AU", AU)):
    for x in items:
        if x["jurisdiction"] == jur and x["family"] == "d" and x["answer"] == "no":
            n = x["id"].split("-")[-1]
            s, note = ("equivalent", lab["E"][n]) if n in lab["E"] else ("overlapping", lab["O"][n]) if n in lab["O"] else ("distinct", "borderline: " + lab["B"][n]) if n in lab["B"] else ("distinct", "")
            rows.append(dict(id=x["id"], jurisdiction=jur, chemical=x["chemical"], source_chemical=x["source_chemical"], reviewer_screen=s, reviewer_note=note))
rv = pd.DataFrame(rows); rv.to_csv(OUT / "reviewer_cf_screen.csv", index=False)
print("reviewer screen counts:", rv.groupby(["jurisdiction", "reviewer_screen"]).size().to_dict())
# ---- compare with the agent's NZ screen (opened only now)
ag = pd.read_csv(RUN / "results/tables/nz_counterfactual_screen.csv")
m = rv[rv.jurisdiction == "NZ"].merge(ag[["id", "screen", "note"]], on="id")
m["agent_nd"] = m.screen != "distinct"; m["rev_nd"] = m.reviewer_screen != "distinct"
print("\nagent counts:", ag.screen.value_counts().to_dict())
print("agreement on distinct vs not:", (m.agent_nd == m.rev_nd).mean(), f"({(m.agent_nd == m.rev_nd).sum()}/100)")
print("exact 3-way label agreement:", (m.screen == m.reviewer_screen).mean())
print("\nDISAGREEMENTS (distinct vs non-distinct):")
dis = m[m.agent_nd != m.rev_nd]
print(dis[["id", "chemical", "screen", "reviewer_screen", "reviewer_note", "note"]].to_string())
print("\nTier disagreements (both non-distinct, different tier):")
print(m[m.agent_nd & m.rev_nd & (m.screen != m.reviewer_screen)][["id", "screen", "reviewer_screen", "reviewer_note"]].to_string())
# ---- H3 under each screen
rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data/runs.jsonl")])
z = rn[rn.condition == "zero"].set_index("id").answer
def h3(ids, label):
    k = int((z[list(ids)] == "yes").sum()); n = len(ids); lo, hi = wilson(k, n)
    v = "Supported" if lo >= 0.2 else "Refuted" if hi < 0.2 else "Inconclusive"
    print(f"{label:48s} affirmed {k:3d}/{n:3d} = {k/n:.3f}  Wilson ({lo:.3f}, {hi:.3f})  -> {v}")
    return k, n, lo
nz = m.set_index("id")
print("\n== H3 (NZ, zero-shot) under alternative screens ==")
h3(nz.index, "all 100 (preregistered)")
h3(nz[~nz.agent_nd].index, "agent's 83 distinct")
h3(nz[~nz.rev_nd].index, f"reviewer's {int((~nz.rev_nd).sum())} distinct")
h3(nz[~(nz.agent_nd | nz.rev_nd)].index, f"distinct under BOTH screens ({int((~(nz.agent_nd | nz.rev_nd)).sum())})")
h3(nz[~(nz.agent_nd & nz.rev_nd)].index, f"distinct under EITHER screen ({int((~(nz.agent_nd & nz.rev_nd)).sum())})")
h3(nz[nz.agent_nd].index, "agent's 17 non-distinct"); h3(nz[nz.rev_nd].index, f"reviewer's {int(nz.rev_nd.sum())} non-distinct")
print("affirmed among reviewer's non-distinct by tier:", nz[nz.rev_nd].assign(yes=lambda t: z[t.index].values == "yes").groupby("reviewer_screen").yes.agg(["size", "sum"]).to_dict())
# break-even: how many more AFFIRMED distinct items would have to be reclassified for the screened lower bound to fall below 0.20?
base = nz[~(nz.agent_nd | nz.rev_nd)].index; k = int((z[list(base)] == "yes").sum()); n = len(base)
for drop in range(0, 20):
    lo, hi = wilson(k - drop, n - drop)
    if lo < 0.2:
        print(f"break-even: removing {drop} more affirmed items from the {n}-item both-screens set ({k - drop}/{n - drop}) drops the Wilson lower bound to {lo:.3f} < 0.20"); break
print("\n== AU (unscreened in the study) under the reviewer's screen ==")
au = rv[rv.jurisdiction == "AU"].set_index("id")
h3(au.index, "AU all 100"); h3(au[au.reviewer_screen == "distinct"].index, f"AU reviewer-distinct ({int((au.reviewer_screen=='distinct').sum())})")
h3(au[au.reviewer_screen != "distinct"].index, f"AU reviewer non-distinct ({int((au.reviewer_screen!='distinct').sum())})")
h3(au[(au.reviewer_screen == "distinct") & ~au.reviewer_note.str.startswith("borderline")].index, "AU distinct excl. borderline")
