#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Foreground exact-head checks. Usage: run_checks.py CHECKOUT PACKET PHASE."""
import concurrent.futures, json, os, pathlib, shutil, subprocess, sys
root, packet=map(lambda p:pathlib.Path(p).resolve(),sys.argv[1:3]); phase=sys.argv[3]
scratch=packet/"scratch"; receipt=packet/"receipts/local"; receipt.mkdir(parents=True,exist_ok=True)
env={k:v for k,v in os.environ.items() if not k.startswith("GTEST_")}
(scratch/"temp").mkdir(exist_ok=True); env["TMPDIR"]=str(scratch/"temp")
def run(name,args):
 with (receipt/(name+".log")).open("w") as f:
  f.write("$ "+" ".join(map(str,args))+"\n");f.flush()
  r=subprocess.run(list(map(str,args)),cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=580)
 (receipt/(name+".rc")).write_text(str(r.returncode)+"\n");print(name,r.returncode,flush=True)
 return {"check":name,"rc":r.returncode}
def hosted():
 b=scratch/"gcc"
 steps=[("gcc-configure",["cmake","-S",root,"-B",b,"-DCMAKE_BUILD_TYPE=Debug","-DTSN_COVERAGE=ON"]),("gcc-build",["cmake","--build",b,"-j16"]),("gcc-test",["ctest","--test-dir",b,"--output-on-failure","-j16"]),("coverage",["python3","scripts/coverage.py",b])]
 out=[]
 for n,a in steps:
  out.append(run(n,a))
  if out[-1]["rc"]:break
 return out
def rv32():return [run("rv32",["python3","scripts/baremetal.py","--work",scratch/"rv32","--jobs","2"])]
def objects():
 for name,src in [("reference",packet/"receipts"),("head",root)]:
  d=scratch/"object-sources"/name;d.mkdir(parents=True,exist_ok=True)
  for suffix in ["c","h"]:
   f=src/("authority-acmp."+suffix) if name=="reference" else src/("src" if suffix=="c" else "include")/("acmp."+suffix)
   shutil.copyfile(f,d/("acmp."+suffix))
 return [run("object-compare",["sh",packet/"receipts/public/reviews/R622-1/scripts/object_compare.sh","riscv64-elf-gcc",root/"include",root/"examples/rv32/include",scratch/"object-sources/reference",scratch/"object-sources/head",scratch/"objects"])]
def metadata():
 checks=[("port-contracts",["python3","scripts/check_port_contracts.py","--selftest"]),("needles",["python3","scripts/needle_audit.py","--selftest"]),("comments",["python3","scripts/check_comments.py"])]
 return [run(n,a) for n,a in checks]
def mutation():return [run("mutation",["python3","scripts/mutation.py","--work",scratch/"mutations","--jobs","8"])]
def witness():return [run("witness",["sh",packet/"receipts/public/reviews/R622-1/scripts/witness.sh",root,scratch/"witness"])]
def probes():return [run("probes",["python3",packet/"receipts/public/reviews/R622-1/scripts/probe.py",root,scratch/"probes","4"])]
def traces():
 return [run("traceability",["python3","scripts/traceability.py","--selftest","--build",scratch/"registration","--jobs","16"]),run("test-inventory",["python3","scripts/test_inventory.py","--build",scratch/"registration","--jobs","16"])]
tasks={"one":[hosted,rv32,objects,metadata],"two":[mutation,witness],"three":[probes],"four":[traces,metadata]}[phase]
with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:results=sum(list(pool.map(lambda f:f(),tasks)),[])
(receipt/("phase-"+phase+".json")).write_text(json.dumps(results,indent=2)+"\n")
sys.exit(any(r["rc"] for r in results))
