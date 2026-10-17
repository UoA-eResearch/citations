"""Figures (each PNG has a .txt caption).

  F1  where Local Contexts elements are in the open-data layer: element-bearing records by platform and kind (log
      scale), with Neotoma (prefix 10.21233) shown separately from every other DataCite publisher
  F2  what survives the crosswalks: share of sampled DOIs whose element is preserved, degraded, dropped or unavailable,
      by machine view; Neotoma and other publishers in separate panels

Palette: status-like ordinal (preserve -> drop) in one sequential hue plus a neutral for unavailable.
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
SEQ = {"preserve": "#123d72", "degrade": "#5f99df", "drop": "#eb6834", "unavailable": "#d8d6d0"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
VIEWS = ["datacite_xml", "oai_datacite", "oai_dc", "crosscite_json", "schemaorg_jsonld", "csl_json", "bibtex", "citation_text", "openaire"]
LAB = {"datacite_xml": "DataCite XML", "oai_datacite": "OAI-PMH oai_datacite", "oai_dc": "OAI-PMH oai_dc", "crosscite_json": "Crosscite JSON",
       "schemaorg_jsonld": "schema.org JSON-LD", "csl_json": "CSL-JSON", "bibtex": "BibTeX", "citation_text": "formatted citation",
       "openaire": "OpenAIRE Graph"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f2():
    v = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "views.jsonl")])
    v["stratum"] = v.doi.str.startswith("10.21233/").map({True: "Neotoma (10.21233)", False: "all other publishers"})
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    fig.subplots_adjust(left=0.2, right=0.98, bottom=0.2, top=0.86, wspace=0.08)
    for ax, (st, g) in zip(axes, sorted(v.groupby("stratum"), key=lambda x: x[0] != "all other publishers")):
        n = g.doi.nunique()
        for i, vw in enumerate(VIEWS):
            x = g[g.view == vw].result.value_counts(normalize=True)
            left = 0
            for res in ("preserve", "degrade", "drop", "unavailable"):
                w = float(x.get(res, 0))
                ax.barh(len(VIEWS) - 1 - i, w, left=left, color=SEQ[res], height=0.62, edgecolor=SURF, lw=1,
                        label=res if (i == 0 and ax is axes[0]) else None)
                left += w
        ax.set_title(f"{st} (n = {n} DOIs)", fontsize=9, color=INK)
        ax.set_xlim(0, 1); ax.set_xlabel("share of sampled DOIs")
        ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(VIEWS))); axes[0].set_yticklabels([LAB[x] for x in VIEWS][::-1])
    fig.legend(frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0.2, 1.0), fontsize=8)
    fig.savefig(F / "F2_crosswalks.png", dpi=200); plt.close(fig)
    caption("F2_crosswalks", """For sampled DOIs carrying a Local Contexts element in DataCite, whether each machine view
    preserves it (in a rights field, distinct from the licence), degrades it (merged into the licence or free text),
    drops it, or returns nothing. Neotoma's records are near-identical, so its panel is one pattern repeated.""")


def f1():
    c = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "census.jsonl")])
    pr = pd.read_csv(T / "precision.csv"); bad = set(zip(pr[pr.genuine == 0].platform, pr[pr.genuine == 0].record.astype(str)))
    c = c[[(p, str(i)) not in bad for p, i in zip(c.platform, c.id)]]
    c["group"] = c.platform
    c.loc[(c.platform == "datacite") & c.doi.str.lower().str.startswith("10.21233/"), "group"] = "DataCite: Neotoma"
    c.loc[(c.platform == "datacite") & ~c.doi.str.lower().str.startswith("10.21233/"), "group"] = "DataCite: all others"
    g = c.groupby("group").size().sort_values()
    fig, ax = plt.subplots(figsize=(7.0, 2.8))
    fig.subplots_adjust(left=0.27, right=0.95, bottom=0.2, top=0.92)
    ax.barh(range(len(g)), g.values, color="#2a78d6", height=0.6)
    for i, val in enumerate(g.values):
        ax.text(val * 1.15, i, f"{val:,}", va="center", fontsize=8, color=INK)
    ax.set_xscale("log"); ax.set_yticks(range(len(g))); ax.set_yticklabels(g.index)
    ax.set_xlabel("records carrying a Local Contexts element (log scale)")
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    fig.savefig(F / "F1_census.png", dpi=200); plt.close(fig)
    caption("F1_census", """Records carrying a Local Contexts Notice or Label, by platform, after the free-text channel
    was adjudicated in full. One repository (Neotoma) accounts for nearly all of them. Zenodo and figshare hits also
    appear as DataCite DOIs, so platforms overlap.""")


if __name__ == "__main__":
    f1(); f2()
    print(sorted(p.name for p in F.iterdir()))
