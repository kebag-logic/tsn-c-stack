#!/usr/bin/env python3
"""Compare the accepted host-header limitation without changing the checkout."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tarfile
import io

p=argparse.ArgumentParser(); p.add_argument('root',type=Path); p.add_argument('--gtest',type=Path,required=True); a=p.parse_args()
root=a.root.resolve(); packet=Path(__file__).resolve().parents[1]
base=packet/'scratch/baseline'
base.mkdir(exist_ok=True)
data=subprocess.check_output(['git','archive','1a9f651cdf7846b8e10ac246a6ef6916960fbb92'],cwd=root)
with tarfile.open(fileobj=io.BytesIO(data)) as archive: archive.extractall(base,filter='data')
out=packet/'receipts/sanitizer-limit'; out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,LD_LIBRARY_PATH=str(packet/'scratch/clang18/usr/lib/x86_64-linux-gnu'))
cc=packet/'scratch/clang18/usr/bin/clang++-18'

def check(item):
    name,tree=item
    argv=[str(cc),'-std=c++20','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
          '-fno-omit-frame-pointer','-I'+str(a.gtest/'include'),'-I'+str(tree/'include'),
          '-fsyntax-only',str(tree/'tests/test_acmp.cpp')]
    r=subprocess.run(argv,cwd=tree,env=env,capture_output=True,text=True,timeout=120)
    (out/(name+'.log')).write_text(repr(argv)+'\n'+r.stdout+r.stderr)
    (out/(name+'.rc')).write_text(str(r.returncode)+'\n')
    return {'case':name,'rc':r.returncode,'first_error':next((line for line in r.stderr.splitlines() if 'error:' in line),'')}

with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(check,[('base',base),('head',root)]))
assert all(r['rc']!=0 for r in results)
assert results[0]['first_error']==results[1]['first_error']
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
