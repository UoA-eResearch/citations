"""Readable view of the re-scoring sample: for responses the scorer marked as mentions, the first two matched spans; for
LC omissions the full stripped text; for CV_NC omissions the cue-word contexts. Written to sample_view.txt."""
import json, re, sys
R='/mnt/citations/research-lab/runs/ancestral-llm-rights-notice-blindness/'
sys.path.insert(0,R+'code'); import score as S
CUES={'CV_NC': r"commercial|\bnc\b|attribution[- ]non|by[- ]nc|licen[cs]e", 'CV_CONTACT': r"contact|collaborat|touch|reach", 'CV_DUA': r"agreement|\bdua\b",
      'LC': r"local|contexts|\btk\b|traditional|knowledge|notice|label|collab|cultur|communit|indigen|biocultur|\bbc\b|rights"}
out=[]
for l in open(R+'review/reviewer_checks/sample.jsonl'):
    r=json.loads(l); t=r['text']
    hdr=f"### {r['id']} | {r['model']} | {r['framing']} | {r['condition']} | {r['stratum']} | auto={r['auto']} | echo_removed={r['echo_removed']} | len={len(t)}"
    if r['auto']==1:
        ms=list(re.finditer(S.PATTERNS[r['condition']], t, S.FLAGS))[:2]
        body='\n'.join(f"  >> ...{t[max(0,m.start()-170):m.end()+170]}...".replace('\n',' / ') for m in ms)
    elif r['condition'] in S.LC_CONDITIONS or r['stratum']=='cell':
        body='  FULL: '+t.replace('\n',' / ')
    else:
        cue=CUES.get(r['condition'],CUES['LC'])
        ctx=[f"  [{m.group(0)}] ...{t[max(0,m.start()-150):m.end()+150]}...".replace('\n',' / ') for m in list(re.finditer(cue,t,re.I))[:6]]
        body='  HEAD: '+t[:350].replace('\n',' / ')+'\n'+'\n'.join(ctx)
    out.append(hdr+'\n'+body+'\n')
open(R+'review/reviewer_checks/sample_view.txt','w').write('\n'.join(out))
print(len(out), 'items;', sum(len(x) for x in out), 'chars')
