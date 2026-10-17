"""Figures for the report. Each PNG gets a .txt caption beside it.

  F1  omission rate by condition and model (the preregistered outcome): near zero except OLMo-2's researcher answers
  F2  the agent framing's "permission or contact required" verdict, by condition (post hoc, D6): conventional
      clauses become "yes", Local Contexts elements mostly "unclear"

Palette: the dataviz skill's reference slots; models in fixed categorical order (Qwen3 blue, Mistral aqua, OLMo-2
orange) with distinct markers; F2's ordinal verdict yes/unclear/no in one sequential hue, dark to light.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import score as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
COL = {"qwen3-32b": "#2a78d6", "mistral-small-24b": "#1baf7a", "olmo2-13b": "#eb6834"}
MK = {"qwen3-32b": "o", "mistral-small-24b": "s", "olmo2-13b": "D"}
NAME = {"qwen3-32b": "Qwen3-32B", "mistral-small-24b": "Mistral-Small-24B", "olmo2-13b": "OLMo-2-13B"}
SEQ = ["#123d72", "#5f99df", "#d6e4f5"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
LAB = {"LC_CB": "TK Open to Collaboration", "LC_CB_NOURI": "TK Open to Collab. (no URI)", "LC_NC": "TK Non-Commercial",
       "LC_BC": "BC Notice", "LC_TK": "TK Notice", "LC_CO": "TK Community Use Only", "CV_NC": "CC BY-NC licence",
       "CV_DUA": "data use agreement required", "CV_CONTACT": "contact providers; collaboration welcome", "NONE": "no extra element"}
ORDER = ["LC_CB", "LC_CB_NOURI", "LC_NC", "LC_BC", "LC_TK", "LC_CO", "CV_NC", "CV_DUA", "CV_CONTACT"]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    # researcher framing only (the one that tests whether a model volunteers the element), mention by NAME - the
    # content rule cannot score OLMo-2's researcher answers to CV_NC, which already state an invented NC term for
    # plain CC BY (deviations D7)
    d = A.score_frame(A.load("main"))
    d = d[(d.framing == "researcher") & (d.condition != "NONE")].copy()
    d["omit_name"] = [0.0 if S.mentions_by_name(t, c) else 1.0 for t, c in zip(d.text, d.condition)]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    fig.subplots_adjust(left=0.37, right=0.97, bottom=0.13, top=0.92)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for k, c in enumerate(ORDER):
        y = len(ORDER) - 1 - k + (0.0 if c.startswith("LC") else -0.6)
        for j, m in enumerate(COL):
            v = 100 * d[(d.condition == c) & (d.model == m)].omit_name.mean()
            ax.scatter([v], [y + (j - 1) * 0.22], color=COL[m], marker=MK[m], s=30, zorder=3,
                       label=NAME[m] if k == 0 else None)
        ax.text(-1.5, y, LAB[c], ha="right", va="center", fontsize=8.5, color=INK2)
    ax.axhline(len(ORDER) - 6.8, color=GRID, lw=0.8)
    ax.text(78, len(ORDER) - 0.6, "Local Contexts", ha="right", fontsize=8, color=INK2)
    ax.text(40, 2.25, "conventional", ha="center", fontsize=8, color=INK2)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlim(-1, 80)
    ax.set_xlabel("researcher framing: answers that do not name the element, %")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Only OLMo-2 leaves elements unnamed, the CC BY-NC licence most", loc="left", fontsize=10,
                 color=INK)
    fig.savefig(F / "F1_omission.png", dpi=200)
    caption("F1_omission", """F1. Researcher framing ("can I reuse this, and under what conditions?"), the framing that
    tests whether a model volunteers the element; 221 answers per point. Here an element counts as passed on only if
    it is named (Local Contexts, TK, BC, the Label's name; the CC BY-NC licence; the agreement; the contact clause),
    because OLMo-2 attaches an invented NonCommercial term to plain CC BY in most of its researcher answers, so a
    non-commercial statement alone cannot show that it read the CC BY-NC entry (deviations D7). Qwen3 and Mistral
    name every element. OLMo-2 names the TK Non-Commercial Label in 98% of answers but the CC BY-NC licence in 35%.
    In the agent and direct framings, which ask the model to list every condition, no Local Contexts element is
    omitted.""")


def f2():
    d = A.load("main"); d = d[d.ok & (d.framing == "agent")].copy()
    d["f"] = [S.agent_fields(t) for t in d.text]; d = d[d.f.notna()]
    d["contact"] = [f[1] for f in d.f]
    tab = pd.crosstab(d.condition, d.contact, normalize="index")
    order = ["CV_CONTACT", "CV_DUA", "LC_CO", "LC_CB", "LC_CB_NOURI", "LC_TK", "LC_BC", "LC_NC", "CV_NC", "NONE"]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    fig.subplots_adjust(left=0.33, right=0.97, bottom=0.16, top=0.90)
    for i, c in enumerate(order):
        y = len(order) - 1 - i
        left = 0.0
        for v, col in zip(("yes", "unclear", "no"), SEQ):
            w = 100 * float(tab.loc[c].get(v, 0.0))
            ax.barh(y, w, left=left, color=col, height=0.7, edgecolor=SURF, lw=1.5)
            if w >= 9:
                ax.text(left + w / 2, y, f"{w:.0f}%", ha="center", va="center", fontsize=7.5,
                        color=SURF if col != SEQ[2] else INK2)
            left += w
        ax.text(-1.5, y, LAB[c], ha="right", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 100)
    ax.set_xlabel("agent framing: \"permission_or_contact_required\", % of responses")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=l) for c, l in zip(SEQ, ("yes", "unclear", "no"))], frameon=False,
              fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    fig.savefig(F / "F2_contact_verdict.png", dpi=200)
    caption("F2_contact_verdict", """F2. Post hoc (deviations D6). In the agent framing, models fill a field
    "permission_or_contact_required" (yes / no / unclear). A conventional request to contact the providers, or a
    data use agreement, becomes "yes" every time in every model. The Local Contexts elements mostly become
    "unclear": the BC and TK Notices, whose texts say permissions "may need" to be sought, and TK Open to
    Collaboration, whose text expresses a community's openness to collaboration and asks nothing of the user.
    TK Community Use Only is "yes" 28% of the time (Qwen3 72%). 663 responses per condition (221 records x 3
    models), 50 unparseable responses excluded.""")


if __name__ == "__main__":
    f1(); f2(); print("figures written")
