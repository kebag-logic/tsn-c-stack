#!/usr/bin/env python3
"""Audit the published merge, tracked bytes/modes/index, and gitlinks.
Usage: python3 integrity.py REPO OUTPUT
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
repo,out=map(Path,sys.argv[1:])
def git(*args): return subprocess.check_output(["git", "-C",str(repo),*args])
head="4c939ef18741916df85a355973db007b588604e0"
prior="0a1a14a1cc0e8cc99cb7a21ed43c391f7001dc6d"
main="51870377c5012766a8ea1d9798e3c499ca1060a3"
assert git("rev-parse","HEAD").decode().strip()==head
assert git("rev-parse","HEAD^{tree}").decode().strip()=="f1adface0d762b1b3a456a6159d750c50cf623f1"
rows=[];gitlinks=[]
for entry in git("ls-tree","-rz","HEAD").split(b"\0"):
 if not entry: continue
 meta,path=entry.split(b"\t",1)
 mode,kind,oid=meta.decode().split(); path=path.decode()
 if mode=="160000": gitlinks.append(dict(path=path,oid=oid)); continue
 pth=repo/path
 data=pth.read_bytes()
 actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
 actual_mode="100755" if pth.stat().st_mode & 0o111 else "100644"
 assert actual==oid and actual_mode==mode,(path,mode,actual_mode)
 rows.append(dict(path=path,mode=mode,blob=oid,sha256=hashlib.sha256(data).hexdigest()))
assert not git("diff","--cached","--raw","HEAD")
assert not git("diff","--raw","HEAD")
assert not git("status","--porcelain")
index_tree=git("write-tree").decode().strip()
assert index_tree=="f1adface0d762b1b3a456a6159d750c50cf623f1"
def plants(ref): return {x["name"]:x for x in json.loads(git("show",ref+":tests/mutations.json"))}
a,b,c=map(plants,[prior,main,head])
assert set(a)|set(b)==set(c)
assert all(c[k]==v for k,v in b.items())
assert all(c[k]==v for k,v in a.items() if k.startswith("entity-"))
changed=[k for k in a if a[k]!=c[k]]
assert changed==["own-discover-discarded"]
assert not git("diff",main,head,"--","src","include")
assert not git("diff",prior,head,"--","examples/entities")
def suppressions(ref):
 text=git("show",ref+":scripts/static_analysis.py").decode()
 return sorted(re.findall(r'"(--(?:suppress|checks)=[^"]+)"',text))
subs={ref:suppressions(ref) for ref in [prior,main,head]}
normalize=lambda x: re.sub(r"(smoke.c:)\d+",r"\1<line>",x)
assert {normalize(x) for x in subs[head]}=={normalize(x) for ref in [prior,main] for x in subs[ref]}
report=dict(head=head,tree=index_tree,parents=git("show","-s","--format=%P",head).decode().strip().split(),
 tracked_files=rows,gitlinks=gitlinks,clean_worktree=True,byte_mode_index_check="PASS",
 merge_audit=dict(prior_count=len(a),main_count=len(b),merged_count=len(c),all_names_preserved=True,
 main_plants_exact=True,entity_plants_exact=True,changed_prior_plants=changed,
 suppressions=subs,core_and_headers_match_main=True,goldens_match_prior=True))
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="tracked_files"},indent=2))
print("Verified tracked files:",len(rows))
