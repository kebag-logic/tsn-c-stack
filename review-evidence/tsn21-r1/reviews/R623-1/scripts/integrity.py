#!/usr/bin/env python3
"""Read-only verification of exact commit, tree, index, file bytes, modes and gitlinks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

p=argparse.ArgumentParser(); p.add_argument('root',type=Path); a=p.parse_args()
root=a.root.resolve(); packet=Path(__file__).resolve().parents[1]
def git(*args): return subprocess.check_output(['git','--no-replace-objects',*args],cwd=root)
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert head=='2dcbe91ead981591d5bfb652f6616f6edb325875'
assert tree=='977d677410f6d44f4b54301a10273f41600c3edc'
entries=git('ls-tree','-rz','HEAD').split(b'\0')
rows=[]; links=[]
index=git('ls-files','--stage','-z').split(b'\0')
expected_index=[]
for entry in filter(None,entries):
    meta,name=entry.split(b'\t',1); mode,kind,oid=meta.decode().split(); name=name.decode()
    expected_index.append(f'{mode} {oid} 0\t{name}'.encode())
    path=root/name
    if kind=='commit':
        links.append({'path':name,'gitlink':oid})
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path).decode().strip()
        assert actual==oid
        continue
    st=path.lstat()
    if mode=='120000':
        assert stat.S_ISLNK(st.st_mode)
        content=os.readlink(path).encode()
    else:
        assert stat.S_ISREG(st.st_mode)
        assert bool(st.st_mode & 0o111)==(mode=='100755'),name
        content=path.read_bytes()
    digest=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
    assert digest==oid,name
    assert content==git('cat-file','blob',oid),name
    rows.append({'path':name,'mode':mode,'blob':oid,'sha256':hashlib.sha256(content).hexdigest()})
assert sorted(filter(None,index))==sorted(expected_index)
assert git('status','--porcelain=v1','--untracked-files=all')==b''
git('diff','--check','1a9f651c..HEAD')
receipt={'head':head,'tree':tree,'parent':git('rev-parse','HEAD^').decode().strip(),
         'tracked_files_verified':len(rows),'tracked_blobs_modes_and_index_equal':True,
         'gitlinks':links,'status':'clean','files':rows}
(packet/'receipts/final-integrity.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
