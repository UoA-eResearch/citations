"""D3.2: cross-check T2 (this study's Medsafe crawl) against the independent Medsafe register snapshot in
UoA-eResearch/pharmac (wildcard scrape, 2026-03-30). For every cohort substance not excluded as old, T2_register = the
earliest approval date among register products whose active ingredients contain the substance, with the same status
filter as link.py. Agreement = both absent, or both present within 31 days. Products approved after 2026-03-30 cannot
be in the snapshot, so substances whose crawl T2 is later are reported separately. Writes
results/tables/medsafe_crosscheck.json and data/medsafe_crosscheck.csv."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from link import CONSENTED, has_any  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
SNAP = pd.Timestamp("2026-03-30")


def main():
    d = pd.read_csv(RUN / "data" / "linked.csv", parse_dates=["t2"])
    d = d[~d.excluded_old]
    reg = pd.read_csv(RUN / "data" / "raw" / "uoa_pharmac" / "medsafe_register.csv", dtype=str)
    reg = reg[reg.Status.isin(CONSENTED)].copy()
    reg["date"] = pd.to_datetime(reg["Approval date"], dayfirst=True, errors="coerce")
    rows = []
    for r in d.itertuples():
        pats = str(r.match_names).split("|")
        m = reg[reg["Active ingredients"].map(lambda x: has_any(pats, x))]
        t2r = m.date.min() if len(m) else pd.NaT
        rows.append(dict(substance=r.substance, t2=r.t2, t2_register=t2r))
    x = pd.DataFrame(rows)
    comparable = x[~(x.t2.notna() & (x.t2 > SNAP))]
    both = comparable.t2.notna() & comparable.t2_register.notna()
    agree = (comparable.t2.isna() & comparable.t2_register.isna()) | (both & ((comparable.t2 - comparable.t2_register).dt.days.abs() <= 31))
    out = dict(n=int(len(x)), after_snapshot=int(len(x) - len(comparable)), comparable=int(len(comparable)), agree=int(agree.sum()),
               agreement=float(agree.mean()), both_present=int(both.sum()),
               crawl_only=int((comparable.t2.notna() & comparable.t2_register.isna()).sum()),
               register_only=int((comparable.t2.isna() & comparable.t2_register.notna()).sum()),
               both_differ_gt_31d=int((both & ((comparable.t2 - comparable.t2_register).dt.days.abs() > 31)).sum()))
    x.assign(agree=agree.reindex(x.index)).to_csv(RUN / "data" / "medsafe_crosscheck.csv", index=False)
    json.dump(out, open(RUN / "results" / "tables" / "medsafe_crosscheck.json", "w"), indent=1)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
