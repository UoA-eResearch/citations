"""Independent recomputation of H1-H3, the H3 decomposition, the D6 verdict tables and the report's numbers.
Own bootstrap implementation (per-record sufficient statistics, seed 7), the study's frozen scorer for the lexical rule."""
import json, sys, collections
import numpy as np, pandas as pd
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0, R+'code'); import score as S
rows=[]
for m in ['qwen3-32b','olmo2-13b','mistral-small-24b']:
    rows+=[json.loads(l) for l in open(R+f'results/generations/{m}_main.jsonl')]
d=pd.DataFrame(rows)
d['mention']=[S.mentions(t,c) if c in S.PATTERNS else np.nan for t,c in zip(d.text,d.condition)]
d['omit']=1-d.mention
# compare with scored_main.csv
sc=pd.read_csv(R+'results/tables/scored_main.csv')
mm=d.merge(sc,on=['doi','condition','framing','model'],suffixes=('','_s'))
print('scored_main.csv rows', len(sc), 'merged', len(mm), 'mention disagreements', int((mm.mention.fillna(-1)!=mm.mention_s.fillna(-1)).sum()))
LC,CV=S.LC_CONDITIONS,S.CV_CONDITIONS
recs=sorted(d.doi.unique()); idx={k:i for i,k in enumerate(recs)}; n=len(recs)
def per_record(mask):
    s=np.zeros(n); c=np.zeros(n)
    g=d[mask].groupby('doi').omit.agg(['sum','count'])
    for k,r in g.iterrows(): s[idx[k]]=r['sum']; c[idx[k]]=r['count']
    return s,c
lcs,lcc=per_record(d.condition.isin(LC)); cvs,cvc=per_record(d.condition.isin(CV))
# H3
a=d[d.framing=='agent'].copy(); a['f']=[S.agent_fields(t) for t in a.text]
base={(r.doi,r.model):r.f for r in a[a.condition=='NONE'].itertuples()}
lc=a[a.condition.isin(LC)].copy(); lc['b']=[base.get((r.doi,r.model)) for r in lc.itertuples()]
v=lc[lc.f.notna()&lc.b.notna()].copy(); unparsed=len(lc)-len(v)
v['chg']=[f!=b for f,b in zip(v.f,v.b)]
h3s=np.zeros(n); h3c=np.zeros(n)
for k,r in v.groupby('doi').chg.agg(['sum','count']).iterrows(): h3s[idx[k]]=r['sum']; h3c[idx[k]]=r['count']
rng=np.random.default_rng(7); B=2000
h1=[];h2=[];h3=[]
for _ in range(B):
    w=np.bincount(rng.integers(0,n,n),minlength=n)
    l=(w*lcs).sum()/(w*lcc).sum(); c=(w*cvs).sum()/(w*cvc).sum()
    h1.append(l); h2.append(l-c); h3.append((w*h3s).sum()/(w*h3c).sum())
pct=lambda x:(float(np.percentile(x,2.5)),float(np.percentile(x,97.5)))
out={}
out['H1']=dict(est=float(lcs.sum()/lcc.sum()), ci=pct(h1), n=int(lcc.sum()))
out['H2']=dict(est=float(lcs.sum()/lcc.sum()-cvs.sum()/cvc.sum()), ci=pct(h2), cv=float(cvs.sum()/cvc.sum()), n_cv=int(cvc.sum()))
out['H3']=dict(est=float(h3s.sum()/h3c.sum()), ci=pct(h3), n_pairs=int(h3c.sum()), unparsed=int(unparsed))
# analytic binomial-ish check: Wilson interval ignoring clustering
# H3 decomposition
def kind(f,b):
    kinds=[]
    for name,(x,y) in zip(('commercial','contact'),zip(b,f)):
        if x!=y: kinds.append((name,f'{x}->{y}'))
    return kinds
dec=collections.Counter(); todef=0; tounc_only=0
for f,b in zip(v.f,v.b):
    ks=kind(f,b)
    for k in ks: dec[k]+=1
    if ks:
        if all(y.endswith('->unclear') for _,y in ks): tounc_only+=1
        else: todef+=1
