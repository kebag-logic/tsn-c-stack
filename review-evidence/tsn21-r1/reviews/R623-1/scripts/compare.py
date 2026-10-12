#!/usr/bin/env python3
"""Independent token, preserved-byte, test-body, and RV32 object comparisons."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
a = p.parse_args()
root = a.root.resolve()
packet = Path(__file__).resolve().parents[1]
scratch = packet / 'scratch'
out = packet / 'receipts/comparison'
out.mkdir(parents=True, exist_ok=True)
os.environ['LD_LIBRARY_PATH'] = str(scratch/'clang18/usr/lib/x86_64-linux-gnu')
os.environ['TSN_CLANG'] = str(scratch/'clang18/usr/bin/clang-18')
sys.path.insert(0, str(root/'scripts'))
from compiler_tokens import raw_tokens

def tokens(text, lang='c'):
    return [(k,v) for k,v,*_ in raw_tokens(text,lang) if k != 'comment' and not (k == 'unknown' and v.isspace())]

def sha(data):
    return hashlib.sha256(data).hexdigest()

up = scratch / 'upstream/sw/firmware/ctrl'
summary = {'base': '1a9f651cdf7846b8e10ac246a6ef6916960fbb92',
           'head': '2dcbe91ead981591d5bfb652f6616f6edb325875',
           'reference': '09c7231eca343607c97c0d66abebb2553688712c', 'tokens': [], 'objects': []}
for local, remote in [('src/acmp.c','acmp/acmp.c'), ('include/acmp.h','acmp/acmp.h')]:
    actual = (root/local).read_text()
    reference = (up/remote).read_text()
    base = subprocess.check_output(['git','show','1a9f651c:'+local], cwd=root).decode()
    original = (scratch/('pre-fint-'+Path(local).name)).read_text()
    ats, rts, bts, ots = map(tokens,[actual,reference,base,original])
    assert ats == rts, local+' reference token mismatch'
    assert bts == ots, local+' baseline token mismatch'
    opcodes = difflib.SequenceMatcher(None,base.splitlines(keepends=True),actual.splitlines(keepends=True),autojunk=False).get_opcodes()
    assert all(op in ('equal','insert') for op,*_ in opcodes), 'baseline bytes modified'
    preserved = ''.join(actual.splitlines(keepends=True)[j1:j2][k] for op,i1,i2,j1,j2 in opcodes if op=='equal' for k in range(j2-j1))
    assert preserved == base
    rows = {'file':local,'head_tokens':len(ats),'reference_tokens':len(rts),'equal':True,
            'baseline_tokens':len(bts),'pre_fint_tokens':len(ots),'baseline_equal':True,
            'preserved_baseline_bytes':True,'base_sha256':sha(base.encode()),
            'head_sha256':sha(actual.encode()),'reference_sha256':sha(reference.encode()),
            'token_sha256':sha(json.dumps(ats,separators=(',',':')).encode())}
    summary['tokens'].append(rows)
    (out/(Path(local).name+'.reference.diff')).write_text(''.join(difflib.unified_diff(reference.splitlines(True),actual.splitlines(True),fromfile='reference/'+remote,tofile='head/'+local)))

# All six F-INT A31 test bodies plus their ordering helpers are unchanged tokens.
actual=(root/'tests/test_acmp.cpp').read_text()
reference=(up/'test/test_acmp.cpp').read_text()
start='int send_at(unsigned n)'
summary['ported_test_tokens_equal'] = tokens(actual[actual.index(start):],'c++') == tokens(reference[reference.index(start):],'c++')
assert summary['ported_test_tokens_equal']

cc=shutil.which('riscv64-unknown-elf-gcc') or shutil.which('riscv64-elf-gcc')
assert cc
builtin=subprocess.check_output([cc,'-print-file-name=include'],text=True).strip()
summary['compiler']=subprocess.check_output([cc,'--version'],text=True).splitlines()[0]
work=scratch/'object-comparison'
for side in ['head','reference']:
    d=work/side
    d.mkdir(parents=True,exist_ok=True)
    for name in ['acmp.c','acmp.h','wire.h']:
        source=(root/('src' if name.endswith('.c') else 'include')/name) if side=='head' else up/('wire' if name=='wire.h' else 'acmp')/name
        shutil.copyfile(source,d/name)

def objects(case):
    opt, debug=case
    flags=['-std=c11','-march=rv32i','-mabi=ilp32','-ffreestanding','-fno-builtin','-nostdinc',
           '-isystem',builtin,'-I'+str(root/'examples/rv32/include'),'-Wall','-Wextra','-Werror',
           '-g0','-frandom-seed=0','-DCTRL_REENTRY_ASSERT',opt]
    if not debug: flags.append('-DNDEBUG')
    name=opt[1:]+('-debug' if debug else '-release')
    hashes=[]
    data=[]
    for side in ['head','reference']:
        argv=[cc,*flags,'-c','acmp.c','-o',name+'.o']
        r=subprocess.run(argv,cwd=work/side,capture_output=True,text=True)
        (out/(name+'-'+side+'.log')).write_text(repr(argv)+'\n'+r.stdout+r.stderr)
        assert r.returncode==0
        b=(work/side/(name+'.o')).read_bytes()
        data.append(b); hashes.append(sha(b))
    assert data[0]==data[1],name+' objects differ'
    return {'case':name,'bytes':len(data[0]),'head_sha256':hashes[0],'reference_sha256':hashes[1],'equal':True,'flags':flags}

with ThreadPoolExecutor(max_workers=4) as pool:
    summary['objects']=list(pool.map(objects,[('-O0',True),('-O0',False),('-Os',False),('-O3',False)]))
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
