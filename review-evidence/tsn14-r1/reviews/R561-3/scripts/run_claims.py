#!/usr/bin/env python3
"""Rerun the unchanged published probe with the original four probe inputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('checkout',type=Path)
p.add_argument('packet',type=Path)
p.add_argument('--dependency-prefix',type=Path,required=True)
a=p.parse_args()
root,packet=a.checkout.resolve(),a.packet.resolve()
env={k:v for k,v in os.environ.items() if not k.startswith('GTEST_')}
env.update(PKG_CONFIG_PATH=str(a.dependency_prefix/'lib/pkgconfig'),
           CMAKE_PREFIX_PATH=str(a.dependency_prefix),
           LD_LIBRARY_PATH=str(a.dependency_prefix/'lib'))
sys.path.insert(0,str(root/'scripts'))
import traceability
tags={name:ids for f in (root/'tests').glob('test_*.cpp')
      for name,ids,_ in traceability.inventory(f.read_text())}
work=packet/'scratch/claims'
work.mkdir(parents=True,exist_ok=True)
def run(f):
    d=json.loads(f.read_text())
    name=d['probe']
    command=[sys.executable,str(packet/'scripts/claim_probe.py'),str(root),
             '663f14de4a07bb1a777282fdfc83d30fd03843d4',str(work),name,
             d['path'],d['old'],d['new']]
    with (work/(name+'.log')).open('w') as log:
        rc=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=480).returncode
    (work/(name+'.rc')).write_text(str(rc)+'\n')
    assert rc==0,name
    result=json.loads((work/name/'result.json').read_text())
    assert result['build_rc']==0,name
    total=0
    for binary in ['adp_tests','acmp_tests','maap_tests','port_tests','adp_release','adp_debug','maap_debug']:
        report=json.loads((work/name/(binary+'.json')).read_text())
        assert report['disabled']==0 and report['errors']==0
        cases=[c for s in report['testsuites'] for c in s['testsuite']]
        assert report['tests']==len(cases)
        assert all(c['status']=='RUN' and c['result']=='COMPLETED' for c in cases)
        total+=len(cases)
    assert total==372,(name,total)
    result['instances']=total
    result['tagged_failures']={test:tags[test] for test in result['failed'] if test in tags}
    if name.startswith('p0'):
        assert not result['failed']
    else:
        required=['MFDISC-01'] if name.startswith('p9') else ['MFCONN-03','MFRECOVERY-01']
        assert all(any(req in ids for ids in result['tagged_failures'].values()) for req in required)
    print(name,'PASS',total,'instances',flush=True)
    return result
inputs=sorted((packet/'receipts/prior-probe-inputs').glob('*.json'))
assert len(inputs)==4
with ThreadPoolExecutor(max_workers=4) as pool:
    result=list(pool.map(run,inputs))
(packet/'receipts/claim-results.json').write_text(json.dumps(result,indent=2)+'\n')
print('Published script sha256:',hashlib.sha256((packet/'scripts/claim_probe.py').read_bytes()).hexdigest())
