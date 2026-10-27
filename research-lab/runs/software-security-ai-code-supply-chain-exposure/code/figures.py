"""Figures (each PNG has a .txt caption). Written after analyse.py.

  F1  AI-attributed share of non-bot commits by month in the repositories behind the top packages, and the agent mix
  F2  p (own latest release flagged), unweighted exposure and download-weighted exposure P_w, with the monorepo-free
      sensitivity
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
ECO = {"npm": "#c8372d", "pypi": "#2a78d6"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.5), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.2, top=0.82, wspace=0.3)
    ax = axes[0]
    for eco, col in ECO.items():
        c = pd.DataFrame(p["monthly"][eco]["commits"])
        c = c[c.month <= "2026-09"]
        ax.plot(pd.to_datetime(c.month), c.share * 100, color=col, lw=2, label=eco)
        ax.annotate(f"{c.share.iloc[-1] * 100:.1f}%", (pd.to_datetime(c.month.iloc[-1]), c.share.iloc[-1] * 100),
                    xytext=(4, 0), textcoords="offset points", color=col, fontsize=8, va="center")
        rs = pd.Series(PH["trend"][eco]["share_of_active_repos_with_agent_commit"])     # D2: repository-level share
        rs = rs[(rs.index >= "2024-06") & (rs.index <= "2026-09")]
        ax.plot(pd.to_datetime(rs.index), rs.values * 100, color=col, lw=1.2, ls="--")
        ax.annotate(f"{rs.iloc[-1] * 100:.0f}% of repos", (pd.to_datetime(rs.index[-1]), rs.iloc[-1] * 100),
                    xytext=(4, 0), textcoords="offset points", color=col, fontsize=7.5, va="center")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("%  (solid: commits; dashed: repositories)", fontsize=8)
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("non-bot commits, repositories of the top 10,000 packages", fontsize=8.5, color=INK2, loc="left")
    ax = axes[1]
    agents = ["claude", "copilot", "cursor", "devin", "aider", "openhands", "codex", "gemini"]
    x = np.arange(len(agents))
    for k, (eco, col) in enumerate(ECO.items()):
        tot = p["monthly"][eco]["agents_total"]
        s = sum(tot.values())
        ax.barh(x + (k - 0.5) * 0.38, [tot.get(a, 0) / s * 100 for a in agents], height=0.36, color=col, label=eco)
    ax.set_yticks(x); ax.set_yticklabels(agents, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("% of AI-attributed commits"); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_title("which agent (by signature)", fontsize=8.5, color=INK2, loc="left")
    fig.suptitle("AI-signed commits rose from near zero to about one in ten; a third of active repositories had one", x=0.02, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F1_monthly_agents.png", dpi=170); plt.close(fig)
    caption("F1_monthly_agents", """Share of commits (excluding dependency and maintenance bots) carrying an AI-agent
    signature: a co-author trailer, a "Generated with" line, or an agent account as author or committer, in shallow
    clones (since 2024-01-01) of the GitHub repositories behind the top 10,000 npm and PyPI packages by downloads. A
    lower bound: unsigned AI-written code is invisible. Dashed (post hoc, D2): share of repositories with any non-bot commit
    that month that had at least one AI-signed commit. Right: agent mix over June 2024 to October 2026 (claude = any
    Claude-model signature, mostly Claude Code; copilot includes committed review suggestions).""")


def f2(p):
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.5), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.2, top=0.8, wspace=0.08)
    labels = ["own latest\nflagged (p)", "tree exposed", "own latest,\nweighted", "tree exposed,\nweighted (P_w)"]
    for ax, (title, st) in zip(axes, (("all top packages", p["H1"]["by_eco"]), ("monorepos removed", p["sensitivity"]["no_monorepos"]))):
        x = np.arange(4)
        for k, (eco, col) in enumerate(ECO.items()):
            s = st[eco]
            wr = PH["decomposition"][eco]["weighted_root_rate"] if title == "all top packages" else np.nan   # D2
            vals = [s["p"], s["unweighted_exposure"], wr, s["P_w"]]
            err = [[s["p"] - s["p_ci"][0], 0, 0, s["P_w"] - s["P_w_ci"][0]], [s["p_ci"][1] - s["p"], 0, 0, s["P_w_ci"][1] - s["P_w"]]]
            ax.bar(x + (k - 0.5) * 0.38, np.array(vals) * 100, width=0.36, color=col, label=f"{eco} (R = {s['R']:.2f})",
                   yerr=np.array(err) * 100, error_kw={"lw": 0.8, "ecolor": INK2})
        ax.axhline(30, color=INK2, lw=0.6, ls="--")
        if title != "all top packages":
            ax.text(2, 1.5, "not computed", ha="center", fontsize=7, color=INK2)
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
        ax.set_title(title, fontsize=9, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.5)
        ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    axes[0].set_ylabel("% of top 10,000 packages")
    fig.suptitle("Download-weighted, dependency trees raise exposure about 1.6-fold, far short of the fivefold hypothesised",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_exposure.png", dpi=170); plt.close(fig)
    caption("F2_exposure", """p: share of top packages whose own latest release contains at least one AI-attributed
    commit in its release range. Exposure: share of top packages whose deps.dev-resolved dependency tree (root
    included) contains at least one AI-flagged release, unweighted and weighted by last-month downloads. R = P_w / p
    (preregistered bar: 5); R divides a weighted by an unweighted rate, so the like-for-like tree effect is P_w over the
    download-weighted own-release rate (third bar; post hoc, D2). Dashed line: H1b's 30% bar for npm. 95% intervals from
    2,000 package bootstrap resamples.
    Right: packages whose repository hosts more than one top package removed, and their releases unflagged in trees.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    PH = json.load(open(T / "posthoc_review.json"))
    f1(p); f2(p)
    print("figures written")
