#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build/execute the two hosted-escape probe copies, at most 16 build jobs."""
from concurrent.futures import ThreadPoolExecutor
import json,pathlib,subprocess,sys
p=pathlib.Path(sys.argv[1]).resolve();receipt=p/"receipts/local"
def check(name):
 tree=p/"scratch/probes"/name;log=receipt/("rv32-probe-"+name+".log")
 with log.open("w") as f:r=subprocess.run(["python3",str(tree/"scripts/baremetal.py"),"--work",str(tree/"build-rv32"),"--jobs","4"],cwd=tree,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 log.with_suffix(".rc").write_text(str(r.returncode)+"\n");result=[]
 for kind in ["debug","release"]:
  elf=tree/"build-rv32"/kind/"rv32_smoke.elf";assert elf.is_file()
  q=subprocess.run(["qemu-system-riscv32","-machine","virt","-nographic","-bios","none","-kernel",str(elf),"-no-reboot"],capture_output=True,text=True,timeout=30)
  result.append({"probe":name,"configuration":kind,"elf_exists":True,"execution_rc":q.returncode,"stdout":q.stdout,"stderr":q.stderr})
 return result
with ThreadPoolExecutor(max_workers=2) as pool:results=sum(list(pool.map(check,["guard-left-set","reset-drops-bound-cache-only"])),[])
(receipt/"rv32-probe-executions.json").write_text(json.dumps(results,indent=2)+"\n");print(results)
