"""Confirmation pass: read the post-D10 limb-2 tables and the pre-D10 copies, and recompute the key figures from
limb2_rows.csv independently of score.py."""
import json
import math
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[2]
TAB = RUN / "results" / "tables"


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


P = json.load(open(TAB / "limb2_primary.json"))
print("H2:", P["H2"], "| scored/tune/test:", P["scored"], P["tune"], P["test"])
print("labels:", P["labels"])
print("labels_by_stratum:", P["labels_by_stratum"])
print("gold_countries:", P["gold_countries"])
for a, v in P["arms"].items():
    t = v["test"]; q = v["test_any_confidence"]
    print(f"{a:10s} tuning={v['tuning']} test: calls={t['predictions']} correct={t['correct']} rec={t['recovery']} "
          f"ci={t['recovery_ci']} det={t['determinable']} | any: calls={q['predictions']} correct={q['correct']} "
          f"rec={q['recovery']} prec={q['precision']} recall={q['recall_of_determinable']}")

S = json.load(open(TAB / "limb2_secondary.json"))
print("\npopulation:", S["population_untagged"])
for c, v in S["projection_label_shares"].items():
    print(f"projection {c:13s} share={v['share_of_untagged']} ci={v['share_ci']} samples={v['samples']} ci={v['ci']} strata={v['strata']}")
print("gold==submitter:", S["gold_country_equals_submitter_country"])
for a in ("gazetteer", "classifier", "llm"):
    r = S["asymmetric_error"][a]["all_records_any_confidence"]
    print(f"asym {a:10s} all-records: {r['naming_submitter_country']}/{r['errors_with_submitter_country']} share={r['share']} ci={r['share_ci']}")
print("brier:", {a: v.get("brier") for a, v in S["calibration"].items()})

N = json.load(open(TAB / "limb2_posthoc_natural.json"))
for s in ("all", "test"):
    o = N[s]
    print(f"\nposthoc {s}: natural={o['natural_records']} det={o['determinable']} ceiling={o['ceiling']} ci={o['ceiling_ci']}")
    for a, v in o["arms_any_confidence"].items():
        print(f"   {a:10s} calls={v['predictions']} correct={v['correct']} prec={v['precision']} ci={v['precision_ci']} recall={v['recall_of_determinable']}")

D = json.load(open(TAB / "decomposition_limb2.json"))
print("\ndecomposition cbd:", {k: (v["n"], v["share"]) for k, v in D["gold_countries"]["cbd"].items()})

# pre-D10 copies exist and hold the old values?
for f in ("limb2_primary_pre_d10.json", "limb2_secondary_pre_d10.json", "limb2_posthoc_natural_pre_d10.json",
          "decomposition_limb2_pre_d10.json", "limb2_rows_pre_d10.csv"):
    print("pre_d10 file present:", f, (TAB / f).exists())
PP = json.load(open(TAB / "limb2_primary_pre_d10.json"))
print("pre_d10 labels:", PP["labels"]["all"], "| classifier test:", PP["arms"]["classifier"]["test"]["recovery"],
      "| det:", PP["arms"]["classifier"]["test"]["determinable"])

# independent recomputation from limb2_rows.csv
rows = pd.read_csv(TAB / "limb2_rows.csv", keep_default_na=False)
pre = pd.read_csv(TAB / "limb2_rows_pre_d10.csv", keep_default_na=False)
ND = "not determinable"
changed = rows.merge(pre, on="record", suffixes=("", "_pre"))
ch = changed[changed.label != changed.label_pre]
print("\nrecords whose label changed vs pre_d10:", sorted(ch.record.tolist()))
print("  all now 'not stated'?:", (ch.label == "not stated").all(), "| old labels:", ch.label_pre.tolist())
test = rows[rows.split == "test"]
det = int((test.gold != ND).sum())
print("test determinable (recomputed):", det, "of", len(test), "=", round(det / len(test), 4), wilson(det, len(test)))
coarse = rows.label.map(lambda l: l if l in ("inapplicable", "not stated") else "country")
print("labels 497 (recomputed):", coarse.value_counts().to_dict())
pop = S["population_untagged"]; Nn = pop["with_publication"] + pop["without_publication"]
for cls in ("inapplicable", "not stated", "country"):
    tot = var = 0.0
    for h, key in ((True, "with_publication"), (False, "without_publication")):
        s = rows[rows.has_pub.astype(str) == str(h)]
        p = (s.label.map(lambda l: l if l in ("inapplicable", "not stated") else "country") == cls).mean()
        tot += pop[key] * p; var += pop[key] ** 2 * p * (1 - p) / len(s)
    se = math.sqrt(var)
    print(f"projection {cls:13s} recomputed share={tot / Nn:.4f} ci=[{(tot - 1.96 * se) / Nn:.4f}, {(tot + 1.96 * se) / Nn:.4f}] samples={tot:.0f}")
nat = rows[rows.label != "inapplicable"]
print("natural all:", len(nat), "det", int((nat.gold != ND).sum()), "ceiling", round((nat.gold != ND).mean(), 4))
m = nat[nat.llm != ""]
print("LLM natural-all calls/correct:", len(m), int((m.llm == m.gold).sum()))
mt = test[test.llm != ""]
print("LLM test any-conf calls/correct:", len(mt), int((mt.llm == mt.gold).sum()))
# CBD comparison figure: publication-linked stratum with a country
wp = rows[rows.has_pub.astype(str) == "True"]
print("publication-linked records with a country label:", int((wp.gold != ND).sum()), "of", len(wp),
      sorted(wp.record[wp.gold != ND].tolist()))
