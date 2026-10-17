"""Does the V3 'invented terms' regex count OLMo-2 explaining that NC/ND/SA do NOT apply to CC BY? For each INVENT hit,
look at the window round the match for a disclaimer. Prints the classification and 12 hits with no disclaimer for reading."""
import json, re, sys, collections
import numpy as np
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0,R+'code'); import score as S
INVENT={"noncommercial": re.compile(r"non[- ]?commercial\s*(\(nc\))?\s*[:\-–]|\*\*non[- ]?commercial|you\s+may\s+not\s+use\s+the\s+(material|dataset|data|work)\s+for\s+commercial", re.I),
        "noderivatives": re.compile(r"no\s*-?\s*derivatives?|\bnoderivatives\b", re.I), "sharealike": re.compile(r"share\s*-?\s*alike", re.I)}
DISCLAIM=re.compile(r"not\s+applicable|not\s+activated|does\s+not\s+apply|doesn'?t\s+apply|not\s+(a\s+)?(part|component|requirement|condition)\s+of|not\s+included|no\s+such|is\s+not\s+(required|a\s+restriction|present|specified)|are\s+not\s+(required|restrictions|present|specified)|\boptional\b|unlike\s+(the\s+)?(cc\s*)?by[- ]?(nc|nd|sa)|only\s+if|would\s+(apply|be\s+required)|if\s+(it|the\s+licen[cs]e)\s+(were|had|included)|not\s+(an?\s+)?(nc|nd|sa)\b|no\s+(nc|nd|sa)\b|free\s+to\s+use\s+.{0,40}commercial|can\s+be\s+used\s+.{0,30}commercial|allows?\s+commercial|permits?\s+commercial|commercial\s+use\s+is\s+(allowed|permitted)", re.I)
rows=[json.loads(l) for l in open(R+'results/generations/olmo2-13b_main.jsonl')]
none=[r for r in rows if r['condition']=='NONE' and r['framing']!='agent']
cls=collections.Counter(); nod=[]
for r in none:
    t=S.strip_echo(r['text']); hit=False; disc=False; assertive=False
    for k,rx in INVENT.items():
        for m in rx.finditer(t):
            hit=True; w=t[max(0,m.start()-200):m.end()+250]
            if DISCLAIM.search(w): disc=True
            else: assertive=True
    if not hit: cls['no hit']+=1
    elif assertive and not disc: cls['hit, no disclaimer anywhere']+=1; nod.append(r)
    elif assertive and disc: cls['hit, mixed (some windows disclaim, some not)']+=1
    else: cls['hit, every window has a disclaimer']+=1
print('OLMo NONE prose responses', len(none)); print(cls)
# the model's own stated verdict on commercial use in the same responses: does it say commercial use allowed?
ALLOW=re.compile(r"(free\s+to|can|may|allowed\s+to|permitted\s+to)\s+(use|reuse|be\s+used)[^.]{0,60}commercial|commercial\s+(use|purposes)\s+(is|are)\s+(allowed|permitted)|even\s+commercially|including\s+commercial", re.I)
FORBID=re.compile(r"(not|cannot|can't|may\s+not|must\s+not)\s+(be\s+)?(used?|reused?)\s+[^.]{0,40}commercial|non[- ]?commercial\s+(use|purposes)\s+only|only\s+(for|be\s+used\s+for)\s+non[- ]?commercial|commercial\s+use\s+is\s+(not\s+(allowed|permitted)|prohibited|restricted)|without\s+(prior\s+)?permission", re.I)
c2=collections.Counter()
for r in none:
    t=S.strip_echo(r['text']); c2[(bool(ALLOW.search(t)), bool(FORBID.search(t)))]+=1
print('(says commercial allowed, says commercial forbidden/permission):', dict(c2))
rng=np.random.default_rng(11)
for r in rng.choice(nod, min(12,len(nod)), replace=False):
    t=S.strip_echo(r['text']); print('=====', r['framing'], r['doi'])
    for k,rx in INVENT.items():
        m=rx.search(t)
        if m: print(f'  [{k}] ...{t[max(0,m.start()-200):m.end()+250]}...'.replace('\n',' / '))
