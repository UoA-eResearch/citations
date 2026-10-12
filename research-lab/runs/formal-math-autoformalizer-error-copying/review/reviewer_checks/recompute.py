"""Independent recomputation of the primary RR, bootstrap CI, verdict, by-model, O-vs-P, verbatim and greedy numbers
from data/classified/*.jsonl and *_outputs.jsonl, without importing analysis.py."""
import json, sys
from collections import Counter, defaultdict
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/formal-math-autoformalizer-error-copying"
fz = [json.loads(l) for l in open(f"{RUN}/results/catalogue/frozen.jsonl")]
prim59 = sorted(r["item"] for r in fz if r["role"]=="primary" and r["set"]=="included" and r.get("N_twin"))
inc129 = sorted(r["item"] for r in fz if r["role"]=="primary" and r["set"]=="included" and r.get("paraphrase"))
one63 = sorted(r["item"] for r in fz if r["role"]=="primary" and r["set"] in ("included","one_rater") and r.get("N_twin"))
ctl = sorted(r["item"] for r in fz if r["role"]=="control")
print("59:",len(prim59),"129:",len(inc129),"63:",len(one63),"ctl:",len(ctl))
MODELS = ["kimina","goedel","herald","dsp_v2","qwen"]; PRIMARY = MODELS[:3]
rows = []
both = Counter(); errs = Counter(); nout = Counter(); times = defaultdict(list)
for m in MODELS:
    cl = {}
    for l in open(f"{RUN}/data/classified/{m}.jsonl"):
        r = json.loads(l); cl[r["uid"]] = r
        if "error" in r: errs[m]+=1
    for l in open(f"{RUN}/data/classified/{m}_outputs.jsonl"):
        o = json.loads(l); item, cond = o["key"].rsplit("|",1)
        c = cl.get(o.get("uid"), {})
        elab = bool(c.get("elab")); cp = bool(c.get("copy")); cr = bool(c.get("correct"))
        if cp and cr: both[m]+=1
        cls = "noelab" if not elab else "copy" if cp and not cr else "correct" if cr and not cp else "other"
        rows.append(dict(model=m,item=item,cond=cond,idx=o["idx"],cls=cls,verbatim=bool(o.get("verbatim")),finish=o.get("finish"),extracted=o.get("extracted"),elab=elab,s=c.get("s"),uid=o.get("uid")))
        nout[(m,o["key"])]+=1
df = pd.DataFrame(rows)
print("copy&correct both:",dict(both)); print("errors in classified:",dict(errs))
# denominators: every key has exactly 17 outputs (16 temp + 1 greedy)?
cnt = Counter(nout.values()); print("outputs per key distribution:",dict(cnt))
temp = df[df.idx!="g"]
print("temp samples per model x cond:"); print(temp.groupby(["model","cond"]).size().unstack())
def rr(xo,xt,n): return ((xo+0.5)/n)/((xt+0.5)/n)
def boot(xo,xt,n_models,B=2000,seed=20261012,n=16):
    I=len(xo); N=I*n_models*n; est=rr(xo.sum(),xt.sum(),N)
    rng=np.random.default_rng(seed); idx=rng.integers(0,I,(B,I))
    bs=rr(xo[idx].sum(1),xt[idx].sum(1),N); lo,hi=np.percentile(bs,[2.5,97.5])
    return est,lo,hi,int(xo.sum()),int(xt.sum()),N
def per_item(items,models,cond,what="copy"):
    d=temp[temp.model.isin(models)&(temp.cond==cond)&temp.item.isin(items)]
    h = (d.cls==what) if what!="verbatim" else d.verbatim
    x=d.assign(h=h).groupby("item").h.sum().reindex(items,fill_value=0)
    return x.to_numpy().astype(float)
res={}
xo,xt=per_item(prim59,PRIMARY,"O"),per_item(prim59,PRIMARY,"T")
res["primary"]=boot(xo,xt,3)
# also a different-seed bootstrap and a BCa-free check with 10000 draws
res["primary_seed1_B10000"]=boot(xo,xt,3,B=10000,seed=1)
for m in MODELS: res[f"by_model/{m}"]=boot(per_item(prim59,[m],"O"),per_item(prim59,[m],"T"),1)
res["O_vs_P_129"]=boot(per_item(inc129,PRIMARY,"O"),per_item(inc129,PRIMARY,"P"),3)
res["O_vs_P_59"]=boot(xo,per_item(prim59,PRIMARY,"P"),3)
res["P_vs_T_59"]=boot(per_item(prim59,PRIMARY,"P"),xt,3)
for m in MODELS: res[f"OvsP_by_model_129/{m}"]=boot(per_item(inc129,[m],"O"),per_item(inc129,[m],"P"),1)
for m in MODELS: res[f"OvsP_by_model_59/{m}"]=boot(per_item(prim59,[m],"O"),per_item(prim59,[m],"P"),1)
res["one_rater_63"]=boot(per_item(one63,PRIMARY,"O"),per_item(one63,PRIMARY,"T"),3)
mf=[i for i in prim59 if i.startswith("minif2f/")]; pn=[i for i in prim59 if i.startswith("proofnet/")]
res["minif2f"]=boot(per_item(mf,PRIMARY,"O"),per_item(mf,PRIMARY,"T"),3)
res["proofnet"]=boot(per_item(pn,PRIMARY,"O"),per_item(pn,PRIMARY,"T"),3)
cat={r["item"]:r["category"] for r in fz if r["role"]=="primary"}
for c in sorted(set(cat[i] for i in prim59)):
    it=[i for i in prim59 if cat[i]==c]; res[f"cat{c}"]=boot(per_item(it,PRIMARY,"O"),per_item(it,PRIMARY,"T"),3)
