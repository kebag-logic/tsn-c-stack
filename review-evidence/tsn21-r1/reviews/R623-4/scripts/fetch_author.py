#!/usr/bin/env python3
import concurrent.futures, hashlib, json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
tree=json.loads((P/"receipts/author-r3-tree.json").read_text())["tree"]
selected=[x for x in tree if x["type"]=="blob" and x["path"].startswith("round3/") and not any(s in x["path"] for s in ("receipt-manifest", "residuals.json", "review-audit", "audit-review", "review-ready", "review-memory"))]
def fetch(x):
 p=P/"receipts/published-author"/x["path"]; p.parent.mkdir(parents=True,exist_ok=True)
 r=subprocess.run(["gh","api","-H","Accept: application/vnd.github.raw+json", "repos/kebag-logic/tsn-c-stack/git/blobs/"+x["sha"]],capture_output=True,check=True,timeout=90)
 b=r.stdout; assert hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()==x["sha"],x["path"]
 p.write_bytes(b)
 return {"path":str(p.relative_to(P)),"git_blob":x["sha"],"sha256":hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e: results=list(e.map(fetch,selected))
(P/"receipts/published-downloads.json").write_text(json.dumps(results,indent=2)+"\n")
print("Verified public author receipts:",len(results))
