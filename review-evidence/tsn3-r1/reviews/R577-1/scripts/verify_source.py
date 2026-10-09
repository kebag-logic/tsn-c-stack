#!/usr/bin/env python3
"""Verify raw tracked bytes, modes, index and gitlinks against the review head."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args(); root=a.source.resolve()
def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert head=='66b3a75746fbbca3cffdfc7d89f013ab14aa1cc0'
assert tree=='231e90357e5efe0101ed7fdd42c8b5ae2b25a89f'
expected={}; rows=[]; links=[]; errors=[]
for entry in git('ls-tree','-r','-z','HEAD').split(b'\0'):
    if not entry: continue
    meta,name=entry.split(b'\t',1); mode,kind,oid=meta.decode().split()
    name=name.decode(); expected[name]=(mode,oid)
    if kind=='commit':
        child=subprocess.check_output(['git','-C',str(root/name),'rev-parse','HEAD']).decode().strip()
        links.append(dict(path=name,expected=oid,actual=child))
        if child!=oid: errors.append(name)
        continue
    path=root/name
    raw=os.fsencode(os.readlink(path)) if mode=='120000' else path.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    actual_mode='120000' if path.is_symlink() else ('100755' if path.stat().st_mode&0o111 else '100644')
    if actual!=oid or actual_mode!=mode: errors.append(name)
    rows.append(dict(path=name,mode=mode,git_blob=actual,sha256=hashlib.sha256(raw).hexdigest()))
index={}
for entry in git('ls-files','--stage','-z').split(b'\0'):
    if not entry: continue
    meta,name=entry.split(b'\t',1); mode,oid,stage=meta.decode().split()
    if stage!='0': errors.append('unmerged index')
    index[name.decode()]=(mode,oid)
if index!=expected: errors.append('index differs from HEAD tree')
result=dict(head=head,tree=tree,tracked_files=len(rows),gitlinks=links,
            index_matches=index==expected,raw_bytes_and_modes_match=not errors,
            worktree_status=git('status','--porcelain=v1').decode(),errors=errors,files=rows)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
raise SystemExit(bool(errors))
