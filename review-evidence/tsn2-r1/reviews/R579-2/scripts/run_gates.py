#!/usr/bin/env python3
"""Run source gates concurrently; all child commands are awaited."""
import argparse, concurrent.futures, json, os, pathlib, subprocess, sys
p=argparse.ArgumentParser(); p.add_argument("repo",type=pathlib.Path);p.add_argument("packet",type=pathlib.Path);p.add_argument("--gtest",required=True);p.add_argument("--clang-bin",required=True);p.add_argument("--jobs",type=int,default=4);a=p.parse_args()
repo=a.repo.resolve();packet=a.packet.resolve();work=packet/"scratch/gates";work.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update(PATH=a.clang_bin+os.pathsep+env["PATH"],PKG_CONFIG_PATH=a.gtest+"/lib/pkgconfig",CMAKE_PREFIX_PATH=a.gtest,LD_LIBRARY_PATH=a.gtest+"/lib",PYTHONDONTWRITEBYTECODE="1")
for key in ("CPATH","CPLUS_INCLUDE_PATH","C_INCLUDE_PATH","LIBRARY_PATH"): env.pop(key,None)
commands={"linux":[sys.executable,"scripts/validate.py","--work",str(work/"linux"),"--jobs",str(a.jobs),"--graphs"],"rv32":[sys.executable,"scripts/baremetal.py","--work",str(work/"rv32"),"--jobs",str(a.jobs)]}
def run(item):
 name,cmd=item
 with (work/(name+".log")).open("w") as f: rc=subprocess.run(cmd,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 (work/(name+".rc")).write_text(str(rc)+"\n");print(name+": rc "+str(rc),flush=True);return {"suite":name,"rc":rc}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(run,commands.items()))
(work/"results.json").write_text(json.dumps(results,indent=2)+"\n")
sys.exit(any(x["rc"] for x in results))
