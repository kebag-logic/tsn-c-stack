#!/usr/bin/env python3
"""Audit pinned token positions, six raw object pairs, and merge provenance."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--cc', default='riscv64-elf-gcc')
a = p.parse_args()
root = a.source.resolve()
packet = Path(__file__).resolve().parents[1]
scratch = packet/'scratch'
sys.path.insert(0, str(root/'scripts'))
from compiler_tokens import raw_tokens
from assertion_messages import inventory, assertion_inventory

def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

def signature(data):
    text=data.decode()
    return [(kind,word,line,start-data.rfind(b'\n',0,start))
            for kind,word,start,end,line in raw_tokens(text)
            if kind != 'comment' and not word.isspace()]

token_results=[]
for local, upstream in [('src/acmp.c','acmp.c'),('include/acmp.h','acmp.h')]:
    left=(root/local).read_bytes(); right=(scratch/'upstream'/upstream).read_bytes()
    l,r=signature(left),signature(right)
    row=dict(file=local,tokens=len(l),tokens_and_locations_equal=l==r,
             unchanged_from_previous=left==git('show','bc68ad8:'+local))
    token_results.append(row)
    if not all((row['tokens_and_locations_equal'], row['unchanged_from_previous'])):
        raise RuntimeError(row)
(packet/'receipts/token-position-identity.json').write_text(json.dumps(token_results,indent=2)+'\n')

old=scratch/'previous_assertion_messages.py'
old.write_bytes(git('show','bc68ad8:scripts/assertion_messages.py'))
spec=importlib.util.spec_from_file_location('previous_assertion_messages',old)
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
compat=[]
for path in sorted((root/'tests').glob('test_*.cpp')):
    text=path.read_text(); left=previous.inventory(text); right=inventory(text)
    compat.append(dict(file=str(path.relative_to(root)),tests=len(right),equal=left==right))
    if left!=right: raise RuntimeError('literal inventory changed: '+str(path))
(packet/'receipts/literal-inventory-compatibility.json').write_text(json.dumps(compat,indent=2)+'\n')

work=scratch/'objects'; build=work/'build'; build.mkdir(parents=True,exist_ok=True)
src=build/'src';src.mkdir(exist_ok=True)
intrinsic=subprocess.check_output([a.cc,'-print-file-name=include'],text=True).strip()
flags=['-Isrc','-I'+str(root/'examples/rv32/include'),'-march=rv32i','-mabi=ilp32',
       '-ffreestanding','-fno-builtin','-nostdinc','-isystem',intrinsic,
       '-std=c11','-Wall','-Wextra','-Werror']
sets={'debug-g0':['-DCTRL_REENTRY_ASSERT','-g0'],
      'debug':['-DCTRL_REENTRY_ASSERT','-g'],
      'release':['-DCTRL_REENTRY_ASSERT','-O3','-DNDEBUG'],
      'os':['-DCTRL_REENTRY_ASSERT','-Os'], 'o2-noassert':['-O2'], 'os-g3':['-Os','-g3']}
objects=[]
for name, extra in sets.items():
    pair=[]
    for side in ('port','upstream'):
        for filename in ('acmp.c','acmp.h','wire.h'):
            original=(root/('src' if filename.endswith('.c') else 'include')/filename
                      if side=='port' else scratch/'upstream'/filename)
            shutil.copyfile(original,src/filename)
        out=work/(name+'-'+side+'.o')
        subprocess.run([a.cc,*flags,*extra,'-c','src/acmp.c','-o',str(out)],cwd=build,check=True)
        pair.append(out.read_bytes())
    row=dict(configuration=name,flags=extra,raw_equal=pair[0]==pair[1],
             bytes=len(pair[0]),sha256=[hashlib.sha256(b).hexdigest() for b in pair])
    objects.append(row)
    if not row['raw_equal']: raise RuntimeError(row)
(packet/'receipts/raw-object-pairs.json').write_text(json.dumps(dict(common_flags=flags,objects=objects),indent=2)+'\n')

base, main, port, merge='1a9f651','98dc9e3','405dc683','3c9ca52f'
def tree(ref):
    return {line.split('\t')[1]:line.split('\t')[0] for line in git('ls-tree','-r',ref).decode().splitlines()}
b,m,s,i=map(tree,(base,main,port,merge))
rows=[]
mw=scratch/'merge-files';mw.mkdir(exist_ok=True)
for path in sorted(set(b)|set(m)|set(s)|set(i)):
    B,M,S,I=[d.get(path) for d in (b,m,s,i)]
    if I in (M,S):
        # A side that alone changed must not be silently discarded.
        expected=S if M==B else M if S==B else None
        if expected is not None and I!=expected: raise RuntimeError('lost parent change '+path)
        continue
    if M==B: automatic='port'
    elif S==B: automatic='main'
    else: automatic='both changed'
    row=dict(path=path,automatic=automatic)
    if all(x is not None for x in (B,M,S)):
        for label,ref in (('base',base),('main',main),('port',port)):
            (mw/label).write_bytes(git('show',ref+':'+path))
        r=subprocess.run(['git','merge-file','-p',str(mw/'main'),str(mw/'base'),str(mw/'port')],capture_output=True)
        row.update(textual_conflict=r.returncode>0,equals_automatic_union=r.returncode==0 and r.stdout==git('show',merge+':'+path))
    rows.append(row)
def plants(ref):return {m['name']:m for m in json.loads(git('show',ref+':tests/mutations.json'))}
B,M,S,I=map(plants,(base,main,port,merge))
for name in set(M)|set(S):
    expected=S[name] if M.get(name)==B.get(name) else M.get(name)
    if expected is None: expected=S[name]
    if I.get(name)!=expected: raise RuntimeError('lost mutation '+name)
if set(I)!=set(M)|set(S): raise RuntimeError('extra mutation')
summary=dict(head=git('rev-parse',merge).decode().strip(),
             parents=git('show','-s','--format=%P',merge).decode().strip().split(),
             different_from_both_parents=rows,mutation_union_preserved=True,
             mutation_counts={k:len(v) for k,v in zip(('base','main','port','integration'),(B,M,S,I))},
             production_parent={p:('main' if i[p]==m[p] else 'port' if i[p]==s[p] else 'other') for p in i if p.startswith(('src/','include/'))},
             gitlinks={r:[p for p,v in tree(r).items() if v.startswith('160000')] for r in (base,main,port,merge)})
(packet/'receipts/merge-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(token_identity=token_results,raw_pairs_equal=len(objects),merge=summary),indent=2))
