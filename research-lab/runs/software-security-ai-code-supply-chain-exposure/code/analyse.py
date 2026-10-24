"""H1, H2 and secondaries (plan sections 3-5) -> results/tables/primary.json and tables.

Package names are compared after normalisation (npm as is; PyPI per PEP 503). Only aggregate counts and package names
are written to results/; commit text stays in data/.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB, REPOS = RUN / "data" / "interim", RUN / "results" / "tables", RUN / "data" / "repos"
TAB.mkdir(parents=True, exist_ok=True)
B, SEED = 2000, 20261025
WINDOW = pd.Timestamp("2024-06-01", tz="UTC")


def norm(eco, name):
    return re.sub(r"[-_.]+", "-", name).lower() if eco == "pypi" else name


def load():
    P = pd.read_parquet(INT / "packages.parquet")
    F = pd.read_parquet(INT / "release_flags.parquet")
    G = pd.read_parquet(INT / "graphs.parquet")
    S = pd.read_parquet(INT / "graph_status.parquet")
    f = INT / "clone_failures.tsv"
    inactive = set(pd.read_csv(f, sep="\t", names=["repo", "status"]).query("status == 'inactive'").repo) if f.exists() else set()
    P["cloned"] = P.repo.map(lambda r: isinstance(r, str) and ((REPOS / (r.replace("/", "__") + ".git") / "HEAD").exists() or r in inactive))
    P["key"] = [norm(e, n) for e, n in zip(P.eco, P.name)]
    F["key"] = [norm(e, n) for e, n in zip(F.eco, F.name)]
    G["key"] = [norm(e, n) for e, n in zip(G.eco, G.node)]
    G["rkey"] = [norm(e, n) for e, n in zip(G.eco, G.root)]
    return P, F, G, S


def flags_for(F, tag_only=False):
    f = F.copy()
    if tag_only:
        f["flagged"] = f.flagged & f.method.isin(["tag", "tag_date"])
    return {(e, k, str(v)): bool(x) for e, k, v, x in zip(f.eco, f.key, f.version, f.flagged)}


def exposure(P, F, G, S, tag_only=False, drop=None):
    fl = flags_for(F, tag_only)
    P = P.copy()
    P["latest_flag"] = [fl.get((e, k, str(v)), False) for e, k, v in zip(P.eco, P.key, P.latest)]
    ok = set(zip(S[S.ok].eco, S[S.ok].name))
    G = G.copy()
    G["flag"] = [fl.get((e, k, str(v)), False) for e, k, v in zip(G.eco, G.key, G.node_version)]
    if drop is not None:
        G.loc[G.key.isin(drop), "flag"] = False
    exp = G.groupby(["eco", "root"]).flag.any()
    P["has_graph"] = [(e, n) in ok for e, n in zip(P.eco, P.name)]
    P["exposed"] = [bool(exp.get((e, n), False)) for e, n in zip(P.eco, P.name)]
    return P, G


def stats(P, rng):
    out = {}
    for eco, g in P.groupby("eco"):
        c = g[g.cloned]
        gr = g[g.has_graph]
        p = c.latest_flag.mean()
        w = gr.downloads.astype(float).to_numpy()
        e = gr.exposed.to_numpy().astype(float)
        Pw = float((w * e).sum() / w.sum())
        bp, bw = [], []
        gi = g.reset_index(drop=True)
        cl, hg = gi.cloned.to_numpy(), gi.has_graph.to_numpy()
        lf, ex = gi.latest_flag.to_numpy().astype(float), gi.exposed.to_numpy().astype(float)
        dw = gi.downloads.astype(float).to_numpy()
        for _ in range(B):
            i = rng.integers(0, len(gi), len(gi))
            bp.append(lf[i][cl[i]].mean())
            m = hg[i]
            bw.append((dw[i][m] * ex[i][m]).sum() / dw[i][m].sum())
        bp, bw = np.array(bp), np.array(bw)
        R = Pw / p if p > 0 else np.inf
        bR = bw / np.where(bp > 0, bp, np.nan)
        q = lambda v: [round(float(np.nanpercentile(v, 2.5)), 4), round(float(np.nanpercentile(v, 97.5)), 4)]
        out[eco] = {"packages": int(len(g)), "cloned": int(c.shape[0]), "with_graph": int(gr.shape[0]),
                    "p": round(float(p), 4), "p_ci": q(bp), "P_w": round(Pw, 4), "P_w_ci": q(bw),
                    "unweighted_exposure": round(float(e.mean()), 4), "R": round(float(R), 3), "R_ci": q(bR)}
    return out


def verdicts(st):
    a = [st[e]["R_ci"] for e in ("npm", "pypi")]
    h1a = "Supported" if all(lo >= 5 for lo, _ in a) else "Refuted" if any(hi < 5 for _, hi in a) else "Inconclusive"
    lo, hi = st["npm"]["P_w_ci"]
    h1b = "Supported" if lo > 0.30 else "Refuted" if hi < 0.30 else "Inconclusive"
    h1 = "Supported" if h1a == h1b == "Supported" else "Refuted" if "Refuted" in (h1a, h1b) else "Inconclusive"
    return h1a, h1b, h1


def latency(rng):
    C = pd.read_parquet(INT / "commit_releases.parquet")
    C = C.sort_values("latency_days").drop_duplicates(["eco", "name", "sha"])
    rows, unmatched = [], 0
    for (repo, eco, name), g in C.groupby(["repo", "eco", "name"]):
        ai = g[g.agent.notna()].sort_values("ct")
        if ai.empty:
            continue
        hu = g[g.agent.isna() & ~g.bot].sort_values("ct")
        used = np.zeros(len(hu), bool)
        hct, hlat = hu.ct.to_numpy(), hu.latency_days.to_numpy()
        for r in ai.itertuples():
            if len(hu) == 0:
                unmatched += 1
                continue
            d = np.abs(hct - r.ct).astype(float)
            d[used] = np.inf
            j = int(np.argmin(d))
            if d[j] <= 14 * 86400:
                used[j] = True
                rows.append({"repo": repo, "eco": eco, "ai": r.latency_days, "human": hlat[j], "agent": r.agent})
            else:
                unmatched += 1
    M = pd.DataFrame(rows)
    ratio = float(np.median(M.ai) / np.median(M.human))
    repos = M.repo.unique()
    idx = {r: np.where(M.repo.to_numpy() == r)[0] for r in repos}
    br = []
    for _ in range(B):
        pick = rng.choice(repos, len(repos))
        ii = np.concatenate([idx[r] for r in pick])
        h = np.median(M.human.to_numpy()[ii])
        br.append(np.median(M.ai.to_numpy()[ii]) / h if h > 0 else np.nan)
    lo, hi = np.nanpercentile(br, [2.5, 97.5])
    v = "Supported" if hi <= 0.5 else "Refuted" if lo > 0.5 else "Inconclusive"
    by_eco = {e: {"pairs": int(len(g)), "median_ai_days": round(float(g.ai.median()), 2), "median_human_days": round(float(g.human.median()), 2)}
              for e, g in M.groupby("eco")}
    return {"pairs": int(len(M)), "repos": int(len(repos)), "unmatched_ai": unmatched, "median_ai_days": round(float(M.ai.median()), 2),
            "median_human_days": round(float(M.human.median()), 2), "ratio": round(ratio, 3), "ratio_ci": [round(float(lo), 3), round(float(hi), 3)],
            "verdict": v, "by_eco": by_eco}


def monthly(P, F):
    Cm = pd.read_parquet(INT / "commits.parquet")
    Cm["month"] = pd.to_datetime(Cm.ct, unit="s", utc=True).dt.strftime("%Y-%m")
    eco_of = P.dropna(subset=["repo"]).groupby("repo").eco.agg(lambda s: ",".join(sorted(set(s))))
    out = {}
    for eco in ("npm", "pypi"):
        rs = set(eco_of[eco_of.str.contains(eco)].index)
        c = Cm[Cm.repo.isin(rs) & ~Cm.bot & (Cm.month >= "2024-06")]
        t = c.groupby("month").agg(commits=("sha", "size"), ai=("agent", lambda s: s.notna().sum()))
        t["share"] = (t.ai / t.commits).round(5)
        by = c[c.agent.notna()].groupby(["month", "agent"]).size().unstack(fill_value=0)
        f = F[F.eco == eco].copy()
        f["month"] = f.published.dt.strftime("%Y-%m")
        rf = f.groupby("month").flagged.agg(["mean", "size"]).round(4)
        out[eco] = {"commits": t.reset_index().to_dict("records"), "agents_total": c.agent.value_counts().to_dict(),
                    "agents_by_month": by.reset_index().to_dict("records"), "releases_flagged_by_month": rf.reset_index().to_dict("records")}
    return out


def main():
    P, F, G, S = load()
    rng = np.random.default_rng(SEED)
    Px, Gx = exposure(P, F, G, S)
    st = stats(Px, rng)
    h1a, h1b, h1 = verdicts(st)
    out = {"H1": {"by_eco": st, "H1a": h1a, "H1b": h1b, "verdict": h1}}
    nodes = Gx[Gx.key != Gx.rkey]
    inset = set(zip(P.eco, P.key))
    out["H1"]["node_coverage"] = {e: round(float(np.mean([(e, k) in inset for k in g.key])), 4) for e, g in nodes.groupby("eco")}
    out["H1"]["release_methods"] = F.method.value_counts().to_dict()
    out["H1"]["latest_release_in_window"] = {e: round(float(g.flagged.size), 0) for e, g in F.groupby("eco")}
    # secondary 3: monorepos dropped, tag-only
    mono = P.dropna(subset=["repo"]).groupby("repo").name.transform("size") > 1
    mono_keys = set(P.dropna(subset=["repo"])[mono].key)
    Pm, _ = exposure(P[~P.key.isin(mono_keys)], F, G, S, drop=mono_keys)
    Pt, _ = exposure(P, F, G, S, tag_only=True)
    out["sensitivity"] = {"no_monorepos": stats(Pm, np.random.default_rng(SEED + 1)),
                          "tag_only": stats(Pt, np.random.default_rng(SEED + 2))}
    out["H2"] = latency(np.random.default_rng(SEED + 3))
    out["monthly"] = monthly(P, F)
    # secondary 5: most-downloaded flagged latest releases and how many roots include them
    fl = Px[Px.latest_flag].sort_values("downloads", ascending=False).head(25)
    cnt = Gx[Gx.flag & (Gx.key != Gx.rkey)].groupby(["eco", "key"]).root.nunique()
    out["top_flagged"] = [{"eco": r.eco, "name": r.name, "downloads": int(r.downloads), "roots_including": int(cnt.get((r.eco, r.key), 0))}
                          for r in fl.itertuples()]
    (TAB / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({"H1": out["H1"], "H2": out["H2"], "sensitivity": out["sensitivity"]}, indent=1, default=str)[:5000])


if __name__ == "__main__":
    main()
