#!/usr/bin/env python3
"""Verify every tracked working byte, mode, index entry and gitlink against HEAD."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('checkout', type=Path)
a=p.parse_args()
root=a.checkout.resolve()
def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args])
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert head=='663f14de4a07bb1a777282fdfc83d30fd03843d4'
assert tree=='cff76b8564bc21ff16a57c2e32f4abe1b6d3e3e9'
expected={}
links=[]
for row in git('ls-tree','-rz','HEAD').split(b'\0'):
    if not row: continue
    metadata, path=row.split(b'\t',1)
    mode, kind, oid=metadata.decode().split()
    path=path.decode()
    expected[path]=(mode,oid)
    if mode=='160000':
        links.append({'path':path,'commit':oid})
        assert subprocess.check_output(['git','-C',str(root/path),'rev-parse','HEAD']).decode().strip()==oid
        continue
    f=root/path
    content=os.readlink(f).encode() if mode=='120000' else f.read_bytes()
    got=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
    assert got==oid, path
    if mode!='120000': assert bool(f.stat().st_mode&0o111)==(mode=='100755'),path
index={}
for row in git('ls-files','--stage','-z').split(b'\0'):
    if not row: continue
    metadata,path=row.split(b'\t',1)
    mode,oid,stage=metadata.decode().split()
    assert stage=='0'
    index[path.decode()]=(mode,oid)
assert index==expected
assert git('diff','18d73783..HEAD','--','src','include')==b''
assert git('diff','--cached','--exit-code')==b''
print(json.dumps({'head':head,'tree':tree,'tracked_entries':len(expected),
                  'tracked_bytes_modes_and_index':'PASS','gitlinks':links,
                  'src_include_identical_to_base':True},indent=2))
