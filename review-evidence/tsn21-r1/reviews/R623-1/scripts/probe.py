#!/usr/bin/env python3
"""Run reviewer-owned tests and three surgical negative controls in scratch only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shlex
import subprocess

p=argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--gtest', type=Path, required=True)
a=p.parse_args()
root=a.root.resolve()
packet=Path(__file__).resolve().parents[1]
work=packet/'scratch/probes'
out=packet/'receipts/probes'
work.mkdir(parents=True,exist_ok=True)
out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ, PKG_CONFIG_PATH=str(a.gtest/'lib/pkgconfig'))
flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','gtest','gmock'],env=env,text=True))
original=(root/'tests/test_acmp.cpp').read_text()
cut=original.rfind('}')
(work/'tests.cpp').write_text(original[:cut]+(packet/'scripts/probes.cpp').read_text()+original[cut:])

def run(argv, log):
    r=subprocess.run(argv,cwd=root,env=env,text=True,capture_output=True,timeout=120)
    log.append(repr(argv)+'\n'+r.stdout+r.stderr)
    return r.returncode

log=[]
assert run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(root/'include'),'-I'+str(root/'tests'),*flags,'-c',str(work/'tests.cpp'),'-o',str(work/'tests.o')],log)==0
assert run(['g++','-std=c++20',*flags,'-c',str(root/'tests/main.cpp'),'-o',str(work/'main.o')],log)==0
(out/'build-tests.log').write_text(''.join(log))
source=(root/'src/acmp.c').read_text()
controls=[('exact-head',source,0),
          ('omit-pre-send-publication',source.replace('\tpublish(a);\n\tif (a->owed_count == 0u','\tif (a->owed_count == 0u'),1),
          ('publish-after-timer',source.replace('\tpublish(a);\n\trearm(a);','\trearm(a);\n\tpublish(a);'),1),
          ('publish-after-admission',source.replace('\tpublish(a);\n\trearm(a);\n\tadmit(a);','\trearm(a);\n\tadmit(a);\n\tpublish(a);'),1)]

def control(item):
    name,code,want=item
    d=work/name; d.mkdir(exist_ok=True)
    (d/'acmp.c').write_text(code)
    log=[]
    assert run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-DNDEBUG','-DCTRL_REENTRY_ASSERT','-I'+str(root/'include'),'-c',str(d/'acmp.c'),'-o',str(d/'acmp.o')],log)==0
    assert run(['g++',str(d/'acmp.o'),str(work/'tests.o'),str(work/'main.o'),*flags,'-o',str(d/'test')],log)==0
    rc=run([str(d/'test'),'--gtest_filter=AcmpCore.R623*','--gtest_output=xml:'+str(out/(name+'.xml'))],log)
    (out/(name+'.log')).write_text(''.join(log))
    assert rc==want,(name,rc,want)
    return {'name':name,'rc':rc,'expected_rc':want,'pass':True}

with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(control,controls))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
