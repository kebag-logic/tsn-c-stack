#!/usr/bin/env python3
"""Extract pinned packages into packet scratch; never install system packages."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

p=argparse.ArgumentParser()
p.add_argument('compiler_packages',type=Path)
a=p.parse_args()
packet=Path(__file__).resolve().parents[1]
sdk=packet/'scratch/sdk'; sdk.mkdir(parents=True,exist_ok=True)
packages=packet/'scratch/packages'; packages.mkdir(exist_ok=True)
records=[]
for item in json.loads((packet/'receipts/public-evidence/author/PACKAGES.json').read_text()):
    path=packages/item['package']
    urllib.request.urlretrieve(item['url'],path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise RuntimeError('package digest mismatch: '+path.name)
for path in sorted(list(a.compiler_packages.glob('*.deb'))+list(packages.glob('*.deb'))):
    members=subprocess.check_output(['ar','t',str(path)],text=True).splitlines()
    member=next(n for n in members if n.startswith('data.tar.'))
    data=subprocess.check_output(['ar','p',str(path),member])
    archive=packages/(path.name+'.'+member)
    archive.write_bytes(data)
    subprocess.run(['tar','-xf',str(archive),'-C',str(sdk)],check=True)
    records.append(dict(package=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
bindir=packet/'scratch/bin'; bindir.mkdir(exist_ok=True)
wrapper='''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
sdk=Path(__file__).resolve().parents[1]/'sdk'
name=Path(sys.argv[0]).name
os.environ['LD_LIBRARY_PATH']=str(sdk/'usr/lib/x86_64-linux-gnu')+os.pathsep+os.environ.get('LD_LIBRARY_PATH','')
args=sys.argv[1:]
if name=='clang-tidy':
    binary=sdk/'usr/bin/clang-tidy-18'
else:
    binary=sdk/'usr/bin/clang-18'
    if name=='clang++':
        args=['--driver-mode=g++','-nostdinc++','-isystem',str(sdk/'usr/include/c++/13'),'-isystem',str(sdk/'usr/include/x86_64-linux-gnu/c++/13'),'-isystem',str(sdk/'usr/include/c++/13/backward')]+args
os.execv(str(binary),[str(binary),*args])
'''
for name in ['clang','clang++','clang-18','clang-tidy']:
    path=bindir/name; path.write_text(wrapper); path.chmod(0o755)
(packet/'receipts/reviewer-packages.json').write_text(json.dumps(records,indent=2)+'\n')
print('Pinned SDK extracted; wrappers created in packet scratch.')
