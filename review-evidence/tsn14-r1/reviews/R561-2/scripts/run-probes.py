#!/usr/bin/env python3
"""Run published probes unchanged, in four concurrent disposable copies."""
import argparse,concurrent.futures,json,pathlib,subprocess,sys
ap=argparse.ArgumentParser();ap.add_argument('source',type=pathlib.Path);ap.add_argument('packet',type=pathlib.Path);a=ap.parse_args();p=a.packet.resolve();source=a.source.resolve();head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip();work=p/'scratch/probes';work.mkdir(exist_ok=True)
plants=[json.loads(f.read_text()) for f in sorted((p/'receipts/prior-probes').glob('*.json'))];base=dict(plants[0]);base.update(probe='p0-baseline',new='__BASELINE__');plants.insert(0,base)
def run(plant):
 name=plant['probe'];argv=[sys.executable,str(p/'scripts/claim_probe.py'),str(source),head,str(work),name,plant['path'],plant['old'],plant['new']]
 with (work/(name+'.log')).open('w') as log:r=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
 (work/(name+'.rc')).write_text(str(r.returncode)+'\n')
 if r.returncode:raise RuntimeError(name+' driver failed')
 result=json.loads((work/name/'result.json').read_text());assert result['build_rc']==0;return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,plants))
sys.path.insert(0,str(source/'scripts'));import traceability
tags={name:set(ids) for path in (source/'tests').glob('test_*.cpp') for name,ids,_ in traceability.inventory(path.read_text())}
for r in results:
 r['head']=head;r['tagged_failures']={tag:[test for test in r['failed'] if tag in tags.get(test,set())] for tag in ['MFDISC-01','MFCONN-03','MFRECOVERY-01']}
 if r['probe'].startswith('p0'):assert not r['failed']
 elif r['probe'].startswith('p7'):assert r['tagged_failures']['MFCONN-03']
 elif r['probe'].startswith('p8'):assert r['tagged_failures']['MFRECOVERY-01'] and r['tagged_failures']['MFCONN-03']
 elif r['probe'].startswith('p9'):assert r['tagged_failures']['MFDISC-01']
(p/'receipts/probe-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
