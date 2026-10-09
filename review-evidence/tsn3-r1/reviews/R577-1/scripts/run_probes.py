#!/usr/bin/env python3
"""Compile an independent oracle and disposable plants without source edits."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--cc',default='gcc')
p.add_argument('--jobs',type=int,default=2)
p.add_argument('--select',default='')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
src=a.source.resolve()
work=root/'scratch/probes'; work.mkdir(parents=True,exist_ok=True)
original=(src/'src/adp.c').read_text()
plants=json.loads((src/'tests/mutations.json').read_text())
selected=[m for m in plants if m['name'] in ['adp-unsupported-version-accepted','adp-short-frame-accepted','adp-wrong-control-length-accepted']]
selected += [
    dict(name='review-discard-not-counted',old='\t\ta->discarded++;\n\t\treturn;',new='\t\treturn;'),
    dict(name='review-refusal-stops-timer',old='\t\ta->discarded++;',new='\t\ta->discarded++; timer_stop(a);'),
    dict(name='review-control-high-bits-ignored',old='& 0x07FFu',new='& 0x00FFu'),
    dict(name='review-version-high-bits-ignored',old='& 0x70u',new='& 0x10u'),
    dict(name='review-valid-discovery-refused',old='!= ADP_MSG_ENTITY_DISCOVER',new='== ADP_MSG_ENTITY_DISCOVER'),
]
if a.select:
    selected += [dict(name='review-control-mask-removed',old=' & 0x07FFu',new='')]
    selected=[m for m in selected if a.select in m['name']]
    if not selected: raise RuntimeError('empty selection')
def run(m):
    name=m['name']; text=original
    if name!='baseline':
        if m['old'] not in text: raise RuntimeError('missing plant '+name)
        text=text.replace(m['old'],m['new'],1)
    c=work/(name+'.c'); c.write_text(text)
    exe=work/name
    argv=[a.cc,'-std=c11','-Wall','-Wextra','-Werror','-O1','-g','-fsanitize=address,undefined',
          '-fno-omit-frame-pointer','-I'+str(src/'include'),str(c),str(root/'scripts/adp_probe.c'),'-o',str(exe)]
    built=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (root/'receipts'/('probe-'+name+'-build.log')).write_text(built.stdout)
    if built.returncode: raise RuntimeError('compile failed '+name+'\n'+built.stdout)
    result=subprocess.run([str(exe)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
    (root/'receipts'/('probe-'+name+'.log')).write_text(result.stdout)
    record=dict(name=name,compile_rc=built.returncode,run_rc=result.returncode,
                expected_rc=0 if name=='baseline' else 1)
    print(json.dumps(record),flush=True)
    return record
with ThreadPoolExecutor(max_workers=a.jobs) as pool:
    results=list(pool.map(run,[dict(name='baseline')]+selected))
(root/'receipts'/('probes'+('-'+a.select if a.select else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(int(any(r['run_rc']!=r['expected_rc'] for r in results)))
