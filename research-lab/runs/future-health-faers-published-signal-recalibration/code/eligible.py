"""Eligible published signals (plan section 2). From data/extract/signals_raw.jsonl: ROR with estimate and 95% CI,
lower bound > 1, a single active ingredient (RxNorm), a stated window, and an event name (after the fixed US-to-UK
spelling map) that is a PT in the FAERS reaction table (deviation D3: checked here, before the cap). At most 5 per paper, at random
(seed 20261018). Deviation D2: reads the v2 extraction (data/extract/signals_raw_v2.jsonl) and also requires the
signal's database to be FAERS and its comparison not to be an interaction; the comparison label is carried for the
all-drugs-only sensitivity analysis. Writes data/signals_all.csv (every extracted ROR signal with its eligibility
reason) and data/signals_eligible.csv."""
import json
import random
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rxnorm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
UK = [(r"hemorrhag", "haemorrhag"), (r"\banemi", "anaemi"), (r"\bedema", "oedema"), (r"diarrhea", "diarrhoea"), (r"(?<!o)esophag", "oesophag"),
      (r"tumor", "tumour"), (r"leukemi", "leukaemi"), (r"ischemi", "ischaemi"), (r"hematom", "haematom"), (r"hematur", "haematur"),
      (r"hemoly", "haemoly"), (r"hemoglobin", "haemoglobin"), (r"pediatric", "paediatric"), (r"apnea", "apnoea"), (r"dyspnea", "dyspnoea"),
      (r"hypoglycemi", "hypoglycaemi"), (r"hyperglycemi", "hyperglycaemi"), (r"glycemi", "glycaemi"), (r"kalemi", "kalaemi"),
      (r"natremi", "natraemi"), (r"cecum", "caecum"), (r"orthopedic", "orthopaedic"), (r"(?<!o)estrogen", "oestrogen"), (r"fetal", "foetal"),
      (r"sulfa", "sulpha"), (r"color", "colour"), (r"behavior", "behaviour"), (r"gynecolog", "gynaecolog"), (r"septicemi", "septicaemi"),
      (r"bacteremi", "bacteraemi"), (r"uremi", "uraemi"), (r"lipemi", "lipaemi"), (r"anesthe", "anaesthe"), (r"hematotox", "haematotox"),
      (r"neutropeni", "neutropeni")]


def uk(event):
    s = (event or "").strip().lower()
    for a, b in UK:
        s = re.sub(a, b, s)
    return s


def main():
    rows = []
    for l in open(RUN / "data" / "extract" / "signals_raw_v2.jsonl"):   # D2
        r = json.loads(l)
        if "out" not in r:
            continue
        w = r["out"].get("window")
        for k, s in enumerate(r["out"].get("signals") or []):
            if s.get("measure") != "ROR":
                continue
            reason = ""
            if s.get("estimate") is None or s.get("ci_low") is None or s.get("ci_high") is None:
                reason = "no estimate/CI"
            elif not (s["ci_low"] > 1):
                reason = "not significant as reported"
            elif not w:
                reason = "no window"
            elif s.get("database") != "FAERS":   # D2
                reason = "not FAERS"
            elif s.get("comparison") == "interaction":   # D2
                reason = "interaction or factor contrast"
            ings = rxnorm.ingredients(s.get("drug", "")) if not reason else []
            if not reason and len(ings) != 1:
                reason = "not a single mapped ingredient" if ings else "drug not mapped"
            rows.append(dict(paper=r["id"], k=k, drug=s.get("drug"), ingredient=ings[0] if len(ings) == 1 else "", event=s.get("event"),
                             event_uk=uk(s.get("event")), level=s.get("level"), estimate=s.get("estimate"), ci_low=s.get("ci_low"),
                             ci_high=s.get("ci_high"), n_cases=s.get("n_cases"), comparison=s.get("comparison"), database=s.get("database"),
                             win=f"{w['start_year']}Q{w['start_quarter']}-{w['end_year']}Q{w['end_quarter']}" if w else "", reason=reason))
    rxnorm.save()
    a = pd.DataFrame(rows)
    a.to_csv(RUN / "data" / "signals_all.csv", index=False)
    # D3: rule 4 (the event is a FAERS PT) is checked here, before the per-paper cap, as the plan orders it
    db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=True)
    pts = {r[0] for r in db.execute("SELECT DISTINCT pt FROM reac").fetchall()}
    db.close()
    a.loc[(a.reason == "") & ~a.event_uk.fillna("").str.upper().isin(pts), "reason"] = "event not a FAERS PT"
    a.to_csv(RUN / "data" / "signals_all.csv", index=False)
    e = a[a.reason == ""].copy()
    rnd = random.Random(20261018)
    keep = []
    for p, g in e.groupby("paper", sort=True):
        idx = list(g.index)
        keep += sorted(rnd.sample(idx, min(5, len(idx))))
    e = e.loc[keep]
    e.to_csv(RUN / "data" / "signals_eligible.csv", index=False)
    print(len(a), "ROR signals;", a.reason.value_counts().to_dict(), ";", len(e), "kept after the per-paper cap,", e.paper.nunique(), "papers")


if __name__ == "__main__":
    main()
