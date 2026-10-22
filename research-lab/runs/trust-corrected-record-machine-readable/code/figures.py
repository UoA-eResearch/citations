"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  unmarked share by publisher (own XML marker, reference lists ignored) and missing sidecar flag, top 15
  F2  marked share by months since retraction: the 180 days before the snapshot, then the primary cohort
  F3  unmarked share by the source of the retraction date
  F4  peS2o (D5 rule): the same papers in PMC and in peS2o, and peS2o overall by source
Cohort (D5): the primary cohort without the documents dated only by a Crossref self-update, which are undated.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
XML, FLAG = "#2a78d6", "#e8a317"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
S = pd.Timestamp("2026-10-21")


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    o = pd.read_csv(RUN / "results" / "overlay" / "retraction_overlay.csv.gz", parse_dates=["date"])
    docs = pd.read_csv(T / "documents.csv.gz")[["pmcid", "publisher_name"]]
    o = o[o.in_snapshot].merge(docs, on="pmcid", how="left")
    o["flag"] = o.sidecar_flag.fillna(False).astype(bool)
    o["own"] = o.own_marker.fillna(False).astype(bool)
    C_all = o[o.stratum == "primary"]
    C = C_all[C_all.date_source != "crossref-self-update (issue date)"]        # D5

    # F1 publishers
    top = C.publisher_name.value_counts().head(15).index[::-1]
    g = C[C.publisher_name.isin(top)].groupby("publisher_name").agg(n=("pmcid", "size"), unm=("own", lambda s: 1 - s.mean()),
                                                                     nof=("flag", lambda s: 1 - s.mean())).loc[top]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    fig.subplots_adjust(left=0.36, right=0.97, bottom=0.1, top=0.88)
    y = range(len(g))
    ax.barh([i + 0.2 for i in y], 100 * g.unm, height=0.38, color=XML, label="no retraction marker of its own in the XML")
    ax.barh([i - 0.2 for i in y], 100 * g.nof, height=0.38, color=FLAG, label="PMC's sidecar flag not set")
    ax.set_yticks(list(y)); ax.set_yticklabels([f"{p[:34]} ({n:,})" for p, n in zip(g.index, g.n)], fontsize=7.5)
    ax.set_xlabel("% of the publisher's retracted documents in the primary cohort"); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.suptitle("Where the retraction marker is missing: by publisher (top 15 by count)", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_publishers.png", dpi=170); plt.close(fig)
    caption("F1_publishers", f"""Primary cohort ({len(C):,} retracted documents in the PMC Open Access bucket,
    retracted at least 180 days before the 2026-10-21 snapshot), by publisher as named by Retraction Watch or the XML.
    Blue: no retraction marker in the document's own XML (reference lists ignored, withdrawal wording counted; D3).
    Orange: PMC's sidecar flag is_retracted not set. Counts in brackets.""")

    # F2 latency
    R = o[o.stratum == "recent"].copy()
    R["m"] = ((S - R.date).dt.days // 30).clip(0, 5)
    lat = R.groupby("m").agg(own=("own", "mean"), flag=("flag", "mean"), n=("pmcid", "size"))
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.21, top=0.85)
    xs = list(lat.index) + [6.5]
    ax.plot(xs, list(100 * lat.own) + [100 * C.own.mean()], marker="o", ms=5, lw=2, color=XML, label="own XML marker")
    ax.plot(xs, list(100 * lat.flag) + [100 * C.flag.mean()], marker="o", ms=5, lw=2, color=FLAG, label="sidecar flag")
    ax.set_xticks(xs); ax.set_xticklabels([f"{m}" for m in lat.index] + ["6+\n(primary)"])
    for x, n in zip(xs, list(lat.n) + [len(C)]):
        ax.text(x, 74, f"n={n:,}", ha="center", fontsize=7, color=INK2)
    ax.set_ylim(72, 101); ax.set_xlabel("months between retraction and the snapshot"); ax.set_ylabel("% marked")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(0.12, 0.45))
    fig.suptitle("Markers arrive within about a month of the retraction", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_latency.png", dpi=170); plt.close(fig)
    caption("F2_latency", """Share of retracted documents marked, by whole months between the retraction date and
    the snapshot (cross-sectional: each point is a different set of documents). Months 0-5 are the documents
    retracted in the 180 days before the snapshot; the last point is the primary cohort. Dates are Retraction
    Watch's, else Crossref's.""")

    # F3 date source
    g = C_all.groupby("date_source").agg(n=("pmcid", "size"), unm=("own", lambda s: 1 - s.mean()))
    order = [k for k in ("retraction-watch", "crossref", "crossref-self-update (issue date)") if k in g.index]
    g = g.loc[order]
    fig, ax = plt.subplots(figsize=(7.4, 2.6))
    fig.subplots_adjust(left=0.36, right=0.97, bottom=0.2, top=0.8)
    ax.barh(range(len(g)), 100 * g.unm, color=XML, height=0.55)
    ax.set_yticks(range(len(g))); ax.set_yticklabels([f"{k} ({n:,})" for k, n in zip(g.index, g.n)], fontsize=8)
    for i, v in enumerate(g.unm):
        ax.text(100 * v + 0.4, i, f"{100 * v:.1f}%", va="center", fontsize=8, color=INK)
    ax.invert_yaxis(); ax.set_xlabel("% with no marker of its own"); ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("The unmarked residue concentrates where the retraction date is doubtful", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F3_date_source.png", dpi=170); plt.close(fig)
    caption("F3_date_source", """The cohort as preregistered, by the source of the retraction date. Crossref
    self-updates (the article's own record asserts its retraction; mostly Elsevier) carry the issue date, not the
    retraction date (D4); D5 moves these 412 documents to the undated stratum.""")

    # F4 peS2o against PMC (D5)
    j = json.load(open(T / "pes2o_secondary.json"))
    ds = j["downstream_pmc_overlap"]
    bars = [("same papers: PMC XML, own marker", ds["pmc_own_marker_share"], ds["n"], XML),
            ("same papers: peS2o text", ds["pes2o_v2_marked_share"], ds["n"], FLAG),
            ("all matched peS2o: full text (s2orc)", j["by_source"]["s2orc"]["v2"], j["by_source"]["s2orc"]["n"], FLAG),
            ("all matched peS2o: title + abstract (s2ag)", j["by_source"]["s2ag"]["v2"], j["by_source"]["s2ag"]["n"], FLAG)]
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    fig.subplots_adjust(left=0.4, right=0.95, bottom=0.2, top=0.82)
    for i, (lab, v, n, col) in enumerate(bars):
        ax.barh(i, 100 * v, color=col, height=0.55)
        ax.text(100 * v + 1, i, f"{100 * v:.1f}%", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(bars))); ax.set_yticklabels([f"{b[0]} ({b[2]:,})" for b in bars], fontsize=8)
    ax.invert_yaxis(); ax.set_xlim(0, 110); ax.set_xlabel("% of retracted documents carrying a retraction marker")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("The same retracted papers: marked in PMC, unmarked in peS2o", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F4_pes2o.png", dpi=170); plt.close(fig)
    caption("F4_pes2o", f"""Top two bars: the {ds['n']:,} retracted papers (retracted on or before 2022-07-07, not
    notices) that are both in the PMC Open Access snapshot and in peS2o v2 (knowledge cutoff 2023-01-03): the share
    whose PMC XML carries its own retraction marker, and the share whose peS2o text does. Bottom two: all
    {j['matched_documents']:,} matched peS2o documents by source, under the D5 rule (the study rule plus "notice of
    retraction" run into the title, as peS2o renders IEEE's retitled records). The full-text documents come largely
    from PMC; the title-and-abstract share is high because of IEEE's 2009-2011 retractions.""")
    print("figures written")


if __name__ == "__main__":
    main()
