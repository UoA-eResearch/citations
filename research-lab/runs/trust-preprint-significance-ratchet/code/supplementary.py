"""Exploratory supplements (deviations D3-D4), all descriptive. Reads the two blind validations and the v1 pipeline.

  verified     every crossing a blind validation judged correct (v1 sample: 12 of 100; v2 census: 42 of 64),
               deduplicated across the two samples by (pair, preprint p, published p); share up with the exact
               interval and a paper bootstrap
  kinds        what the verified crossings are, from the adjudication notes: data changed, re-analysis, a correction or
               typo, a reversed conclusion, or values that look permuted across labels
  failures     why the rejected crossings failed (crossing stratum only), from the notes: extraction, reordered list, fragment, table / legend
               misalignment, different statistic
  S1 interval  paper bootstrap of share significant among added minus dropped statistics (v1 extraction, v1 population)
Writes results/tables/supplementary.json.
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_v2 import clopper, direction_of  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
V, TAB = RUN / "data" / "validation", RUN / "results" / "tables"
SEED, NBOOT = 20261017, 2000


def verified():
    out = []
    for tag, sample, val in (("v1", "sample.jsonl", "alignment_validation.csv"), ("v2", "sample_v2.jsonl", "alignment_validation_v2.csv")):
        s = {json.loads(l)["id"]: json.loads(l) for l in open(V / sample)}
        v = pd.read_csv(TAB / val)
        for r in v[v.stratum == "crossing"].itertuples():
            x = s[r.id]
            pre, pub = (x["stat_1"], x["stat_2"]) if int(r.pre_is) == 1 else (x["stat_2"], x["stat_1"])
            a, b = direction_of(pre), direction_of(pub)
            out.append(dict(sample=tag, id=r.id, pair=r.pair, correct=int(r.correct), note=str(r.note) if pd.notna(r.note) else "",
                            pre=pre, pub=pub, up=bool(a is False and b is True)))
    return pd.DataFrame(out)


def kind(note):
    n = note.lower()
    for k, keys in (("values look permuted", ("permuted",)),
                    ("correction or typo", ("typo", "contradicts", ".46", "value changed", "value differs", "corrected")),
                    ("conclusion reversed", ("reversed",)),
                    ("data changed", ("data changed", "more patients", "dataset replaced", "species set", "n 15")),
                    ("re-analysis", ("re-analysed", "re-estimated", "test changed", "category added", "trend"))):
        if any(k2 in n for k2 in keys):
            return k
    return "changed, reason not stated"


def failure(note):
    n = note.lower()
    if n == "different statistic / table or legend misaligned":     # the batch default note does not separate the two
        return "different statistic or table/legend row (not separated)"
    for k, keys in (("extraction (encoding, decimals, typos, effect sizes)", ("mojibake", "middle-dot", "comma", "eta2p", "exponent",
                                                                             "typo", "broken decimal", "<=")),
                    ("reordered list or shifted rank", ("reorder", "shifted", "rank", "dropped", "adjacent", "same sentence")),
                    ("fragment too short to identify", ("fragment",)),
                    ("table or legend misaligned", ("table", "legend"))):
        if any(k2 in n for k2 in keys):
            return k
    return "different statistic"


def paper_boot(df):
    g = df.groupby("pair").up.agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = np.random.default_rng(SEED).integers(0, len(g), size=(NBOOT, len(g)))
    v = s[idx].sum(1) / n[idx].sum(1)
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def main():
    d = verified()
    ok = d[d.correct == 1].copy()
    ok["key"] = ok.pair + "|" + ok.pre + "|" + ok.pub
    comb = ok.drop_duplicates("key")
    out = dict(verified={})
    for name, g in (("v1_sample", ok[ok["sample"] == "v1"]), ("v2_census", ok[ok["sample"] == "v2"]), ("combined", comb)):
        k, n = int(g.up.sum()), len(g)
        out["verified"][name] = dict(n=n, n_papers=int(g.pair.nunique()), up=k, share_up=k / n, exact_ci=list(clopper(k, n)),
                                     paper_boot_ci=paper_boot(g))
    out["overlap_v1_v2"] = int(len(ok) - len(comb))
    comb = comb.assign(kind=comb.note.map(kind))
    out["kinds"] = {k: dict(n=int(len(g)), up=int(g.up.sum())) for k, g in comb.groupby("kind")}
    bad = d[d.correct == 0].assign(failure=lambda x: x.note.map(failure))      # rejected crossings only
    out["failures"] = {s: bad[bad["sample"] == s].failure.value_counts().to_dict() for s in ("v1", "v2")}
    # S1 interval, v1 extraction and v1 population (the preregistered secondary)
    pairs = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "aligned" / "pairs.jsonl")])
    v1 = set(pairs[pairs.version_used.astype(str) == "1"].preprint_doi)
    rows = []
    for l in gzip.open(RUN / "data" / "aligned" / "statistics.jsonl.gz", "rt"):
        r = json.loads(l)
        if r["pair"] in v1 and r["status"] in ("dropped", "added"):
            x = r["pre"] if r["status"] == "dropped" else r["pub"]
            if x["sig"] is not None:
                rows.append((r["pair"], r["status"], bool(x["sig"])))
    s1 = pd.DataFrame(rows, columns=["pair", "status", "sig"])
    g = s1.groupby(["pair", "status"]).sig.agg(["sum", "count"]).unstack(fill_value=0)
    sa, na, sd, nd = (g[("sum", "added")].to_numpy(), g[("count", "added")].to_numpy(),
                      g[("sum", "dropped")].to_numpy(), g[("count", "dropped")].to_numpy())
    idx = np.random.default_rng(SEED).integers(0, len(g), size=(NBOOT, len(g)))
    diff = sa[idx].sum(1) / na[idx].sum(1) - sd[idx].sum(1) / nd[idx].sum(1)
    out["S1_v1"] = dict(share_sig_added=float(sa.sum() / na.sum()), share_sig_dropped=float(sd.sum() / nd.sum()),
                        diff=float(sa.sum() / na.sum() - sd.sum() / nd.sum()),
                        diff_ci=[float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))],
                        n_added=int(na.sum()), n_dropped=int(nd.sum()), n_papers=int(len(g)))
    json.dump(out, open(TAB / "supplementary.json", "w"), indent=1, default=float)
    comb[["sample", "id", "pair", "pre", "pub", "up", "kind", "note"]].to_csv(TAB / "verified_crossings.csv", index=False)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
