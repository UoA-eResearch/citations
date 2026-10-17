"""Draw the reviewer's re-scoring sample: 2 per (model x framing x non-NONE condition) cell = 162, plus every scored
Local Contexts omission (48), plus 30 of OLMo-2's researcher CV_NC omissions and 30 extra OLMo-2 researcher mentions.
Seed 20261017+1. Writes sample.jsonl (with the scorer's verdict and the matched span, for the reviewer's reading)."""
import json, sys, re, collections
import numpy as np, pandas as pd
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0, R+'code'); import score as S
rows=[]
for m in ['qwen3-32b','olmo2-13b','mistral-small-24b']:
    rows+=[json.loads(l) for l in open(R+f'results/generations/{m}_main.jsonl')]
d=pd.DataFrame(rows); d=d[d.condition!='NONE'].reset_index(drop=True)
d['mention']=[S.mentions(t,c) for t,c in zip(d.text,d.condition)]
rng=np.random.default_rng(20261018)
picks=[]
for (m,f,c),g in d.groupby(['model','framing','condition']):
    picks+=list(rng.choice(g.index,2,replace=False))
strat=set(picks)
lc_om=list(d[d.condition.isin(S.LC_CONDITIONS)&(d.mention==0)].index)
cv_om=list(d[(d.model=='olmo2-13b')&(d.framing=='researcher')&(d.condition=='CV_NC')&(d.mention==0)].index)
cv_om=list(rng.choice(cv_om,30,replace=False))
olmo_m=list(d[(d.model=='olmo2-13b')&(d.framing=='researcher')&(d.mention==1)&~d.index.isin(strat)].index)
olmo_m=list(rng.choice(olmo_m,30,replace=False))
sel=list(dict.fromkeys(picks+lc_om+cv_om+olmo_m))
s=d.loc[sel].copy(); s['stratum']=['cell' if i in strat else ('lc_omit' if i in lc_om else ('cv_omit' if i in cv_om else 'olmo_mention')) for i in sel]
s['id']=[f'r{i:03d}' for i in range(len(s))]
def span(t,c):
    m=re.search(S.PATTERNS[c],S.strip_echo(t),S.FLAGS)
    if not m: return None
    tt=S.strip_echo(t); return tt[max(0,m.start()-160):m.end()+160].replace('\n',' / ')
s['span']=[span(t,c) for t,c in zip(s.text,s.condition)]
s['stripped']=[S.strip_echo(t) for t in s.text]
s['echo_removed']=[len(t or '')-len(S.strip_echo(t)) for t in s.text]
with open(R+'review/reviewer_checks/sample.jsonl','w') as fh:
    for r in s.itertuples():
        fh.write(json.dumps(dict(id=r.id,doi=r.doi,model=r.model,framing=r.framing,condition=r.condition,stratum=r.stratum,auto=int(r.mention),span=r.span,echo_removed=int(r.echo_removed),text=r.stripped),ensure_ascii=False)+'\n')
print(len(s), s.stratum.value_counts().to_dict(), s.groupby(['stratum','mention']).size().to_dict())
