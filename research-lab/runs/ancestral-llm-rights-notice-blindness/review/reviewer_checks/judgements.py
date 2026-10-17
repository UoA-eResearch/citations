"""Reviewer's judgements for the 270-response sample (read in full in review/reviewer_checks/sample_view.txt), the
agreement table, and the corrected omission rates / H2 implied by them. Rule applied: plan.md section 4 - a response
mentions the element if it names it OR states what it asks."""
import json, sys, collections
import numpy as np, pandas as pd
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0,R+'code'); import score as S
s=pd.read_json(R+'review/reviewer_checks/sample.jsonl', lines=True)
FALSE_OMISSION_LC={'r178':'LC_NC: "Non-Commercial (NC - mentioned in your metadata): You may not use the dataset for commercial purposes" - states what the element asks; NC regex misses the phrasing',
                   'r195':'LC_NC: "NonCommercial: You may not use the dataset for commercial purposes without separate permission" - states the restriction; regex misses the phrasing'}
BORDERLINE={'r187':'LC_BC: "check if there are any additional terms ... specified by the local context (as mentioned in the rightsList)" - alludes to the entry without naming or explaining it; counted as omission'}
rows=[]
for r in s.itertuples():
    if r.auto==1:
        j,note=1,'genuine mention (name or content of the inserted element in the model\'s own output)'
        if r.framing=='agent': note='element string listed verbatim in the JSON "conditions" field'
    elif r.condition=='CV_NC':
        j,note=1,'FALSE OMISSION: states the non-commercial restriction ("may not use the dataset for commercial purposes" / "can be used for non-commercial purposes"); NC regex misses the phrasing'
    elif r.id in FALSE_OMISSION_LC: j,note=1,FALSE_OMISSION_LC[r.id]
    elif r.id in BORDERLINE: j,note=0,BORDERLINE[r.id]
    else: j,note=0,'true omission: the response recites CC BY (with hallucinated SA/NC/ND clauses) and never refers to the second rights entry'
    rows.append(dict(id=r.id,model=r.model,framing=r.framing,condition=r.condition,stratum=r.stratum,auto=r.auto,reviewer=j,note=note))
J=pd.DataFrame(rows); J.to_csv(R+'review/reviewer_checks/reviewer_judgements.csv',index=False)
out={}
out['n']=len(J)
out['agreement_by_stratum']={k:dict(n=int(len(g)),agree=int((g.auto==g.reviewer).sum()),auto1_rev1=int(((g.auto==1)&(g.reviewer==1)).sum()),auto0_rev0=int(((g.auto==0)&(g.reviewer==0)).sum()),auto0_rev1=int(((g.auto==0)&(g.reviewer==1)).sum()),auto1_rev0=int(((g.auto==1)&(g.reviewer==0)).sum())) for k,g in J.groupby('stratum')}
out['overall']=dict(auto1_rev1=int(((J.auto==1)&(J.reviewer==1)).sum()),auto0_rev0=int(((J.auto==0)&(J.reviewer==0)).sum()),auto0_rev1=int(((J.auto==0)&(J.reviewer==1)).sum()),auto1_rev0=int(((J.auto==1)&(J.reviewer==0)).sum()))
om=J[J.auto==0]
out['false_omission_share_among_scored_omissions_in_sample']=float((om.reviewer==1).mean())
out['false_omission_by_condition_group']={'CV_NC_olmo_researcher':f"{int(((om.condition=='CV_NC')&(om.reviewer==1)).sum())}/{int((om.condition=='CV_NC').sum())}",'LC_conditions':f"{int((om.condition.isin(S.LC_CONDITIONS)&(om.reviewer==1)).sum())}/{int(om.condition.isin(S.LC_CONDITIONS).sum())}"}
# population-level correction: all 93 OLMo-researcher CV_NC scored omissions state the restriction (nc_cell_check.py: 93/93); LC: 2 of 48 false
d=pd.read_csv(R+'results/tables/scored_main.csv')
lc=d[d.condition.isin(S.LC_CONDITIONS)]; cv=d[d.condition.isin(S.CV_CONDITIONS)]
lc_om=int((1-lc.mention).sum()); cv_om=int((1-cv.mention).sum())
out['corrected']=dict(lc_omissions=lc_om-2, lc_rate=(lc_om-2)/len(lc), cv_omissions=cv_om-93, cv_rate=(cv_om-93)/len(cv), h2_diff=(lc_om-2)/len(lc)-(cv_om-93)/len(cv))
# H3 variant: definite-direction change only, with a record bootstrap
rows=[]
for m in ['qwen3-32b','olmo2-13b','mistral-small-24b']: rows+=[json.loads(l) for l in open(R+f'results/generations/{m}_main.jsonl')]
g=pd.DataFrame(rows); a=g[g.framing=='agent'].copy(); a['f']=[S.agent_fields(t) for t in a.text]
base={(r.doi,r.model):r.f for r in a[a.condition=='NONE'].itertuples()}
lcx=a[a.condition.isin(S.LC_CONDITIONS)].copy(); lcx['b']=[base.get((r.doi,r.model)) for r in lcx.itertuples()]
v=lcx[lcx.f.notna()&lcx.b.notna()].copy()
def definite(f,b): return any(x!=y and y!='unclear' for x,y in zip(b,f))
v['def']=[definite(f,b) for f,b in zip(v.f,v.b)]
recs=sorted(v.doi.unique()); idx={k:i for i,k in enumerate(recs)}; n=len(recs)
sm=np.zeros(n); ct=np.zeros(n)
for k,r in v.groupby('doi')['def'].agg(['sum','count']).iterrows(): sm[idx[k]]=r['sum']; ct[idx[k]]=r['count']
rng=np.random.default_rng(7); vals=[]
for _ in range(2000):
    w=np.bincount(rng.integers(0,n,n),minlength=n); vals.append((w*sm).sum()/(w*ct).sum())
out['H3_definite_change']=dict(est=float(sm.sum()/ct.sum()), ci=(float(np.percentile(vals,2.5)),float(np.percentile(vals,97.5))))
json.dump(out,open(R+'review/reviewer_checks/rescoring_summary.json','w'),indent=1)
print(json.dumps(out,indent=1))
