#!/usr/bin/env python3
"""Extract public compiler compatibility packages under packet scratch only."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import urllib.request

p=argparse.ArgumentParser()
p.add_argument('packet',type=Path)
p.add_argument('--lexer',type=Path,required=True)
a=p.parse_args()
packet=a.packet.resolve()
sdk=packet/'scratch/compat'
sdk.mkdir(parents=True,exist_ok=True)
packages=[
 ('https://archive.ubuntu.com/ubuntu/pool/main/g/gcc-13/libstdc++-13-dev_13.2.0-23ubuntu4_amd64.deb',
  '0e34b7a6ad0d9db6c718301a0c30a077590decbb31099d0fd6ac957222d77a94'),
 ('https://archive.ubuntu.com/ubuntu/pool/universe/l/llvm-toolchain-18/libclang-rt-18-dev_18.1.3-1_amd64.deb',
  '2e406b65eb8426b8988ca28bcf6db8568348c8e3fb3bda8c034104a2b4f32ba4')]
receipts=[]
for url,expected in packages:
    f=sdk/url.rsplit('/',1)[-1]
    with urllib.request.urlopen(url,timeout=90) as r:
        data=r.read()
    assert hashlib.sha256(data).hexdigest()==expected
    f.write_bytes(data)
    members=subprocess.check_output(['ar','t',str(f)],text=True).splitlines()
    member=next(x for x in members if x.startswith('data.tar.'))
    archive=sdk/(f.name+'.'+member)
    archive.write_bytes(subprocess.check_output(['ar','p',str(f),member]))
    (sdk/'root').mkdir(exist_ok=True)
    subprocess.run(['tar','-xf',str(archive),'-C',str(sdk/'root')],check=True)
    receipts.append({'url':url,'sha256':expected,'bytes':len(data)})
old=Path(subprocess.check_output([str(a.lexer),'-print-resource-dir'],text=True).strip())
resource=sdk/'root/usr/lib/llvm-18/lib/clang/18'
shutil.copytree(old/'include',resource/'include',dirs_exist_ok=True)
bindir=sdk/'bin'
bindir.mkdir(exist_ok=True)
for name in ['clang','clang++']:
    flags=['-resource-dir='+str(resource)]
    if name=='clang++':
        flags += ['--driver-mode=g++','-nostdinc++',
                  '-isystem',str(sdk/'root/usr/include/c++/13'),
                  '-isystem',str(sdk/'root/usr/include/x86_64-linux-gnu/c++/13')]
    (bindir/name).write_text('#!/bin/sh\nexec '+shlex.join([str(a.lexer),*flags])+' "$@"\n')
    (bindir/name).chmod(0o755)
(packet/'receipts/compat-packages.json').write_text(json.dumps(receipts,indent=2)+'\n')
print('Compatibility packages hash-verified and extracted; compiler launchers prepared.')