out['H3_decomposition']={f'{a}:{b}':c for (a,b),c in dec.most_common()}
out['H3_changed_pairs']=int(v.chg.sum()); out['H3_changed_only_to_unclear']=tounc_only; out['H3_changed_incl_definite']=todef
out['H3_rate_definite_change']=todef/len(v)
# by condition
out['H3_by_condition']={c:dict(change=float(g.chg.mean()), definite=float(np.mean([not all(y.endswith('->unclear') for _,y in kind(f,b)) and bool(kind(f,b)) for f,b in zip(g.f,g.b)]))) for c,g in v.groupby('condition')}
out['H3_by_model']={m:float(g.chg.mean()) for m,g in v.groupby('model')}
# V1 full crosstabs
p=a[a.f.notna()].copy(); p['commercial']=[f[0] for f in p.f]; p['contact']=[f[1] for f in p.f]
out['contact_by_condition']=pd.crosstab(p.condition,p.contact,normalize='index').round(3).to_dict('index')
out['commercial_by_condition']=pd.crosstab(p.condition,p.commercial,normalize='index').round(3).to_dict('index')
out['commercial_LC_CO_by_model']=pd.crosstab(p[p.condition=='LC_CO'].model,p[p.condition=='LC_CO'].commercial,normalize='index').round(3).to_dict('index')
out['contact_LC_CB_by_model']=pd.crosstab(p[p.condition=='LC_CB'].model,p[p.condition=='LC_CB'].contact,normalize='index').round(3).to_dict('index')
out['contact_CV_CONTACT_by_model']=pd.crosstab(p[p.condition=='CV_CONTACT'].model,p[p.condition=='CV_CONTACT'].contact,normalize='index').round(3).to_dict('index')
out['unparseable_agent']=int(a.f.isna().sum())
# omission tables
out['omission_by_model']={m:dict(lc=float(g[g.condition.isin(LC)].omit.mean()), cv=float(g[g.condition.isin(CV)].omit.mean())) for m,g in d.groupby('model')}
out['omission_by_framing']={m:dict(lc=float(g[g.condition.isin(LC)].omit.mean()), cv=float(g[g.condition.isin(CV)].omit.mean())) for m,g in d.groupby('framing')}
out['omission_by_condition']=d[d.condition!='NONE'].groupby('condition').omit.mean().round(4).to_dict()
olr=d[(d.model=='olmo2-13b')&(d.framing=='researcher')]
out['olmo_researcher_omission_by_condition']=olr[olr.condition!='NONE'].groupby('condition').omit.mean().round(4).to_dict()
out['omissions_count_by_model_framing']=d[d.condition!='NONE'].groupby(['model','framing']).omit.sum().to_dict()
out['omissions_count_by_model_framing']={f'{k[0]}|{k[1]}':int(v_) for k,v_ in out['omissions_count_by_model_framing'].items()}
out['lc_omissions_total']=int(d[d.condition.isin(LC)].omit.sum()); out['cv_omissions_total']=int(d[d.condition.isin(CV)].omit.sum())
out['lc_omissions_outside_olmo_researcher']=int(d[d.condition.isin(LC)&~((d.model=='olmo2-13b')&(d.framing=='researcher'))].omit.sum())
d['named']=[S.named_lc(t) for t in d.text]
out['named_given_lc_mention']=float(d[d.condition.isin(LC)&(d.mention==1)].named.mean())
out['truncated']=int((d.finish=='length').sum())
nt=d[d.finish!='length']; out['excl_trunc']=dict(lc=float(nt[nt.condition.isin(LC)].omit.mean()), cv=float(nt[nt.condition.isin(CV)].omit.mean()))
d['name_only']=[S.mentions_by_name(t,c) if c in S.NAMES else np.nan for t,c in zip(d.text,d.condition)]
out['name_only_omission']=dict(lc=float(1-d[d.condition.isin(LC)].name_only.mean()), cv=float(1-d[d.condition.isin(CV)].name_only.mean()))
out['uri_cue']=dict(LC_CB=float(d[d.condition=='LC_CB'].omit.mean()), LC_CB_NOURI=float(d[d.condition=='LC_CB_NOURI'].omit.mean()))
# V2, V3 as in supplementary.py
import re
NOTBIND=re.compile(r"not\s+(a\s+)?legal(ly)?\s+(binding|restriction|requirement|obligation)|no\s+legal\s+(weight|force|effect)|does\s+not\s+impose\s+(any\s+)?legal|not\s+legally\s+(binding|enforceable)|not\s+a\s+legal\s+barrier|\bcourtesy\b|not\s+(a\s+)?(binding|enforceable)", re.I)
t=d[(d.framing!='agent')&(d.condition!='NONE')&(d.mention==1)].copy(); t['nb']=[bool(NOTBIND.search(S.strip_echo(x))) for x in t.text]
out['V2_by_condition']=t.groupby('condition').nb.mean().round(3).to_dict()
t['courtesy_only']=[bool(re.search(r'\bcourtesy\b',S.strip_echo(x),re.I)) and not bool(re.sub(r'\\bcourtesy\\b\|','',NOTBIND.pattern) and re.search(re.sub(r'\\bcourtesy\\b\|','',NOTBIND.pattern),S.strip_echo(x),re.I)) for x in t.text]
out['V2_courtesy_only_by_condition']=t.groupby('condition').courtesy_only.mean().round(3).to_dict()
INVENT={"noncommercial": re.compile(r"non[- ]?commercial\s*(\(nc\))?\s*[:\-–]|\*\*non[- ]?commercial|you\s+may\s+not\s+use\s+the\s+(material|dataset|data|work)\s+for\s+commercial", re.I),
        "noderivatives": re.compile(r"no\s*-?\s*derivatives?|\bnoderivatives\b", re.I), "sharealike": re.compile(r"share\s*-?\s*alike", re.I)}
nn=d[(d.condition=='NONE')&(d.framing!='agent')].copy()
for k,rx in INVENT.items(): nn[k]=[bool(rx.search(S.strip_echo(x))) for x in nn.text]
nn['any']=nn[list(INVENT)].any(axis=1)
out['V3_by_model']=nn.groupby('model')[list(INVENT)+['any']].mean().round(3).to_dict()
out['V3_olmo_by_framing']=nn[nn.model=='olmo2-13b'].groupby('framing')['any'].mean().round(3).to_dict()
json.dump(out,open(R+'review/reviewer_checks/recompute.json','w'),indent=1,default=float)
print(json.dumps(out,indent=1,default=float))
