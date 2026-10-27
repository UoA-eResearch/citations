"""POST HOC (D2, after independent review): the decompositions, denominators and coverage the review asked for.
Uses analyse.py's loading and flagging (with D2's PEP 440 version canonicalisation). Aggregates and package names only.

  posthoc_review.py -> results/tables/posthoc_review.json, results/tables/coverage.json (G2 stages)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from analyse import B, SEED, WINDOW, exposure, flags_for, load, norm, vnorm  # noqa: E402
from coverage import Coverage  # noqa: E402

q = lambda v: [round(float(np.nanpercentile(v, 2.5)), 4), round(float(np.nanpercentile(v, 97.5)), 4)]


def decomposition(Px):
    """P_w split into the download-weighted root rate and what trees add; joint bootstrap over packages."""
    out = {}
    rng = np.random.default_rng(SEED + 10)
    for eco, g in Px.groupby("eco"):
        gr = g[g.has_graph].reset_index(drop=True)
        w, root, ex = gr.downloads.astype(float).to_numpy(), gr.latest_flag.to_numpy(float), gr.exposed.to_numpy(float)
        Pw_root, Pw = (w * root).sum() / w.sum(), (w * ex).sum() / w.sum()
        bm, br = [], []
        for _ in range(B):
            i = rng.integers(0, len(gr), len(gr))
            a, b = (w[i] * root[i]).sum() / w[i].sum(), (w[i] * ex[i]).sum() / w[i].sum()
            br.append(a); bm.append(b / a if a > 0 else np.nan)
        out[eco] = {"weighted_root_rate": round(float(Pw_root), 4), "weighted_root_rate_ci": q(br), "P_w": round(float(Pw), 4),
                    "tree_adds_points": round(float(Pw - Pw_root), 4),
                    "tree_multiplier": round(float(Pw / Pw_root), 3), "tree_multiplier_ci": q(bm),
                    "unweighted_root_rate_with_graph": round(float(root.mean()), 4), "unweighted_exposed": round(float(ex.mean()), 4),
                    "unweighted_multiplier": round(float(ex.mean() / root.mean()), 2)}
    return out


def denominators(P, F, Px):
    Pr = P.dropna(subset=["repo"])
    mono_repo = set(Pr[Pr.groupby("repo").name.transform("size") > 1].repo)      # as analyse.py: across ecosystems
    fl_in = {(e, k, vnorm(e, v)) for e, k, v in zip(F.eco, F.key, F.version)}
    Px = Px.copy()
    Px["mono"] = Px.repo.isin(mono_repo)
    Px["latest_in_window"] = [(e, k, vnorm(e, v)) in fl_in for e, k, v in zip(Px.eco, Px.key, Px.latest)]
    meth = {(e, k, vnorm(e, v)): m for e, k, v, m in zip(F.eco, F.key, F.version, F.method)}
    Px["latest_method"] = [meth.get((e, k, vnorm(e, v)), "none") for e, k, v in zip(Px.eco, Px.key, Px.latest)]
    out = {}
    for eco, g in Px.groupby("eco"):
        c = g[g.cloned]
        top5 = c[c.latest_flag].groupby("repo").size().sort_values(ascending=False).head(5)
        out[eco] = {"cloned": int(len(c)), "p": round(float(c.latest_flag.mean()), 4),
                    "p_single_package_repos": round(float(c[~c.mono].latest_flag.mean()), 4), "n_single": int((~c.mono).sum()),
                    "p_multi_package_repos": round(float(c[c.mono].latest_flag.mean()), 4), "n_multi": int(c.mono.sum()),
                    "share_of_flagged_latest_from_multi": round(float(c[c.mono].latest_flag.sum() / max(1, c.latest_flag.sum())), 4),
                    "no_release_in_window": int((~c.latest_in_window).sum()),
                    "p_among_released_in_window": round(float(c[c.latest_in_window].latest_flag.mean()), 4),
                    "p_by_latest_method": c.groupby("latest_method").latest_flag.agg(["mean", "size"]).round(4).to_dict("index"),
                    "top5_repos_by_flagged_latest": top5.to_dict(),
                    "p_excluding_top5_repos": round(float(c[~c.repo.isin(top5.index)].latest_flag.mean()), 4)}
    bk = F.groupby(pd.cut(F.n_commits, [-1, 0, 5, 20, 100, 500, 2000, 1e9]), observed=False).flagged.agg(["mean", "size"])
    out["flag_rate_by_range_size"] = {str(k): {"flag_rate": round(float(v["mean"]), 4), "releases": int(v["size"])} for k, v in bk.iterrows()}
    out["flag_rate_by_method"] = F.groupby(["eco", "method"]).flagged.agg(["mean", "size"]).round(4).astype(object).to_dict("index")
    out["flag_rate_by_method"] = {f"{k[0]}|{k[1]}": v for k, v in out["flag_rate_by_method"].items()}
    return out


def coverage(P, F, G):
    """G2 stages: releases (range method, empty ranges), packages in p (no release in window), tree nodes (version match)."""
    path = TAB / "coverage.json"
    cr = Coverage("release_ranges", path, allowed=("date window (no matching tag)",))
    empty = F.n_commits == 0
    date = F.method == "date"
    cr.add_counts(ok=int((~empty & ~date).sum()), drops={"empty commit range (unflagged)": int(empty.sum())},
                  fallbacks={"date window (no matching tag)": int((~empty & date).sum())})
    cr.save()
    cp = Coverage("packages_in_p", path, allowed=("no release since 2024-06-01 -> unflagged",))
    fl_in = {(e, k, vnorm(e, v)) for e, k, v in zip(F.eco, F.key, F.version)}
    c = P[P.cloned]
    inwin = np.array([(e, k, vnorm(e, v)) in fl_in for e, k, v in zip(c.eco, c.key, c.latest)])
    cp.add_counts(ok=int(inwin.sum()), fallbacks={"no release since 2024-06-01 -> unflagged": int((~inwin).sum())})
    cp.save()
    R = pd.read_parquet(INT / "releases.parquet")
    allrel = {(e, norm(e, n), vnorm(e, v)) for e, n, v in zip(R.eco, R.name, R.version.astype(str))}
    pre_window = {(e, norm(e, n), vnorm(e, v)) for e, n, v, t in zip(R.eco, R.name, R.version.astype(str), R.published) if t < WINDOW}
    inset = set(zip(P.eco, P.key))
    nodes = G[(G.key != G.rkey)]
    nodes = nodes[[(e, k) in inset for e, k in zip(nodes.eco, nodes.key)]]
    out = {}
    for eco, g in nodes.groupby("eco"):
        cn = Coverage(f"tree_nodes_{eco}", path)
        keys = [(e, k, vnorm(e, v)) for e, k, v in zip(g.eco, g.key, g.node_version)]
        inF = np.array([k in fl_in for k in keys])
        pre = np.array([k in pre_window for k in keys]) & ~inF
        pr = g.node_version.astype(str).str.contains(r"(?:a|b|rc|dev)\d|-", case=False).to_numpy() & ~inF & ~pre
        anyrel = np.array([k in allrel for k in keys])
        un = ~inF & ~pre & ~pr
        cn.add_counts(ok=int(inF.sum()), drops={"version released before 2024-06-01 (unflagged)": int(pre.sum()),
                                                "pre-release version (excluded by design)": int(pr.sum()),
                                                "version in no registry release": int((un & ~anyrel).sum()),
                                                "package has no cloned repository (unflagged)": int((un & anyrel).sum())})
        cn.save()
        out[eco] = {"in_set_nodes": int(len(g)), "matched_window_release": round(float(inF.mean()), 4)}
    return out


def latency_extras():
    """H2 as reported (per package) and as the plan worded it (per repository, one row per commit, first release)."""
    C = pd.read_parquet(INT / "commit_releases.parquet")
    C = C.sort_values("latency_days")
    out = {}

    def match(df, keys, rng_seed):
        rows, unmatched = [], []
        for _, g in df.groupby(keys):
            ai = g[g.agent.notna()].sort_values("ct")
            if ai.empty:
                continue
            hu = g[g.agent.isna() & ~g.bot].sort_values("ct")
            used = np.zeros(len(hu), bool)
            hct, hlat, hver = hu.ct.to_numpy(), hu.latency_days.to_numpy(), hu.version.astype(str).to_numpy()
            for r in ai.itertuples():
                if len(hu) == 0:
                    unmatched.append(r.latency_days); continue
                d = np.abs(hct - r.ct).astype(float); d[used] = np.inf
                j = int(np.argmin(d))
                if d[j] <= 14 * 86400:
                    used[j] = True
                    rows.append({"repo": r.repo, "sha": r.sha, "ai": r.latency_days, "human": hlat[j], "same_release": str(r.version) == hver[j]})
                else:
                    unmatched.append(r.latency_days)
        M = pd.DataFrame(rows)
        rng = np.random.default_rng(rng_seed)
        repos = M.repo.unique()
        idx = {r: np.flatnonzero(M.repo.to_numpy() == r) for r in repos}
        br = []
        for _ in range(B):
            ii = np.concatenate([idx[r] for r in rng.choice(repos, len(repos))])
            h = np.median(M.human.to_numpy()[ii]); br.append(np.median(M.ai.to_numpy()[ii]) / h if h > 0 else np.nan)
        diff = M[~M.same_release]
        return {"pairs": int(len(M)), "distinct_agent_commits": int(M.sha.nunique()), "repos": int(len(repos)),
                "ratio": round(float(M.ai.median() / M.human.median()), 3), "ratio_ci": q(br),
                "same_release_share": round(float(M.same_release.mean()), 4),
                "ratio_different_release_pairs": round(float(diff.ai.median() / diff.human.median()), 3) if len(diff) else None,
                "unmatched_agent": len(unmatched), "median_unmatched_agent_days": round(float(np.median(unmatched)), 2) if unmatched else None,
                "median_matched_agent_days": round(float(M.ai.median()), 2)}
    Cp = C.drop_duplicates(["eco", "name", "sha"])
    out["as_reported_per_package"] = match(Cp, ["repo", "eco", "name"], SEED + 11)
    Cr = C.drop_duplicates(["repo", "sha"])          # first release containing the commit, any package of the repository
    out["plan_wording_per_repository"] = match(Cr, ["repo"], SEED + 12)
    return out


def hubs(Px, Gx, P, F, G, S):
    out = {}
    for eco in ("npm", "pypi"):
        gr = Px[(Px.eco == eco) & Px.has_graph]
        w = gr.downloads.astype(float).to_numpy()
        base = float((w * gr.exposed).sum() / w.sum())
        top = Gx[(Gx.eco == eco) & Gx.flag & (Gx.key != Gx.rkey)].groupby("key").root.nunique().sort_values(ascending=False).head(10)
        rows = []
        for k, n in top.items():
            Pd, _ = exposure(P, F, G, S, drop={k})
            g2 = Pd[(Pd.eco == eco) & Pd.has_graph]
            rows.append({"node": k, "roots_including": int(n), "P_w_without": round(float((w * g2.exposed).sum() / w.sum()), 4)})
        out[eco] = {"P_w": round(base, 4), "leave_one_out": rows}
    return out


def trend(P):
    Cm = pd.read_parquet(INT / "commits.parquet")
    Cm["month"] = pd.to_datetime(Cm.ct, unit="s", utc=True).dt.strftime("%Y-%m")
    eco_of = P.dropna(subset=["repo"]).groupby("repo").eco.agg(lambda s: ",".join(sorted(set(s))))
    out = {}
    for eco in ("npm", "pypi"):
        rs = set(eco_of[eco_of.str.contains(eco)].index)
        c = Cm[Cm.repo.isin(rs) & ~Cm.bot & (Cm.month >= "2024-06")]
        per = c.groupby(["month", "repo"]).agent.apply(lambda s: s.notna().any()).groupby("month").agg(["mean", "size"])
        out[eco] = {"share_of_active_repos_with_agent_commit": {m: round(float(v), 4) for m, v in per["mean"].items()},
                    "active_repos": {m: int(v) for m, v in per["size"].items()}}
    c = Cm[~Cm.bot & (Cm.month >= "2024-06") & Cm.agent.notna()]
    top = c.groupby("repo").size().sort_values(ascending=False)
    out["agent_commits"] = int(len(c))
    out["share_top10_repos"] = round(float(top.head(10).sum() / len(c)), 4)
    out["share_top50_repos"] = round(float(top.head(50).sum() / len(c)), 4)
    by = c.groupby(["agent", "repo"]).size()
    out["agent_top_repo_share"] = {a: round(float(by[a].max() / by[a].sum()), 3) for a in c.agent.unique()}
    # Copilot: coding agent (account or swe-agent trailer) vs review-suggestion trailer
    A = pd.read_parquet(INT / "ai_matches.parquet", columns=["agent", "rule", "line"])
    cp = A[A.agent == "copilot"]
    sugg = (cp.rule == "trailer") & cp.line.str.contains(r"\+copilot@users\.noreply\.github\.com", case=False, regex=True) & \
        ~cp.line.str.contains("copilot-swe-agent", case=False)
    out["copilot_split"] = {"identity_rule": int((cp.rule == "identity").sum()), "suggestion_trailer_first_line": int(sugg.sum()),
                            "other": int(len(cp) - (cp.rule == "identity").sum() - sugg.sum()), "total": int(len(cp)),
                            "note": "the stored line is the first co-author trailer (review finding 6), so the split is approximate"}
    return out


def main():
    P, F, G, S = load()
    Px, Gx = exposure(P, F, G, S)
    out = {"label": "POST HOC (D2, after independent review)"}
    out["decomposition"] = decomposition(Px)
    out["denominators"] = denominators(P, F, Px)
    out["node_coverage"] = coverage(P, F, G)
    out["H2_extras"] = latency_extras()
    out["hubs"] = hubs(Px, Gx, P, F, G, S)
    out["trend"] = trend(P)
    (TAB / "posthoc_review.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("decomposition", "denominators", "node_coverage", "H2_extras")}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
