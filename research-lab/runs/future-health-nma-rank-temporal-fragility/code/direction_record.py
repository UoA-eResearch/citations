"""D4 (review issue 3): a per-network record of the arm-level direction check behind D2. For every arm-level network:
the catalogue label, the sheet's own label, the outcome text, and, where a control arm is named (placebo, control,
no treatment, sham, standard/usual care, waitlist), the pooled control-arm outcome against the pooled other arms and
whether that is consistent with the call for an efficacy outcome. hand_checked marks the 60 networks adjudicated by
hand in D2 (data/validation/d2_handchecked_lists.txt). Writes results/tables/direction_arm_record.csv."""
import json
import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
CTRL = re.compile(r"placebo|placbeo|\bcontrol\b|no treatment|\bsham\b|standard care|usual care|wait", re.I)


def sheet_label(raw):
    for x in [str(v) for v in list(raw.columns) + raw.astype(str).values.ravel().tolist()]:
        t = x.strip().lower()
        if re.match(r"^(harm|harmful)\b", t):
            return "Harmful"
        if re.match(r"^(benefit|beneficial)\b", t):
            return "Beneficial"
    return ""


def main():
    dr = pd.read_csv(RUN / "results" / "tables" / "direction.csv", dtype={"record": str})
    cat = pd.read_csv(RUN / "data" / "raw" / "catalog.csv", sep=";", dtype=str).set_index("Record ID")
    lists = {l.split()[0]: set(l.split()[1:]) for l in open(RUN / "data" / "validation" / "d2_handchecked_lists.txt")}
    hand = lists.get("bin", set()) | lists.get("cont", set())
    jobs = {j["record"] for j in json.load(open(RUN / "data" / "jobs.json"))}
    rows = []
    for r in dr[(dr.format != "iv") & dr.record.isin(jobs)].itertuples():
        raw = pd.read_excel(RUN / "data" / "raw" / "datasets" / f"{r.record}.xlsx")
        d = pd.read_csv(RUN / "data" / "std" / f"{r.record}.csv")
        trt = json.load(open(RUN / "data" / "std" / f"{r.record}.trt.json"))
        ctrl = [int(k) for k, v in trt.items() if CTRL.search(v)]
        comp, consistent = "", ""
        if ctrl and "t" in d:
            val = (lambda g: g.r.sum() / g.n.sum()) if "r" in d and "time" not in d else (lambda g: (g.y * g.n).sum() / g.n.sum()) if "y" in d else (lambda g: g.r.sum() / g.time.sum())
            c, o = d[d.t.isin(ctrl)], d[~d.t.isin(ctrl)]
            if len(c) and len(o):
                vc, vo = float(val(c)), float(val(o))
                comp = f"control {vc:.3g} vs others {vo:.3g}"
                better_others = vo < vc if r.small_values == "good" else vo > vc
                consistent = "yes" if better_others else "no (check: safety outcome?)"
        rows.append(dict(record=r.record, catalogue=r.catalogue, sheet=sheet_label(raw), call=r.small_values, override=r.record == "501243",
                         hand_checked=r.record in hand, outcome=(str(cat.loc[r.record, "Primary Outcome"]) + " | " + str(cat.loc[r.record, "Description of the outcome(s)"]))[:160].replace("\n", " "),
                         control_comparison=comp, control_consistent_with_call=consistent))
    out = pd.DataFrame(rows)
    out.to_csv(RUN / "results" / "tables" / "direction_arm_record.csv", index=False)
    print(len(out), "arm-level networks;", int(out.hand_checked.sum()), "hand-checked;", int((out.control_comparison != "").sum()),
          "with a named control;", int((out.control_consistent_with_call == "yes").sum()), "consistent;",
          out[out.control_consistent_with_call.str.startswith("no")].record.tolist())


if __name__ == "__main__":
    main()
