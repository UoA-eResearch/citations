"""The OLMo-2 researcher cell: the NC content pattern's false-positive rate on NONE by model x framing; name-only
omission for CV_NC / LC_NC by model x framing; and, among OLMo researcher CV_NC responses scored as omissions, how
many state a non-commercial restriction in other words (upper bound on false omissions) or name the licence."""
import json, re, sys, collections
import pandas as pd, numpy as np
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0,R+'code'); import score as S
rows=[]
for m in ['qwen3-32b','olmo2-13b','mistral-small-24b']: rows+=[json.loads(l) for l in open(R+f'results/generations/{m}_main.jsonl')]
d=pd.DataFrame(rows); d['t']=[S.strip_echo(x) for x in d.text]
none=d[d.condition=='NONE'].copy()
for pat in ['NC','CONTACT','DUA','CO','GEN_LC']:
    rx=getattr(S,pat); none[pat]=[bool(re.search(rx,t,S.FLAGS)) for t in none.t]
print('pattern hit rate on NONE responses (false-positive rate), by model x framing:')
print(none.groupby(['model','framing'])[['NC','CONTACT','DUA','CO','GEN_LC']].mean().round(3))
d['mention']=[S.mentions(x,c) if c in S.PATTERNS else np.nan for x,c in zip(d.text,d.condition)]
d['name']=[S.mentions_by_name(x,c) if c in S.NAMES else np.nan for x,c in zip(d.text,d.condition)]
for c in ['CV_NC','LC_NC']:
    g=d[d.condition==c]
    print(c, 'content omission by model x framing:'); print((1-g.groupby(['model','framing']).mention.mean()).round(3).unstack())
    print(c, 'name-only omission by model x framing:'); print((1-g.groupby(['model','framing']).name.mean()).round(3).unstack())
o=d[(d.condition=='CV_NC')&(d.model=='olmo2-13b')&(d.framing=='researcher')]
om=o[o.mention==0]
states=re.compile(r"non[- ]?commercial|not\s+(be\s+)?(use|used|reuse)[^.]{0,40}commercial|commercial\s+purposes?[^.]{0,40}(permission|not)", re.I)
names=re.compile(r"attribution[- ]non[- ]?commercial|by[- ]nc|non[- ]?commercial\s+4\.0", re.I)
print('OLMo researcher CV_NC: n', len(o), 'scored omission', len(om))
print('  of the omissions, state a non-commercial restriction in some words:', int(sum(bool(states.search(t)) for t in om.t)))
print('  of the omissions, name the CC BY-NC licence:', int(sum(bool(names.search(t)) for t in om.t)))
print('  of ALL OLMo researcher CV_NC responses, name the CC BY-NC licence:', int(sum(bool(names.search(t)) for t in o.t)), '/', len(o))
# the same for NONE OLMo researcher: how many name a BY-NC licence (should be 0) and how many state NC
n=none[(none.model=='olmo2-13b')&(none.framing=='researcher')]
print('OLMo researcher NONE: state NC restriction', int(sum(bool(states.search(t)) for t in n.t)), '/', len(n), '; name BY-NC', int(sum(bool(names.search(t)) for t in n.t)))
# what would CV omission and H2 be if CV_NC were scored by name (licence named) in the OLMo researcher cell only?
d2=d.copy(); mask=(d2.condition=='CV_NC')&(d2.model=='olmo2-13b')&(d2.framing=='researcher')
d2.loc[mask,'mention']=[bool(names.search(t)) for t in d2[mask].t]
lc=d2[d2.condition.isin(S.LC_CONDITIONS)]; cv=d2[d2.condition.isin(S.CV_CONDITIONS)]
print('CV omission if OLMo-researcher CV_NC scored by licence name:', round(1-cv.mention.mean(),4), '; LC', round(1-lc.mention.mean(),4), '; H2 diff', round((1-lc.mention.mean())-(1-cv.mention.mean()),4))
d3=d.copy(); d3.loc[mask,'mention']=[bool(states.search(t)) or bool(S.mentions(x,'CV_NC')) for t,x in zip(d3[mask].t,d3[mask].text)]
cv=d3[d3.condition.isin(S.CV_CONDITIONS)]
print('CV omission if any NC statement counts in that cell:', round(1-cv.mention.mean(),4), '; H2 diff', round((1-lc.mention.mean())-(1-cv.mention.mean()),4))
# LC omissions: cue words present?
lo=d[d.condition.isin(S.LC_CONDITIONS)&(d.mention==0)]
cue=re.compile(r"local\s*contexts|\btk\b|traditional|biocultur|indigen|notice|label|collaborat|communit|cultur", re.I)
print('LC omissions', len(lo), 'with any cue word:', int(sum(bool(cue.search(t)) for t in lo.t)), collections.Counter(lo.condition))
