#!/usr/bin/env python3
import concurrent.futures, json, os, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
ROOT=Path(sys.argv[1]).resolve(); W=P/"scratch"; R=P/"receipts/local"; R.mkdir(parents=True,exist_ok=True)
env=os.environ.copy(); env.update(TSN_CLANG=os.environ.get("TSN_CLANG","clang-18"),TMPDIR=str(W),PYTHONDONTWRITEBYTECODE="1")
for k in list(env):
 if k.startswith("GTEST_"): del env[k]
results=[]
def run(name,args):
 with (R/(name+".log")).open("w") as f:
  f.write("COMMAND "+" ".join(map(str,args))+"\n");f.flush()
  p=subprocess.run(list(map(str,args)),cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=540)
 (R/(name+".rc")).write_text(str(p.returncode)+"\n")
 row={"name":name,"rc":p.returncode}; print(json.dumps(row),flush=True);return row
def host():
 rows=[]
 for n,c in [("host-configure",["cmake","-S",ROOT,"-B",W/"host","-DTSN_COVERAGE=ON","-DCMAKE_BUILD_TYPE=Debug"]),("host-build",["make","-C",W/"host","-j16"]),("host-tests",["ctest","--test-dir",W/"host","--output-on-failure","-j16"]),("coverage",[sys.executable,"scripts/coverage.py",W/"host"])]:
  rows.append(run(n,c))
  if rows[-1]["rc"]:break
 return rows
def metadata():
 return [run(n,[sys.executable,*args]) for n,args in [("cache",["scripts/check_acmp_cache.py","--selftest"]),("cache-optimized",["-O","scripts/check_acmp_cache.py","--selftest"]),("needles",["scripts/needle_audit.py","--selftest"]),("port-contracts",["scripts/check_port_contracts.py","--selftest"]),("privacy",["scripts/check_privacy.py"]),("license",["scripts/check_license.py","--selftest"])]]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:
 for rows in e.map(lambda f:f(),[host,metadata]):results+=rows
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:
 tasks=[("mutations",[sys.executable,"scripts/mutation.py","--work",W/"mutations","--jobs","8"]),("rv32",[sys.executable,"scripts/baremetal.py","--work",W/"rv32","--jobs","4"])]
 for row in e.map(lambda t:run(*t),tasks):results.append(row)
(P/"receipts/local-results.json").write_text(json.dumps(results,indent=2)+"\n")
sys.exit(any(x["rc"] for x in results))
