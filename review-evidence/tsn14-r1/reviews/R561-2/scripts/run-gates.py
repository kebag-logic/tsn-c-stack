#!/usr/bin/env python3
"""Run both exact-source campaigns concurrently and retain logs and exit codes."""
import argparse, concurrent.futures, json, os, pathlib, subprocess, time
ap=argparse.ArgumentParser();ap.add_argument('source',type=pathlib.Path);ap.add_argument('packet',type=pathlib.Path);ap.add_argument('--jobs',type=int,default=16);a=ap.parse_args()
source=a.source.resolve();packet=a.packet.resolve();work=packet/'scratch'
env={k:v for k,v in os.environ.items() if not k.startswith('GTEST_')}
for k in ['CPATH','CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','LIBRARY_PATH']: env.pop(k,None)
def run(name,script,extra):
 start=time.monotonic();argv=['python3','scripts/'+script,'--work',str(work/name),'--jobs',str(a.jobs),*extra]
 with (work/(name+'.log')).open('w') as log:
  proc=subprocess.run(argv,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
 (work/(name+'.rc')).write_text(str(proc.returncode)+'\n')
 result={'campaign':name,'rc':proc.returncode,'elapsed_seconds':round(time.monotonic()-start,3)}
 print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(run,'validate','validate.py',['--graphs']),pool.submit(run,'baremetal','baremetal.py',[])]
 result=[f.result() for f in futures]
(packet/'receipts/campaigns.json').write_text(json.dumps(result,indent=2)+'\n')
raise SystemExit(any(r['rc'] for r in result))
