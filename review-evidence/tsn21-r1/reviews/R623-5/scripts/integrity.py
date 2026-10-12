#!/usr/bin/env python3
"""Check all source bytes, executable modes, index, head and gitlinks."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess

p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=a.source.resolve();packet=Path(__file__).resolve().parents[1]
head='405dc68310a18f669049ffc10cc23eef7300dcff'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True)
items=[];links=[]
for line in git('ls-tree','-r',head).splitlines():
    meta,name=line.split('\t');mode,kind,oid=meta.split()
    if mode=='160000':
        links.append(dict(path=name,gitlink=oid,actual=git('-C',str(root/name),'rev-parse','HEAD').strip()))
        continue
    path=root/name;data=path.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    actual='100755' if path.stat().st_mode&stat.S_IXUSR else '100644'
    items.append(dict(path=name,blob=oid,bytes_match=blob==oid,mode_match=actual==mode))
result=dict(head=git('rev-parse','HEAD').strip(),tree=git('rev-parse',head+'^{tree}').strip(),
            index_tree=git('write-tree').strip(),tracked=items,gitlinks=links,status=git('status','--porcelain'))
if (result['head']!=head or result['index_tree']!=result['tree'] or result['status']
    or not all(x['bytes_match'] and x['mode_match'] for x in items)
    or not all(x['gitlink']==x['actual'] for x in links)):
    raise RuntimeError('exact-head integrity failed')
(packet/'receipts/final-integrity.json').write_text(json.dumps(result,indent=2)+'\n')
print('Exact source head, tracked bytes/modes, index and gitlinks verified.')