flag={"proofnet/Ireland-Rosen|exercise_3_10","proofnet/Rudin|exercise_1_11a","proofnet/Shakarchi|exercise_1_19b"}
nf=[i for i in prim59 if i not in flag]; res["flagged_dropped"]=boot(per_item(nf,PRIMARY,"O"),per_item(nf,PRIMARY,"T"),3)
inf=[i for i in prim59 if i not in {"minif2f/mathd_algebra_188","minif2f/mathd_algebra_314"}]
res["informative_57"]=boot(per_item(inf,PRIMARY,"O"),per_item(inf,PRIMARY,"T"),3)
for k,v in res.items(): print(f"{k:32s} RR={v[0]:.4f} CI=({v[1]:.4f},{v[2]:.4f}) xO={v[3]} xT={v[4]} n={v[5]}")
# verbatim and greedy
for items,lab in ((prim59,"59"),(inc129,"129")):
    for c in "OTP":
        d=temp[temp.model.isin(PRIMARY)&(temp.cond==c)&temp.item.isin(items)]
        g=df[(df.idx=="g")&df.model.isin(PRIMARY)&(df.cond==c)&df.item.isin(items)]
        print(f"items={lab} cond={c}: temp n={len(d)} copies={int((d.cls=='copy').sum())} verbatim={int(d.verbatim.sum())} verbatim&copy={int((d.verbatim&(d.cls=='copy')).sum())} verbatim&notcopy={int((d.verbatim&(d.cls!='copy')).sum())} | greedy n={len(g)} copies={int((g.cls=='copy').sum())}")
# accuracy
for c in "OT":
    d=temp[temp.model.isin(PRIMARY)&(temp.cond==c)&temp.item.isin(prim59)]
    print(f"accuracy {c}: correct={(d.cls=='correct').mean():.4f} copy={(d.cls=='copy').mean():.4f} n={len(d)}")
# among elaborating
for c in "OTP":
    d=temp[temp.model.isin(PRIMARY)&(temp.cond==c)&temp.item.isin(prim59)]
    e=d[d.cls!="noelab"]; print(f"among elab {c}: n={len(e)} copies={int((e.cls=='copy').sum())} rate={(e.cls=='copy').mean():.4f}")
# control
for m in MODELS:
    d=temp[(temp.model==m)&temp.item.isin(ctl)&(temp.cond=="O")]
    print(f"control {m}: n={len(d)} copy={int((d.cls=='copy').sum())} correct={int((d.cls=='correct').sum())} elab={int((d.cls!='noelab').sum())}")
d=temp[temp.model.isin(MODELS)&temp.item.isin(ctl)]
print("control copies by item (all models):"); print(d[d.cls=="copy"].groupby(["item","model"]).size())
# items with any defect output
print("items with any defect:",int(((xo+xt)>0).sum()))
# other share among elaborating & elab rate by model x cond on 59 items
d=temp[temp.item.isin(prim59)]
e=d[d.cls!="noelab"]
print("other share among elaborating (59 items):"); print(e.assign(o=e.cls=="other").groupby(["model","cond"]).o.mean().unstack().round(3))
print("elab rate (59 items):"); print(d.assign(e=d.cls!="noelab").groupby(["model","cond"]).e.mean().unstack().round(3))
# extraction and finish
print("extracted rate by model:"); print(df.groupby("model").extracted.mean().round(4))
print("finish==length by model:"); print(df[df.finish=="length"].groupby("model").size())
# unique statements
tot=0
for m in MODELS: tot+=sum(1 for _ in open(f"{RUN}/data/classified/{m}.jsonl"))
print("unique statements total:",tot)
# timing of classification by cond (potential timeouts): s per unique statement
u=df.drop_duplicates(["model","uid"]).dropna(subset=["uid"])
u=u[u.item.isin(prim59)&u.model.isin(PRIMARY)]
print("classification seconds by cond (unique stmts, 59 items, primary models):")
print(u.groupby("cond").s.describe().round(1))
print("share of unique elaborating statements with s>=20s by cond:"); ue=u[u.elab]; print(ue.assign(slow=ue.s>=20).groupby("cond").slow.mean().round(4))
print("share with s>=40 by cond:"); print(ue.assign(slow=ue.s>=40).groupby("cond").slow.mean().round(4))
df.to_pickle("/mnt/citations/research-lab/runs/formal-math-autoformalizer-error-copying/review/reviewer_checks/outputs_df.pkl")
