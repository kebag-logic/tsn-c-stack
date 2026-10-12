#!/usr/bin/env python3
"""Run individual cache omission controls in disposable RV32 source copies."""
import concurrent.futures,io,json,os,pathlib,subprocess,sys,tarfile
repo,packet=map(lambda s:pathlib.Path(s).resolve(),sys.argv[1:3]);scratch=packet/"scratch";out=packet/"receipts/rv32-cache-controls";out.mkdir(parents=True,exist_ok=True)
archive=subprocess.check_output(["git","-C",str(repo),"archive","HEAD"])
def run(field):
 root=scratch/("rv32-drop-"+field);root.mkdir(exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(archive)) as t:t.extractall(root,filter="data")
 path=root/"src/acmp.c";s=path.read_text();old=f"\ts->published_{field} = published_{field};";assert s.count(old)==1;path.write_text(s.replace(old,f"\t(void)published_{field};"))
 env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
 with (out/(field+".log")).open("w") as log:
  r=subprocess.run([sys.executable,"scripts/baremetal.py","--work",str(root/"build"),"--jobs","4"],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 (out/(field+".rc")).write_text(str(r.returncode)+"\n")
 row={"field":field,"rc":r.returncode};print(row,flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,["bound","started","stream"]))
(out/"summary.json").write_text(json.dumps(rows,indent=2)+"\n")
