#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare exact core tokens and line positions, plus six imported cases."""
import difflib,hashlib,json,pathlib,subprocess,sys
root,packet=map(lambda s:pathlib.Path(s).resolve(),sys.argv[1:]);sys.path.insert(0,str(root/"scripts"))
from compiler_tokens import raw_tokens
base="1a9f651cdf7846b8e10ac246a6ef6916960fbb92"
def git(path,ref):return subprocess.check_output(["git","-C",str(root),"show",ref+":"+path]).decode()
def toks(s,lang="c"):
 return [(kind,val,row) for kind,val,start,end,row in raw_tokens(s,lang) if kind!="comment" and not (kind=="unknown" and val.isspace())]
results=[]
for ext,d in [("c","src"),("h","include")]:
 path=d+"/acmp."+ext;head=(root/path).read_text(); b=git(path,base); ref=(packet/"receipts"/("authority-acmp."+ext)).read_text(); old=(packet/"receipts"/("baseline-acmp."+ext)).read_text()
 ht,rt,bt,ot=map(toks,[head,ref,b,old]);same=lambda a,b:[x[:2] for x in a]==[x[:2] for x in b]
 changes=difflib.SequenceMatcher(None,b.splitlines(True),head.splitlines(True),autojunk=False).get_opcodes();deleted=[x for x in changes if x[0] not in ("equal","insert")]
 item={"path":path,"head_tokens":len(ht),"reference_tokens":len(rt),"head_token_identity":same(ht,rt),"head_token_line_identity":ht==rt,"baseline_tokens":len(bt),"baseline_identity":same(bt,ot),"baseline_token_line_identity":bt==ot,"round2_token_identity":same(ht,toks(git(path,"2dcbe91ead981591d5bfb652f6616f6edb325875"))),"baseline_bytes_preserved_by_insertions_only":not deleted,"head_lines":len(head.splitlines()),"reference_lines":len(ref.splitlines())}
 assert all(item[x] for x in ["head_token_identity","head_token_line_identity","baseline_identity","baseline_token_line_identity","round2_token_identity","baseline_bytes_preserved_by_insertions_only"])
 results.append(item)
def cases(s):
 ts=[x[:2] for x in toks(s,"c++")];out={}
 for i,t in enumerate(ts):
  if t[1]=="TEST_F" and i+6<len(ts) and ts[i+4][1].startswith("A31"):
   n=ts[i+4][1];start=i;body=i+6;depth=0
   for j in range(body,len(ts)):
    if ts[j][1]=="{":depth+=1
    if ts[j][1]=="}":
     depth-=1
     if depth==0:out[n]=ts[start:j+1];break
 return out
h=cases((root/"tests/test_acmp.cpp").read_text());r=cases((packet/"receipts/authority-test_acmp.cpp").read_text());assert len(r)==6 and all(h[k]==v for k,v in r.items())
out={"core":results,"upstream_cases":list(r),"six_upstream_bodies_token_equal":True,"head_case_count":len(h)}
(packet/"receipts/token-identity.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
