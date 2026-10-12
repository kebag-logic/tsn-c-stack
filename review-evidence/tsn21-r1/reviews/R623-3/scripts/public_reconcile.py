#!/usr/bin/env python3
"""Read PR metadata after the independent verdict; never emit review bodies."""
import datetime,hashlib,json,pathlib,re,subprocess,sys
packet=pathlib.Path(sys.argv[1]).resolve();proof=json.loads((packet/"receipts/independent-verdict-record.json").read_text())
assert hashlib.sha256((packet/"receipts/independent-verdict.md").read_bytes()).hexdigest()==proof["sha256"]
assert proof["verdict"] in ("POSITIVE","NEGATIVE")
rows=[]
for endpoint in ["issues/22/comments","pulls/22/reviews","pulls/22/comments"]:
 pages=json.loads(subprocess.check_output(["gh","api","--paginate","--slurp","repos/kebag-logic/tsn-c-stack/"+endpoint+"?per_page=100"]))
 for c in [c for page in pages for c in page]:
  b=c.get("body") or "";row={"url":c.get("html_url"),"finding_ids":sorted(set(re.findall(r"\b(?:F|P)-\d+\b",b)))}
  if re.match(r"\s*\[A10\]",b):row["manager_body"]=b
  rows.append(row)
  print(json.dumps(row,ensure_ascii=False))
result={"retrieved_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"independent_verdict_sha256":proof["sha256"],"comments":rows,"policy":"Only manager bodies and finding IDs retained; all other bodies discarded."}
(packet/"receipts/public-reconciliation.json").write_text(json.dumps(result,indent=2)+"\n")
