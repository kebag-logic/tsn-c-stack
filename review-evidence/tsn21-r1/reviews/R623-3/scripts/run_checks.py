#!/usr/bin/env python3
"""Run independent source checks concurrently and join them in the foreground.
Usage: run_checks.py REPO PACKET; environment supplies pinned dependency paths.
"""
import concurrent.futures, json, os, pathlib, subprocess, sys, shutil, time
repo, packet = map(lambda x: pathlib.Path(x).resolve(), sys.argv[1:3])
scratch=packet/"scratch"; receipts=packet/"receipts/local"; receipts.mkdir(parents=True,exist_ok=True)
env=os.environ.copy(); env["TMPDIR"]=str(scratch/"tmp"); pathlib.Path(env["TMPDIR"]).mkdir(exist_ok=True)
env.pop("GTEST_FILTER",None); env["PYTHONDONTWRITEBYTECODE"]="1"
def run(name,argv):
    start=time.time()
    with (receipts/(name+".log")).open("w") as log:
        r=subprocess.run(list(map(str,argv)),cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=540)
    (receipts/(name+".rc")).write_text(str(r.returncode)+"\n")
    print(name,r.returncode,round(time.time()-start,2),flush=True)
    return {"name":name,"rc":r.returncode,"elapsed_seconds":round(time.time()-start,2)}
def metadata():
    out=[]
    for name,args in [("port-contracts",["scripts/check_port_contracts.py","--selftest"]),("traceability",["scripts/traceability.py","--selftest","--build",scratch/"registration","--jobs","2"]),("test-inventory",["scripts/test_inventory.py","--build",scratch/"registration","--jobs","2"]),("needles",["scripts/needle_audit.py","--selftest"]),("comments",["scripts/check_comments.py"] )]:
        out.append(run(name,[sys.executable,*args]))
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    fs=[pool.submit(run,"mutations",[sys.executable,"scripts/mutation.py","--work",scratch/"mutations","--jobs","8"]),pool.submit(run,"rv32",[sys.executable,"scripts/baremetal.py","--work",scratch/"rv32","--jobs","2"]),pool.submit(metadata),pool.submit(run,"objects",["sh",packet/"scripts/object_compare.sh",os.environ.get("REVIEW_RV32_CC","riscv64-elf-gcc"),repo/"include",repo/"examples/rv32/include",scratch/"head",scratch/"reference",scratch/"objects"])]
    results=[f.result() for f in fs]
(receipts/"campaigns.json").write_text(json.dumps(results,indent=2)+"\n")
for name in ("mutations","rv32"):
    d=receipts/name;d.mkdir(exist_ok=True)
    for src in (scratch/name).rglob("*"):
        if src.is_file() and src.suffix in (".json",".xml",".log"):
            if src.name=="compile_commands.json":continue
            rel=src.relative_to(scratch/name);dst=d/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
