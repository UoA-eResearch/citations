"""Reviewer check 6: how many 'opinions' in one shard (cluster_id % 32 == 0, 1/32 of the corpus) look like party
filings? Heuristic markers in the first 3,000 characters (caption/title) and the last 3,000 (signature block)."""
import gzip, json, re, random, sys, html
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
TAG = re.compile(r"<[^>]+>")
HEAD = re.compile(r"\b(MOTION|PETITION|BRIEF|COMPLAINT|RESPONSE|REPLY|OBJECTION|APPLICATION|NOTICE OF APPEAL|MEMORANDUM OF LAW|MEMORANDUM IN SUPPORT|OPPOSITION)\b")
ONLYHEAD = re.compile(r"(PLAINTIFF'?S?|DEFENDANT'?S?|APPELLANT'?S?|APPELLEE'?S?|PETITIONER'?S?|RESPONDENT'?S?|MOVANT'?S?|DEBTOR'?S?)\s+(MOTION|PETITION|BRIEF|RESPONSE|REPLY|OBJECTION|MEMORANDUM|OPPOSITION|APPLICATION|COMPLAINT|STATEMENT|ANSWER)")
TAIL = re.compile(r"(Respectfully submitted|RESPECTFULLY SUBMITTED|CERTIFICATE OF SERVICE|Certificate of Service|COMES NOW|Comes now|WHEREFORE, (?:Plaintiff|Defendant|Appellant|Petitioner|Movant)|Attorney for (?:Plaintiff|Defendant|Appellant|Appellee|Petitioner|Respondent)|Pro Se|pro se litigant|SO ORDERED)")
JUDGE = re.compile(r"(It is (?:so |hereby )?ordered|IT IS (?:SO |HEREBY )?ORDERED|OPINION|MEMORANDUM OPINION|ORDER|JUDGMENT|Affirmed|AFFIRMED|Reversed|REVERSED|we conclude|we hold|the court finds|The Court finds|J\.,? delivered|J\.,? concur|PER CURIAM|Per Curiam)")
shard = sys.argv[1] if len(sys.argv) > 1 else "00"
n = 0; sus = []; rng = random.Random(7); sample = []
for line in gzip.open(f"{RUN}/data/opinions/shard_{shard}.jsonl.gz", "rt", encoding="utf-8"):
    rec = json.loads(line)
    if not (20230101 <= rec["date"] <= 20260930): continue
    n += 1
    t = rec["raw"]
    if rec["field"] != "plain_text": t = html.unescape(TAG.sub(" ", t))
    t = " ".join(t.split())
    head, tail = t[:3000], t[-3000:]
    h = ONLYHEAD.search(head); tl = TAIL.search(tail); rs = re.search(r"Respectfully submitted|RESPECTFULLY SUBMITTED", t)
    cos = re.search(r"CERTIFICATE OF SERVICE|Certificate of Service", t)
    score = int(bool(h)) + int(bool(rs)) + int(bool(cos))
    if score >= 2:
        sus.append({"opinion_id": rec["opinion_id"], "cluster_id": rec["cluster_id"], "date": rec["date"], "type": rec["type"], "ocr": rec["ocr"],
                    "head_hit": h.group(0) if h else None, "resp_sub": bool(rs), "cert_serv": bool(cos), "head": head[:400], "tail": tail[-300:]})
    if rng.random() < 0.0004:
        sample.append({"opinion_id": rec["opinion_id"], "type": rec["type"], "head": head[:500]})
out = {"shard": shard, "screened_period_docs": n, "suspect_filings_score2plus": len(sus), "share": round(len(sus) / max(1, n), 5), "suspects": sus, "random_sample_heads": sample}
json.dump(out, open(f"{RUN}/review/reviewer_checks/party_filing_scan_{shard}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("suspects", "random_sample_heads")}))
for s in sus[:40]:
    print("---", s["opinion_id"], s["type"], s["head_hit"], "| RS", s["resp_sub"], "CoS", s["cert_serv"]); print("   ", s["head"][:300])
